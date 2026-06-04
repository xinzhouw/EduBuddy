import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './style.css'
import { hydrateDynamicFigures } from './utils/dynamicFigures'

const app = createApp(App)

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局指令：v-dyn-figures
// 在 v-html 内容挂载/更新后，自动把其中的 ```funcplot```/```smiles``` 占位元素
// 异步绘制成 ECharts 函数图、smiles-drawer 分子结构图。
const hydrate = (el: HTMLElement) => {
  // 等待 DOM patch 完成后再绘制，确保占位元素已存在
  requestAnimationFrame(() => hydrateDynamicFigures(el))
}
app.directive('dyn-figures', {
  mounted: hydrate,
  updated: hydrate,
})


app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: undefined })

app.mount('#app')
