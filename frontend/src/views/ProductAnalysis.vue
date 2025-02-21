<template>
    <div class="page-container">
        <!-- 顶部工具栏 -->
        <div class="toolbar">
            <div class="toolbar-left">
                <el-form :inline="true" class="search-form">
                    <el-form-item label="商品">
                        <el-autocomplete
                            v-model="searchQuery"
                            :fetch-suggestions="querySearch"
                            placeholder="输入商品名称或条形码"
                            :trigger-on-focus="false"
                            clearable
                            class="search-input"
                            @select="handleSelect"
                        >
                            <template #prefix>
                                <el-icon><Search /></el-icon>
                            </template>
                            <template #default="{ item }">
                                <div class="search-item">
                                    <div class="name">{{ item.name }}</div>
                                    <div class="info">
                                        <span>条形码: {{ item.barcode }}</span>
                                        <span>库存: {{ item.stock }}</span>
                                    </div>
                                </div>
                            </template>
                        </el-autocomplete>
                    </el-form-item>
                    <el-form-item>
                        <el-button type="primary" @click="showProductList">
                            <el-icon><List /></el-icon>
                            选择商品
                        </el-button>
                    </el-form-item>
                    <!-- 修改时间范围的选择方式 -->
                    <el-form-item label="时间范围">
                        <el-date-picker
                            v-model="dateRange"
                            type="daterange"
                            range-separator="至"
                            start-placeholder="开始日期"
                            end-placeholder="结束日期"
                            :shortcuts="dateShortcuts"
                            value-format="YYYY-MM-DD"
                            @change="handleDateChange"
                        />
                    </el-form-item>
                </el-form>
            </div>
        </div>

        <!-- 商品列表对话框 -->
        <el-dialog
            v-model="productListVisible"
            title="选择商品"
            width="80%"
            class="custom-dialog"
        >
            <el-table
                :data="productList"
                style="width: 100%"
                height="500px"
                :header-cell-class-name="'table-header'"
                @row-click="handleProductSelect"
            >
                <el-table-column prop="barcode" label="条形码" width="150" />
                <el-table-column prop="name" label="商品名称" />
                <el-table-column prop="unit" label="单位" width="100" />
                <el-table-column prop="stock" label="库存" width="100" align="right" />
                <el-table-column label="状态" width="100">
                    <template #default="{ row }">
                        <el-tag :type="row.is_active ? 'success' : 'danger'">
                            {{ row.is_active ? '启用' : '禁用' }}
                        </el-tag>
                    </template>
                </el-table-column>
            </el-table>
            <!-- 添加分页组件 -->
            <div class="pagination-container">
                <el-pagination
                    v-model:current-page="currentPage"
                    v-model:page-size="pageSize"
                    :page-sizes="[10, 20, 50, 100]"
                    :total="total"
                    layout="total, sizes, prev, pager, next"
                    @size-change="handleSizeChange"
                    @current-change="handleCurrentChange"
                />
            </div>
        </el-dialog>

        <!-- 保留原有的分析图表内容 -->
        <div v-if="currentProduct" class="analysis-content">
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
import { ref, computed, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import { Search, List } from '@element-plus/icons-vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { LineChart, BarChart } from 'echarts/charts';
import {
    TitleComponent,
    TooltipComponent,
    LegendComponent,
    GridComponent,
    DataZoomComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { getInventoryByBarcode, getProductAnalysis, searchInventory, getInventoryList, type Inventory } from '../api/inventory';

// 注册 ECharts 组件
use([
    CanvasRenderer,
    LineChart,
    BarChart,
    TitleComponent,
    TooltipComponent,
    LegendComponent,
    GridComponent,
    DataZoomComponent
]);

const searchQuery = ref('');
const productListVisible = ref(false);
const productList = ref<Inventory[]>([]);
const searchBarcode = ref('');
const dateRange = ref<[Date, Date] | null>(null);
const currentProduct = ref<Inventory | null>(null);

// 添加日期快捷选项
const dateShortcuts = [
    {
        text: '最近一月',
        value: () => {
            const end = new Date();
            const start = new Date();
            start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
            return [start, end];
        },
    },
    {
        text: '最近一季度',
        value: () => {
            const end = new Date();
            const start = new Date();
            start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
            return [start, end];
        },
    },
    {
        text: '最近半年',
        value: () => {
            const end = new Date();
            const start = new Date();
            start.setTime(start.getTime() - 3600 * 1000 * 24 * 180);
            return [start, end];
        },
    },
    {
        text: '最近一年',
        value: () => {
            const end = new Date();
            const start = new Date();
            start.setTime(start.getTime() - 3600 * 1000 * 24 * 365);
            return [start, end];
        },
    }
];

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
        const response = await getInventoryByBarcode(searchBarcode.value);
        currentProduct.value = response; 
        
        if (currentProduct.value) {
            await loadAnalysisData();
        }
    } catch (error) {
        ElMessage.error('商品不存在');
        currentProduct.value = null;
    }
};

// 修改数据加载函数
const loadAnalysisData = async () => {
    if (!currentProduct.value || !dateRange.value) return;

    try {
        const [start, end] = dateRange.value;
        const response = await getProductAnalysis(
            currentProduct.value.barcode,
            {
                start_date: start,
                end_date: end
            }
        );

        // 反转数据，使最新的数据显示在右边
        const priceTrends = [...response.price_trends].reverse();
        const salesAnalysis = [...response.sales_analysis].reverse();

        // 找到第一次入库和出库的日期
        let firstInDate = null;
        let firstOutDate = null;
        
        for (const trend of priceTrends) {
            if (!firstInDate && trend.cost > 0) {
                firstInDate = new Date(trend.date);
            }
            if (!firstOutDate && trend.price > 0) {
                firstOutDate = new Date(trend.date);
            }
            if (firstInDate && firstOutDate) break;
        }

        // 处理价格数据
        let lastCost = 0;
        let lastPrice = 0;
        
        const processedPriceTrends = priceTrends.map(trend => {
            const currentDate = new Date(trend.date);
            
            // 处理成本价
            if (firstInDate && currentDate >= firstInDate) {
                if (trend.cost > 0) {
                    lastCost = trend.cost;
                }
            } else {
                lastCost = 0;
            }

            // 处理售价
            if (firstOutDate && currentDate >= firstOutDate) {
                if (trend.price > 0) {
                    lastPrice = trend.price;
                }
            } else {
                lastPrice = 0;
            }
            
            return {
                ...trend,
                cost: lastCost,
                price: lastPrice
            };
        });

        // 确保所有数据都被正确处理
        const processedSales = salesAnalysis.map(s => s.sales);
        const processedProfits = salesAnalysis.map(s => s.profit);

        // 更新数据
        priceData.value = {
            dates: processedPriceTrends.map(p => formatDate(p.date)),
            costs: processedPriceTrends.map(p => p.cost),
            prices: processedPriceTrends.map(p => p.price)
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
        ElMessage.error('加载分析数据失败');
        priceData.value = initChartData();
        profitData.value = initProfitData();
    }
};

// 处理日期变化
const handleDateChange = () => {
    if (currentProduct.value) {
        loadAnalysisData();
    }
};

// 搜索建议
const querySearch = async (queryString: string, cb: (arg: any[]) => void) => {
    if (!queryString) {
        cb([]);
        return;
    }

    try {
        const response = await searchInventory(queryString);
        const suggestions = response.map(item => ({
            value: item.barcode,
            label: `${item.name} (${item.barcode})`,
            ...item
        }));
        cb(suggestions);
    } catch (error) {
        cb([]);
    }
};

// 选择商品
const handleSelect = (item: Inventory) => {
    searchQuery.value = item.name;
    searchBarcode.value = item.barcode;
    handleSearch();
};

// 添加分页相关的响应式变量
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);

// 修改显示商品列表的方法
const showProductList = async () => {
    try {
        const response = await getInventoryList({
            page: currentPage.value,
            page_size: pageSize.value
        });
        productList.value = response.items;
        total.value = response.total;
        productListVisible.value = true;
    } catch (error) {
        ElMessage.error('加载商品列表失败');
    }
};

// 处理页码变化
const handleCurrentChange = (page: number) => {
    currentPage.value = page;
    showProductList();
};

// 处理每页数量变化
const handleSizeChange = (size: number) => {
    pageSize.value = size;
    currentPage.value = 1; // 重置到第一页
    showProductList();
};

// 从列表选择商品
const handleProductSelect = (row: Inventory) => {
    searchQuery.value = row.name;
    searchBarcode.value = row.barcode;
    productListVisible.value = false;
    handleSearch();
};
</script>

<style scoped>
.page-container {
    padding: 20px;
    height: 100%;
    width: 100%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.toolbar {
    flex-shrink: 0;
}

.search-form {
    display: flex;
    gap: 12px;
    align-items: center;
}

.analysis-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 20px;
    min-height: 800px; /* 确保有最小高度 */
}

.chart-card {
    flex: 1;
    min-height: 400px;
    display: flex;
    flex-direction: column;
}

.chart-wrapper {
    flex: 1;
    min-height: 350px;
    position: relative;
}

.chart {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
}

/* Element Plus 卡片样式覆盖 */
:deep(.el-card) {
    height: 100%;
    display: flex;
    flex-direction: column;
}

:deep(.el-card__header) {
    padding: 12px 20px;
    border-bottom: 1px solid #ebeef5;
}

:deep(.el-card__body) {
    flex: 1;
    padding: 20px;
    overflow: hidden;
}

/* 搜索相关样式 */
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
    width: 300px;
}

/* 图表容器样式 */
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

:deep(.el-date-editor) {
    width: 360px;  /* 调整日期选择器宽度 */
}

.pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
}

/* 调整对话框内容的布局 */
:deep(.el-dialog__body) {
    display: flex;
    flex-direction: column;
    gap: 20px;
    padding: 20px;
}
</style>