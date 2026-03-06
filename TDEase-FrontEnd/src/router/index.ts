import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    redirect: '/workflow'
  },
  {
    path: '/workflow',
    name: 'WorkflowEditor',
    component: () => import('../pages/workflow.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
