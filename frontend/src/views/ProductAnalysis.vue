<template>
    <div class="product-analysis">
        <!-- 搜索区域 -->
        <el-card class="search-area">
            <div class="search-form">
                <!-- 左侧：搜索和选择区域 -->
                <div class="search-controls">
                    <el-autocomplete
                        v-model="searchBarcode"
                        :fetch-suggestions="querySearch"
                        placeholder="请输入商品条形码或名称"
                        :trigger-on-focus="false"
                        @select="handleSelect"
                        @keyup.enter="handleSearch"
                        class="barcode-input"
                    >
                        <template #default="{ item }">
                            <div class="search-item">
                                <div class="name">{{ item.name }}</div>
                                <div class="info">
                                    <span>条码: {{ item.barcode }}</span>
                                    <span>库存: {{ item.stock }}{{ item.unit }}</span>
                                </div>
                            </div>
                        </template>
                        <template #append>
                            <el-button @click="handleSearch">
                                <el-icon>
                                    <Search />
                                </el-icon>
                            </el-button>
                        </template>
                    </el-autocomplete>

                    <el-select v-model="timeRange" class="time-range">
                        <el-option label="最近1个月" value="1" />
                        <el-option label="最近3个月" value="3" />
                        <el-option label="最近半年" value="6" />
                        <el-option label="最近1年" value="12" />
                    </el-select>
                </div>

                <!-- 右侧：商品信息 -->
                <div v-if="currentProduct" class="product-info">
                    <el-descriptions :column="3" size="small" border>
                        <el-descriptions-item label="商品名称">{{ currentProduct.name }}</el-descriptions-item>
                        <el-descriptions-item label="单位">{{ currentProduct.unit }}</el-descriptions-item>
                        <el-descriptions-item label="当前库存">{{ currentProduct.stock }}</el-descriptions-item>
                    </el-descriptions>
                </div>
            </div>
        </el-card>

        <!-- 图表区域 -->
        <div v-if="currentProduct" class="charts-container">
            <!-- 价格趋势图 -->
            <el-card class="chart-card">
                <template #header>
                    <div class="card-header">
                        <span>价格趋势</span>
                    </div>
                </template>
                <div class="chart-wrapper">
                    <v-chart class="chart" :option="priceChartOption" autoresize />
                </div>
            </el-card>

            <!-- 销售和利润图 -->
            <el-card class="chart-card">
                <template #header>
                    <div class="card-header">
                        <span>销售与利润</span>
                    </div>
                </template>
                <div class="chart-wrapper">
                    <v-chart class="chart" :option="profitChartOption" autoresize />
                </div>
            </el-card>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import { Search } from '@element-plus/icons-vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { LineChart, BarChart } from 'echarts/charts';
import {
    TitleComponent,
    TooltipComponent,
    LegendComponent,
    GridComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { getInventoryByBarcode, getProductAnalysis, searchInventory } from '../api/inventory';
import type { Inventory, ProductAnalysis } from '../api/inventory';

// 注册 ECharts 组件
use([
    CanvasRenderer,
    LineChart,
    BarChart,
    TitleComponent,
    TooltipComponent,
    LegendComponent,
    GridComponent
]);

const searchBarcode = ref('');
const timeRange = ref('1');
const currentProduct = ref<Inventory | null>(null);

// 初始化数据结构
const initChartData = () => ({
    dates: [],
    costs: [],
    prices: []
});

const initProfitData = () => ({
    dates: [],
    sales: [],
    profits: []
});

// 使用函数初始化数据
const priceData = ref(initChartData());
const profitData = ref(initProfitData());

// 价格趋势图配置
const priceChartOption = computed(() => ({
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'cross'
        },
        formatter: (params: any) => {
            const date = params[0].name;
            const costValue = params[0].value;
            const priceValue = params[1].value;
            return `${date}<br/>
                   成本: ¥${costValue.toLocaleString()}<br/>
                   售价: ¥${priceValue.toLocaleString()}`;
        }
    },
    legend: {
        data: ['成本', '售价'],
        top: 10
    },
    grid: {
        top: 60,
        left: 60,
        right: 30,
        bottom: 40,
        containLabel: true
    },
    dataZoom: [
        {
            type: 'inside',
            start: 0,
            end: 100
        },
        {
            type: 'slider',
            show: true,
            bottom: 10
        }
    ],
    xAxis: {
        type: 'category',
        data: priceData.value.dates,
        axisLabel: {
            interval: Math.floor(priceData.value.dates.length / 6),  // 大约显示6个标签
            rotate: 45,
            fontSize: 11,
            margin: 8
        }
    },
    yAxis: {
        type: 'value',
        axisLabel: {
            formatter: '¥{value}'
        }
    },
    series: [
        {
            name: '成本',
            type: 'line',
            data: priceData.value.costs,
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: { width: 2 },
            itemStyle: {
                color: '#409EFF'  // 使用 Element Plus 的主题蓝色
            },
            label: {
                show: true,
                position: 'top',
                formatter: (params: any) => {
                    return `¥${params.value}`;
                }
            }
        },
        {
            name: '售价',
            type: 'line',
            data: priceData.value.prices,
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: { width: 2 },
            itemStyle: {
                color: '#67C23A'  // 使用 Element Plus 的成功绿色
            },
            label: {
                show: true,
                position: 'top',
                formatter: (params: any) => {
                    return `¥${params.value}`;
                }
            }
        }
    ]
}));

// 销售和利润图配置
const profitChartOption = computed(() => ({
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'shadow'
        },
        formatter: (params: any) => {
            const date = params[0].name;
            const salesValue = params[0].value;
            const profitValue = params[1].value;
            return `${date}<br/>
                   销售额: ¥${salesValue.toLocaleString()}<br/>
                   利润: ¥${profitValue.toLocaleString()}`;
        }
    },
    legend: {
        data: ['销售额', '利润'],
        top: 10
    },
    grid: {
        top: 60,
        left: 80,    // 增加左边距，为大数值留出空间
        right: 30,
        bottom: 60,  // 增加底部边距，为x轴标签留出空间
        containLabel: true
    },
    dataZoom: [
        {
            type: 'inside',
            start: 0,
            end: 100,
            zoomLock: true,  // 锁定缩放，只允许平移
            moveOnMouseWheel: true  // 允许鼠标滚轮平移
        },
        {
            type: 'slider',
            show: true,
            bottom: 10,
            height: 20
        }
    ],
    xAxis: {
        type: 'category',
        data: profitData.value.dates,
        axisLabel: {
            interval: Math.floor(profitData.value.dates.length / 6),  // 大约显示6个标签
            rotate: 45,
            fontSize: 11,
            margin: 8
        }
    },
    yAxis: {
        type: 'value',
        name: '金额 (元)',
        nameLocation: 'middle',
        nameGap: 50,
        axisLabel: {
            formatter: (value: number) => {
                if (value >= 10000) {
                    return `${(value / 10000).toFixed(1)}万`;
                }
                return value.toFixed(0);
            }
        },
        splitLine: {
            show: true,
            lineStyle: {
                type: 'dashed'
            }
        }
    },
    series: [
        {
            name: '销售额',
            type: 'bar',
            data: profitData.value.sales.map(v => parseFloat(v.toString())),
            barMaxWidth: 30,
            itemStyle: {
                opacity: 0.8,
                color: '#409EFF'  // 使用 Element Plus 的主题蓝色
            },
            label: {
                show: true,
                position: 'top',
                formatter: (params: any) => {
                    const value = params.value;
                    return value >= 10000 ?
                        `${(value / 10000).toFixed(1)}万` :
                        value.toFixed(0);
                }
            }
        },
        {
            name: '利润',
            type: 'bar',
            data: profitData.value.profits.map(v => parseFloat(v.toString())),
            barMaxWidth: 30,
            itemStyle: {
                opacity: 0.8,
                color: '#67C23A'  // 使用 Element Plus 的成功绿色
            },
            label: {
                show: true,
                position: 'top',
                formatter: (params: any) => {
                    const value = params.value;
                    return value >= 10000 ?
                        `${(value / 10000).toFixed(1)}万` :
                        value.toFixed(0);
                }
            }
        }
    ]
}));

// 修改日期格式，使其更简洁
const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}.${date.getDate()}`;  // 使用点号分隔月和日
};

// 修改搜索函数，在搜索新商品前重置数据
const handleSearch = async () => {
    if (!searchBarcode.value) {
        ElMessage.warning('请输入条形码');
        return;
    }

    try {
        // 重置数据
        priceData.value = initChartData();
        profitData.value = initProfitData();

        // 清除当前商品
        currentProduct.value = null;

        // 获取新商品数据
        currentProduct.value = await getInventoryByBarcode(searchBarcode.value);
        if (currentProduct.value) {
            await loadAnalysisData();
        }
    } catch (error) {
        console.error('查询商品失败:', error);
        ElMessage.error('商品不存在');
        currentProduct.value = null;
    }
};

// 修改数据加载函数
const loadAnalysisData = async () => {
    if (!currentProduct.value) return;

    try {
        const months = parseInt(timeRange.value);
        const data = await getProductAnalysis(currentProduct.value.barcode, months);

        // 反转数据，使最新的数据显示在右边
        const priceTrends = [...data.price_trends].reverse();
        const salesAnalysis = [...data.sales_analysis].reverse();

        // 确保所有数据都被正确处理
        const processedSales = salesAnalysis.map(s => s.sales);
        const processedProfits = salesAnalysis.map(s => s.profit);

        // 更新数据
        priceData.value = {
            dates: priceTrends.map(p => formatDate(p.date)),
            costs: priceTrends.map(p => p.cost),
            prices: priceTrends.map(p => p.price)
        };

        profitData.value = {
            dates: salesAnalysis.map(s => formatDate(s.date)),
            sales: processedSales,
            profits: processedProfits
        };

        // 强制更新图表
        nextTick(() => {
            const charts = document.querySelectorAll('.chart');
            charts.forEach((chart: any) => {
                if (chart.__vue__) {
                    chart.__vue__.resize();
                }
            });
        });
    } catch (error) {
        console.error('加载分析数据失败:', error);
        ElMessage.error('加载分析数据失败');
        priceData.value = initChartData();
        profitData.value = initProfitData();
    }
};

// 监听时间范围变化
watch(timeRange, () => {
    if (currentProduct.value) {
        loadAnalysisData();
    }
});

// 搜索建议
const querySearch = async (queryString: string, cb: (arg: any[]) => void) => {
    if (!queryString) {
        cb([]);
        return;
    }

    try {
        const response = await searchInventory(queryString);
        cb(response);
    } catch (error) {
        console.error('搜索商品失败:', error);
        cb([]);
    }
};

// 选择商品
const handleSelect = (item: Inventory) => {
    searchBarcode.value = item.barcode;
    handleSearch();  // 自动触发搜索
};
</script>

<style scoped>
.product-analysis {
    padding: 10px 20px;
    height: 100%;
    width: 100%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.search-area {
    flex-shrink: 0;
    width: 100%;
    height: 80px !important;
    /* 设置固定高度 */
}

.search-form {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    max-width: 1600px;
    margin: 0 auto;
    height: 100%;
    /* 让表单占满卡片高度 */
}

.search-controls {
    display: flex;
    gap: 15px;
    align-items: center;
}

.barcode-input {
    width: 300px;
}

.time-range {
    width: 150px;
}

.product-info {
    flex: 1;
    min-width: 500px;
}

.charts-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 15px;
    overflow: hidden;
    min-height: 900px;
    width: 100%;
    max-width: 1800px;
    margin: 0 auto;
}

.chart-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 420px;
}

.chart-wrapper {
    flex: 1;
    min-height: 380px;
    position: relative;
}

.chart {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* 禁用 Element Plus 的过渡动画 */
:deep(.el-card) {
    transition: none !important;
    width: 100%;
    height: 100%;
    box-shadow: 0 1px 4px rgba(0, 21, 41, .08);
    /* 更细腻的阴影 */
}

:deep(.el-card__header) {
    padding: 8px;
    /* 减小卡片头部内边距 */
}

:deep(.el-card__body) {
    height: calc(100% - 40px);
    /* 减去header高度 */
    padding: 5px 10px;
    /* 减小卡片内容区内边距 */
}

:deep(.el-descriptions) {
    margin: 0;
    height: 100%;
}

:deep(.el-descriptions__cell) {
    padding: 2px 8px !important;
    /* 进一步减小单元格内边距 */
}

:deep(.el-descriptions__label) {
    width: 70px;
    /* 固定标签宽度 */
}

:deep(.el-descriptions__body) {
    background-color: transparent;
}

/* 调整搜索区域卡片的样式 */
.search-area:deep(.el-card__body) {
    padding: 8px 15px;
    height: 100%;
    /* 让卡片内容区域占满高度 */
}

.search-item {
    padding: 4px 0;
}

.search-item .name {
    font-weight: bold;
}

.search-item .info {
    font-size: 12px;
    color: #666;
    display: flex;
    gap: 10px;
}

:deep(.el-autocomplete) {
    width: 100%;
}
</style>