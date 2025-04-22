import { createRouter, createWebHistory } from 'vue-router'
import FileUpload from '../views/FileUpload.vue'
import TaskList from '../views/TaskList.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: FileUpload
    },
    {
      path: '/tasks',
      name: 'tasks',
      component: TaskList
    }
  ]
})

export default router