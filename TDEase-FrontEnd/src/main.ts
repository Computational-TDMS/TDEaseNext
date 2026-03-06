import { createApp } from "vue";
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from "./App.vue";
import router from "./router";
import { createAPIClient } from './services/api/client'
import { useVisualizationStore } from './stores/visualization'
import { useWorkspaceStore } from './stores/workspace'
import { useThemeStore } from './stores/theme'
import '@/styles/catppuccin.css'
import '@/styles/catppuccin-element-plus.css'
import '@/styles/catppuccin-vueflow.css'

const app = createApp(App)

// 全局错误处理
app.config.errorHandler = (err, _instance, info) => {
  console.error('Vue Error:', err, 'Info:', info);
};

const pinia = createPinia()
app.use(pinia)
app.use(ElementPlus)
app.use(router)

// Initialize API client and set it to stores
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const apiClient = createAPIClient({
  baseURL: API_BASE_URL && !API_BASE_URL.includes('1421') ? API_BASE_URL : '',
  timeout: 30000,
})

// Set API client to stores after pinia is installed
const visualizationStore = useVisualizationStore()
const workspaceStore = useWorkspaceStore()
const themeStore = useThemeStore()

visualizationStore.setApiClient(apiClient)
workspaceStore.setApiClient(apiClient)

// Initialize theme
themeStore.initialize()

app.mount("#app");
