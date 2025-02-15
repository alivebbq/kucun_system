<template>
  <div class="performance">
    <!-- 日期选择器 -->
    <el-card class="date-picker">
      <el-date-picker
        v-model="dateRange"
        type="monthrange"
        range-separator="至"
        start-placeholder="开始月份"
        end-placeholder="结束月份"
        :default-value="defaultDateRange"
        value-format="YYYY-MM-DD"
        @change="handleDateChange"
      />
    </el-card>

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
      <el-table :data="sortedProfitRankings" style="width: 100%">
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
    </el-card>

    <!-- 销售额排名 -->
    <el-card class="rankings">
      <template #header>
        <div class="card-header">
          <span>商品销售排名</span>
        </div>
      </template>
      <el-table :data="stats.sales_rankings" style="width: 100%">
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
    </el-card>
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

// 默认日期范围（当前月份）
const defaultDateRange = [
  new Date().setDate(1),
  new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0)
];
const dateRange = ref(defaultDateRange);

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

// 加载数据
const loadStats = async () => {
  try {
    const [start_date, end_date] = dateRange.value;
    console.log('Date range:', { start_date, end_date });
    
    const response = await getPerformanceStats({
      start_date: start_date ? `${new Date(start_date).toISOString().split('T')[0]}T00:00:00` : undefined,
      end_date: end_date ? `${new Date(end_date).toISOString().split('T')[0]}T23:59:59` : undefined
    });
    console.log('Performance stats response:', response);
    
    stats.value = response;
  } catch (error) {
    console.error('加载统计数据失败:', error);
    ElMessage.error('加载统计数据失败');
  }
};

// 处理日期变化
const handleDateChange = () => {
  loadStats();
};

onMounted(() => {
  loadStats();
});
</script>

<style scoped>
.performance {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.date-picker {
  display: flex;
  justify-content: flex-end;
  padding: 10px;
}

.summary {
  margin-bottom: 20px;
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
</style> 