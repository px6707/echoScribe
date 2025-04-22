from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .models import TranscriptionTask, SessionLocal
from .tasks import transcribe_audio_task
import uuid
import os
import aiofiles
import pandas as pd
from typing import List
import re
from .config import UPLOAD_DIR  # 导入配置
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path

app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传目录
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 配置限制
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_TYPES = [
    'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav',
    'audio/ogg', 'audio/x-m4a', 'audio/m4a', 'video/mp4'
]

def sanitize_filename(filename: str) -> str:
    """清理文件名，移除不安全字符"""
    # 获取文件扩展名
    name, ext = os.path.splitext(filename)
    # 只保留字母、数字、下划线、连字符和点
    name = re.sub(r'[^\w\-\.]', '_', name)
    return f"{name}{ext}".lower()  # 转换为小写以确保跨平台一致性

def get_file_path(filename: str) -> Path:
    """获取文件的完整路径，确保跨平台兼容性"""
    return UPLOAD_DIR / filename

async def save_file(file: UploadFile, file_path: Path) -> None:
    """保存上传的文件"""
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"保存文件失败: {str(e)}"
        )

def validate_file(file: UploadFile):
    """验证上传的文件"""
    # 检查文件大小
    file.file.seek(0, 2)  # 移动到文件末尾
    size = file.file.tell()  # 获取文件大小
    file.file.seek(0)  # 重置文件指针
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件太大。最大允许大小为 {MAX_FILE_SIZE/1024/1024:.0f}MB"
        )
    
    # 检查文件类型
    content_type = file.content_type
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"不支持的文件类型: {content_type}。支持的类型: {', '.join(ALLOWED_TYPES)}"
        )

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """处理多文件上传请求"""
    db = SessionLocal()
    results = []
    failed_files = []
    try:
        for file in files:
            file_path = None
            try:
                # 验证文件
                validate_file(file)

                # 生成唯一任务ID和安全的文件名
                task_id = str(uuid.uuid4())
                original_filename = file.filename
                safe_filename = sanitize_filename(original_filename)
                file_name = f"{task_id}_{safe_filename}"  # 只是文件名，不包含路径
                file_path = get_file_path(file_name)   # 完整的文件系统路径

                # 保存文件
                await save_file(file, file_path)
                
                # 创建任务记录
                task = TranscriptionTask(
                    id=task_id,
                    filename=safe_filename,
                    status="pending"
                )
                db.add(task)
                db.commit()

                # 使用 Dramatiq 发送任务
                transcribe_audio_task.send(task_id, file_name)

                results.append({
                    "filename": original_filename,
                    "task_id": task_id,
                    "status": "success"
                })

            except Exception as e:
                failed_files.append({
                    "filename": getattr(file, 'filename', 'unknown'),
                    "error": str(e)
                })
                # 回滚当前文件的数据库操作
                db.rollback()
                # 删除已上传的文件（如果存在）
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)

        # 返回处理结果
        return {
            "success": results,
            "failed": failed_files
        }

    finally:
        db.close()

@app.get("/tasks")
def list_tasks():
    db = SessionLocal()
    try:
        tasks = db.query(TranscriptionTask).order_by(TranscriptionTask.created_at.desc()).all()
        return [{
            "id": task.id,
            "filename": task.filename,
            "status": task.status,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
            "result": task.result if task.status == "completed" else None,
            "error": task.error if task.status == "failed" else None
        } for task in tasks]
    finally:
        db.close()

@app.delete("/tasks")
async def delete_tasks(task_ids: List[str] = Body(...)):
    db = SessionLocal()
    try:
        # 查找所有指定的任务
        tasks = db.query(TranscriptionTask).filter(
            TranscriptionTask.id.in_(task_ids)
        ).all()

        if not tasks:
            raise HTTPException(status_code=404, detail="No tasks found")

        deleted_count = 0
        failed_deletes = []

        for task in tasks:
            try:
                # 删除关联的音频文件（如果存在）
                file_path = get_file_path(f"{task.id}_{task.filename}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # 删除任务记录
                db.delete(task)
                deleted_count += 1
            except Exception as e:
                failed_deletes.append({
                    "task_id": task.id,
                    "error": str(e)
                })

        # 提交数据库更改
        db.commit()

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "failed_deletes": failed_deletes
        }
    finally:
        db.close()

@app.post("/export")
async def export_tasks(task_ids: List[str]):
    db = SessionLocal()
    try:
        tasks = db.query(TranscriptionTask).filter(
            TranscriptionTask.id.in_(task_ids)
        ).all()

        if not tasks:
            raise HTTPException(status_code=404, detail="No tasks found")
        
        # 创建DataFrame
        data = [{
            "文件名": task.filename,
            "创建时间": task.created_at,
            "完成时间": task.completed_at,
            "状态": task.status,
            "转录结果": task.result
        } for task in tasks]
        
        df = pd.DataFrame(data)
        
        # 导出到Excel
        export_path = get_file_path(f"export_{uuid.uuid4()}.xlsx")
        df.to_excel(export_path, index=False)
        
        return FileResponse(
            export_path,
            filename="transcription_results.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            background=None  # 确保文件在发送后被删除
        )
    finally:
        db.close()
        # 清理导出文件
        if 'export_path' in locals() and os.path.exists(export_path):
            try:
                os.remove(export_path)
            except Exception:
                pass