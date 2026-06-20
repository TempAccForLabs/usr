import { createRouter, createWebHistory } from 'vue-router'
import AuthView from '../views/AuthView.vue'
import DashboardView from '../views/DashboardView.vue'

const routes = [
  { path: '/', name: 'auth', component: AuthView },
  { path: '/dashboard', name: 'dashboard', component: DashboardView },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
