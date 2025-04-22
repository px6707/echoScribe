<template>
  <div class="upload-container">
    <h2>文件上传</h2>
    
    <!-- 拖拽上传区域 -->
    <el-upload
      v-model:file-list="fileList"
      class="upload-area"
      drag
      :http-request="customUpload"
      :on-exceed="handleExceed"
      :on-remove="handleRemove"
      :before-upload="beforeUpload"
      :limit="10"
      accept="audio/*,video/*"
      multiple
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        <template v-if="!uploading">
          拖拽文件到此处或 <em>点击上传</em>
        </template>
        <template v-else>
          正在上传...
        </template>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持音频或视频文件（单个文件最大 500MB，最多同时上传 10 个文件）
        </div>
      </template>
    </el-upload>

    <!-- 上传结果展示 -->
    <div v-if="uploadResults.length > 0" class="upload-results">
      <div class="results-header">
        <h3>上传结果</h3>
        <el-button type="danger" link @click="clearResults">
          清空结果
        </el-button>
      </div>
      <el-table :data="uploadResults" style="width: 100%">
        <el-table-column prop="filename" label="文件名" min-width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="error" label="错误信息" min-width="200">
          <template #default="{ row }">
            <span v-if="row.error" class="error-message">{{ row.error }}</span>
            <span v-else-if="row.status === 'success'" class="success-message">
              转录任务已创建
            </span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import type { UploadFile, UploadFiles } from 'element-plus'

const router = useRouter()
const API_BASE = 'http://localhost:8000'
const uploadUrl = `${API_BASE}/upload`

interface UploadResult {
  filename: string
  status: 'success' | 'error'
  error?: string
  task_id?: string
}

interface UploadResponse {
  success: Array<{
    filename: string
    task_id: string
    status: string
  }>
  failed: Array<{
    filename: string
    error: string
  }>
}

const fileList = ref<UploadFile[]>([])
const uploadResults = ref<UploadResult[]>([])
const uploading = ref(false)

const beforeUpload = (file: File) => {
  const isAudioVideo = file.type.startsWith('audio/') || file.type.startsWith('video/')
  const maxSize = 500 * 1024 * 1024 // 500MB
  
  if (!isAudioVideo) {
    ElMessage.error('请上传音频或视频文件！')
    return false
  }
  
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 500MB！')
    return false
  }

  uploading.value = true
  return true
}

const handleSuccess = (response: UploadResponse) => {
  if (!response.success && !response.failed) {
    ElMessage.error('服务器返回了意外的响应格式')
    return
  }

  // 处理所有成功的文件
  response.success?.forEach(result => {
    uploadResults.value.push({
      filename: result.filename,
      status: 'success',
      task_id: result.task_id
    })
  })

  // 处理所有失败的文件
  response.failed?.forEach(result => {
    uploadResults.value.push({
      filename: result.filename,
      status: 'error',
      error: result.error
    })
  })

  // 显示汇总信息
  const successCount = response.success?.length || 0
  const failedCount = response.failed?.length || 0
  
  if (successCount > 0) {
    ElMessage.success(`${successCount} 个文件上传成功，开始转录...`)
  }
  
  if (failedCount > 0) {
    ElMessage.error(`${failedCount} 个文件上传失败，请查看详情`)
  }

  uploading.value = false
}

const handleError = (error: any, uploadFile: UploadFile) => {
  const message = error.response?.data?.detail || '上传失败，请重试'
  uploadResults.value.push({
    filename: uploadFile.name,
    status: 'error',
    error: message
  })
  ElMessage.error(`上传失败：${message}`)
  uploading.value = false
}

const handleExceed = (files: File[]) => {
  ElMessage.warning(`最多只能同时上传 10 个文件，本次选择了 ${files.length} 个文件`)
}

const handleRemove = (file: UploadFile, fileList: UploadFiles) => {
  // 从结果列表中移除对应的记录
  const index = uploadResults.value.findIndex(
    result => result.filename === file.name
  )
  if (index !== -1) {
    uploadResults.value.splice(index, 1)
  }
}

const clearResults = () => {
  uploadResults.value = []
  fileList.value = []
}

defineExpose({
  clearResults
})

const customUpload = async (options: any) => {
  const { file } = options
  const formData = new FormData()
  formData.append('files', file)  // 注意这里用 'files' 而不是 'file'

  try {
    uploading.value = true
    const response = await fetch(uploadUrl, {
      method: 'POST',
      body: formData,
    }).catch(error => {
      // 处理网络错误
      throw new Error(`网络错误：${error.message || '无法连接到服务器'}`)
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '上传失败')
    }

    const data = await response.json()
    handleSuccess(data)
  } catch (error: any) {
    const errorMessage = error.message || '上传失败，请检查服务器是否正在运行'
    handleError({ response: { data: { detail: errorMessage } } }, { name: file.name } as UploadFile)
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.upload-container {
  margin-bottom: 20px;
}

.upload-area {
  width: 100%;
}

.results-container {
  margin-top: 20px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.error-message {
  color: var(--el-color-danger);
}

.success-message {
  color: var(--el-color-success);
}

.action-container {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}
</style>