<template>
  <div class="performance">
    <!-- 日期选择器 -->
    <el-card class="date-picker">
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        :shortcuts="dateShortcuts"
        value-format="YYYY-MM-DD"
        :clearable="false"
        @change="handleDateChange"
      />
    </el-card>

    <!-- 当有日期选择时才显示内容 -->
    <template v-if="dateRange">
      <!-- 销售汇总 -->
      <el-card class="summary">
        <template #header>
          <div class="card-header">
            <span>销售汇总</span>
          </div>
        </template>
        <el-row :gutter="20">
          <el-col :span="5">
            <div class="stat-item">
              <div class="label">进货总额</div>
              <div class="value">¥{{ formatNumber(stats.summary.total_purchase) }}</div>
            </div>
          </el-col>
          <el-col :span="5">
            <div class="stat-item">
              <div class="label">销售总额</div>
              <div class="value">¥{{ formatNumber(stats.summary.total_sales) }}</div>
            </div>
          </el-col>
          <el-col :span="5">
            <div class="stat-item">
              <div class="label">销售成本(先进先出法)</div>
              <div class="value cost">¥{{ formatNumber(stats.summary.total_sales_cost) }}</div> 
            </div>
          </el-col>
          <el-col :span="5">
            <div class="stat-item">
              <div class="label">总利润</div>
              <div class="value profit">¥{{ formatNumber(stats.summary.total_profit) }}</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="stat-item">
              <div class="label">利润率</div>
              <div class="value">{{ formatNumber(stats.summary.profit_rate) }}%</div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 利润排名 -->
      <el-card class="rankings">
        <template #header>
          <div class="card-header">
            <span>商品利润排名</span>
            <el-radio-group v-model="profitSortBy" size="small" @change="handleProfitSortChange">
              <el-radio-button label="profit">按利润</el-radio-button>
              <el-radio-button label="rate">按利润率</el-radio-button>
            </el-radio-group>
          </div>
        </template>
        <el-table :data="currentProfitRankings" style="width: 100%">
          <el-table-column type="index" label="排名" width="80" />
          <el-table-column prop="barcode" label="条形码" width="150" />
          <el-table-column prop="name" label="商品名称" />
          <el-table-column
            prop="total_cost"
            label="总成本"
            width="120"
            align="right"
          >
            <template #default="{ row }">
              ¥{{ formatNumber(row.total_cost) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="total_revenue"
            label="总收入"
            width="120"
            align="right"
          >
            <template #default="{ row }">
              ¥{{ formatNumber(row.total_revenue) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="profit"
            label="利润"
            width="120"
            align="right"
          >
            <template #default="{ row }">
              ¥{{ formatNumber(row.profit) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="profit_rate"
            label="利润率"
            width="100"
            align="right"
          >
            <template #default="{ row }">
              {{ formatNumber(row.profit_rate) }}%
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="profitCurrentPage"
            v-model:page-size="profitPageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="sortedProfitRankings.length"
            layout="total, sizes, prev, pager, next"
            @size-change="handleProfitSizeChange"
            @current-change="handleProfitPageChange"
          />
        </div>
      </el-card>

      <!-- 销售额排名 -->
      <el-card class="rankings">
        <template #header>
          <div class="card-header">
            <span>商品销售排名</span>
          </div>
        </template>
        <el-table :data="currentSalesRankings" style="width: 100%">
          <el-table-column type="index" label="排名" width="80" />
          <el-table-column prop="barcode" label="条形码" width="150" />
          <el-table-column prop="name" label="商品名称" />
          <el-table-column
            prop="quantity"
            label="销售数量"
            width="120"
            align="right"
          />
          <el-table-column
            prop="revenue"
            label="销售额"
            width="120"
            align="right"
          >
            <template #default="{ row }">
              ¥{{ formatNumber(row.revenue) }}
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="salesCurrentPage"
            v-model:page-size="salesPageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="stats.sales_rankings.length"
            layout="total, sizes, prev, pager, next"
            @size-change="handleSalesSizeChange"
            @current-change="handleSalesPageChange"
          />
        </div>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { getPerformanceStats, type PerformanceStats } from '../api/inventory';

const stats = ref<PerformanceStats>({
  profit_rankings: [],
  sales_rankings: [],
  summary: {
    total_purchase: 0,
    total_sales: 0,
    total_sales_cost: 0,
    total_profit: 0,
    profit_rate: 0
  }
});

// 移除默认日期范围
const dateRange = ref<[Date, Date] | null>(null);

// 排序方式
const profitSortBy = ref<'profit' | 'rate'>('profit');

// 计算排序后的利润排名
const sortedProfitRankings = computed(() => {
  if (!stats.value.profit_rankings) return [];
  
  return [...stats.value.profit_rankings].sort((a, b) => {
    if (profitSortBy.value === 'profit') {
      return b.profit - a.profit;  // 按利润降序
    } else {
      return b.profit_rate - a.profit_rate;  // 按利润率降序
    }
  });
});

// 处理排序方式变化
const handleProfitSortChange = () => {
  // 不需要特别处理，因为使用了计算属性
};

// 格式化数字
const formatNumber = (num: number) => {
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
};

// 格式化日期范围显示
const formatDateRange = (range: [Date, Date] | null) => {
  if (!range) return '';
  const [start, end] = range;
  const formatDate = (date: Date | number) => {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };
  return `${formatDate(start)} 至 ${formatDate(end)}`;
};

// 添加日期快捷选项
const dateShortcuts = [
  {
    text: '最近一周',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
      return [start, end];
    },
  },
  {
    text: '本月',
    value: () => {
      const end = new Date();
      const start = new Date(end.getFullYear(), end.getMonth(), 1);
      return [start, end];
    },
  },
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
    text: '最近三月',
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

// 修改加载数据的方法
const loadStats = async () => {
  if (!dateRange.value) return;  // 如果没有选择日期，不加载数据
  
  try {
    const [start, end] = dateRange.value;
    
    const formatForApi = (date: Date | number) => {
      const d = new Date(date);
      return d.toISOString().split('T')[0];
    };
    
    const response = await getPerformanceStats({
      start_date: `${formatForApi(start)}T00:00:00`,
      end_date: `${formatForApi(end)}T23:59:59`
    });
    
    stats.value = response;
  } catch (error) {
    ElMessage.error('加载统计数据失败');
  }
};

// 处理日期变化
const handleDateChange = () => {
  loadStats();
};

// 添加分页相关的响应式变量
const profitCurrentPage = ref(1);
const profitPageSize = ref(10);
const salesCurrentPage = ref(1);
const salesPageSize = ref(10);

// 计算当前页的利润排名数据
const currentProfitRankings = computed(() => {
  const start = (profitCurrentPage.value - 1) * profitPageSize.value;
  const end = start + profitPageSize.value;
  return sortedProfitRankings.value.slice(start, end);
});

// 计算当前页的销售排名数据
const currentSalesRankings = computed(() => {
  const start = (salesCurrentPage.value - 1) * salesPageSize.value;
  const end = start + salesPageSize.value;
  return stats.value.sales_rankings.slice(start, end);
});

// 处理利润排名分页
const handleProfitSizeChange = (size: number) => {
  profitPageSize.value = size;
  profitCurrentPage.value = 1;
};

const handleProfitPageChange = (page: number) => {
  profitCurrentPage.value = page;
};

// 处理销售排名分页
const handleSalesSizeChange = (size: number) => {
  salesPageSize.value = size;
  salesCurrentPage.value = 1;
};

const handleSalesPageChange = (page: number) => {
  salesCurrentPage.value = page;
};

onMounted(() => {
  // 不再自动加载数据
});
</script>

<style scoped>
.performance {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background-color: #f5f7fa;
  min-height: 100%;
}

.date-picker {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background-color: #fff;
  
  .date-info {
    .date-label {
      color: #606266;
      margin-right: 8px;
    }
    
    .date-value {
      font-weight: bold;
      color: #409EFF;
    }
  }
}

.summary {
  margin-bottom: 20px;
  background-color: #fff;
}

.stat-item {
  text-align: center;
  padding: 15px 5px;
  background-color: #f8f9fa;
  border-radius: 4px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-item .label {
  color: #666;
  margin-bottom: 8px;
  font-size: 14px;
  white-space: nowrap;
}

.stat-item .value {
  font-size: 16px;
  font-weight: bold;
  color: #409EFF;
  line-height: 1.2;
  word-break: break-all;
  padding: 0 2px;
}

.stat-item .value.profit {
  color: #67C23A;
}

.stat-item .value.cost {
  color: #E6A23C;
}

.rankings {
  margin-bottom: 20px;
  background-color: #fff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-card__header) {
  padding: 15px 20px;
}

:deep(.el-table) {
  margin-top: 10px;
}

.el-row {
  margin: 0 !important;
}

.el-col {
  padding: 0 5px !important;
}

.summary .el-card__body {
  padding: 10px;
}

/* 添加排序按钮组的样式 */
.card-header :deep(.el-radio-group) {
  margin-left: 16px;
}

.card-header :deep(.el-radio-button__inner) {
  padding: 5px 15px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style> 