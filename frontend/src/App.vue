<template>
  <el-config-provider>
    <div class="app-container">
      <!-- 侧边栏 -->
      <nav class="sidebar">
        <ul class="nav-links">
          <li>
            <RouterLink to="/" class="nav-link" active-class="active">
              <el-icon><upload-filled /></el-icon>
              文件上传
            </RouterLink>
          </li>
          <li>
            <RouterLink to="/tasks" class="nav-link" active-class="active">
              <el-icon><document /></el-icon>
              任务列表
            </RouterLink>
          </li>
        </ul>
      </nav>

      <!-- 主内容区 -->
      <main class="main-content">
        <RouterView />
      </main>
    </div>
  </el-config-provider>
</template>

<script setup>
import { UploadFilled, Document } from '@element-plus/icons-vue'
</script>

<style>
.app-container {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 200px;
  background-color: #545c64;
  padding: 20px 0;
}

.nav-links {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-link {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  color: #fff;
  text-decoration: none;
  transition: background-color 0.3s;
}

.nav-link:hover, .nav-link.active {
  background-color: #434a50;
}

.nav-link .el-icon {
  margin-right: 10px;
}

.main-content {
  flex: 1;
  padding: 20px;
  background-color: #f5f6fa;
}
</style>