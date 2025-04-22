
<template>
  <div class="task-list-container">
    <div class="header">
      <h2>转录任务列表</h2>
      <div class="actions">
        <el-button type="primary" @click="$router.push('/')">
          <el-icon><plus /></el-icon>新建任务
        </el-button>
        <el-button 
          type="success" 
          :disabled="selectedTasks.length === 0"
          @click="exportSelected"
        >
          <el-icon><download /></el-icon>导出所选
        </el-button>
        <el-button 
          type="danger" 
          :disabled="selectedTasks.length === 0"
          @click="deleteSelected"
        >
          <el-icon><delete /></el-icon>删除所选
        </el-button>
      </div>
    </div>

    <div class="selection-info" v-if="selectedTasks.length > 0">
      已选择 {{ selectedTasks.length }} 个任务
    </div>

    <el-table 
      :data="tasks" 
      style="width: 100%"
      @selection-change="handleSelectionChange"
      v-loading="loading"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="filename" label="文件名" min-width="180" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button 
            v-if="row.status === 'completed'"
            type="primary" 
            size="small" 
            @click="viewResult(row)"
          >
            查看结果
          </el-button>
          <el-button 
            v-if="row.status === 'failed'"
            type="info" 
            size="small" 
            @click="showError(row)"
          >
            查看错误
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="70%"
      destroy-on-close
    >
      <div v-if="currentTask">
        <div class="result-header" v-if="currentTask.status === 'completed'">
          <el-button type="primary" size="small" @click="copyText">
            <el-icon><document-copy /></el-icon>
            复制文本
          </el-button>
        </div>
        <div class="dialog-content">
          <p v-if="currentTask.status === 'completed'" style="white-space: pre-wrap;">
            {{ currentTask.result }}
          </p>
          <p v-else-if="currentTask.status === 'failed'" class="error-message">
            {{ currentTask.error }}
          </p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, DocumentCopy, Download } from '@element-plus/icons-vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

interface Task {
  id: string
  filename: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  result?: string
  error?: string
  created_at: string
  completed_at?: string
}

const tasks = ref<Task[]>([])
const selectedTasks = ref<Task[]>([])
const dialogVisible = ref(false)
const dialogTitle = ref('')
const currentTask = ref<Task | null>(null)
const loading = ref(false)
let pollingInterval: number | null = null

// 获取任务列表
const fetchTasks = async () => {
  try {
    loading.value = true
    const response = await axios.get(`${API_BASE}/tasks`)
    tasks.value = response.data
  } catch (error) {
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

// 停止轮询
const stopPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
}

onMounted(() => {
  fetchTasks()
})

onUnmounted(() => {
  stopPolling()
})

const handleSelectionChange = (selection: Task[]) => {
  selectedTasks.value = selection
}

const deleteSelected = async () => {
  if (selectedTasks.value.length === 0) return
  
  try {
    await ElMessageBox.confirm('确定要删除选中的任务吗？', '提示', {
      type: 'warning'
    })
    
    const taskIds = selectedTasks.value.map(task => task.id)
    await axios.delete(`${API_BASE}/tasks`, { data: taskIds })
    ElMessage.success('删除成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败，请重试')
    }
  }
}

const exportSelected = async () => {
  if (selectedTasks.value.length === 0) return

  try {
    const taskIds = selectedTasks.value.map(task => task.id)
    const response = await axios.post(
      `${API_BASE}/export`,
      taskIds,
      { responseType: 'blob' }
    )
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `transcription_results_${new Date().toISOString().split('T')[0]}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败，请重试')
  }
}

const viewResult = (task: Task) => {
  currentTask.value = task
  dialogTitle.value = '转录结果'
  dialogVisible.value = true
}

const showError = (task: Task) => {
  currentTask.value = task
  dialogTitle.value = '错误信息'
  dialogVisible.value = true
}

const copyText = async () => {
  if (!currentTask.value?.result) return
  
  try {
    await navigator.clipboard.writeText(currentTask.value.result)
    ElMessage.success('文本已复制到剪贴板')
  } catch (err) {
    ElMessage.error('复制失败，请重试')
  }
}

const getStatusType = (status: string): "success" | "warning" | "info" | "danger" => {
  const types: Record<string, "success" | "warning" | "info" | "danger"> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.task-list-container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
}

.actions {
  display: flex;
  gap: 10px;
}

.selection-info {
  margin-bottom: 15px;
  color: #606266;
  font-size: 14px;
}

.result-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 15px;
}

.dialog-content {
  max-height: 60vh;
  overflow-y: auto;
}

.dialog-content p {
  margin: 0;
  line-height: 1.6;
}

.error-message {
  color: #f56c6c;
}

:deep(.el-table .cell) {
  word-break: break-word;
}
</style>