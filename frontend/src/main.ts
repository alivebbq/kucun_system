import { createApp } from 'vue'
import './style.css'
import './styles/common.scss'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
// 导入 echarts 相关
import ECharts from 'vue-echarts'
import { use } from 'echarts/core'
import {
    CanvasRenderer
} from 'echarts/renderers'
import {
    LineChart,
    BarChart
} from 'echarts/charts'
import {
    TitleComponent,
    TooltipComponent,
    LegendComponent,
    GridComponent
} from 'echarts/components'
import {
    Odometer,
    List,
    Plus,
    Minus,
    Tickets,
    DataLine,
    TrendCharts
} from '@element-plus/icons-vue'
import { createPinia } from 'pinia'

// 手动注册 ECharts 需要的组件
use([
    CanvasRenderer,
    LineChart,
    BarChart,
    TitleComponent,
    TooltipComponent,
    LegendComponent,
    GridComponent
])

const app = createApp(App)
app.use(createPinia())

// 注册 ECharts 组件
app.component('v-chart', ECharts)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}

// 手动注册需要的图标
app.component('Odometer', Odometer)
app.component('List', List)
app.component('Plus', Plus)
app.component('Minus', Minus)
app.component('Tickets', Tickets)
app.component('DataLine', DataLine)
app.component('TrendCharts', TrendCharts)

app.use(ElementPlus, {
    locale: zhCn,
})
app.use(router)

app.mount('#app')
