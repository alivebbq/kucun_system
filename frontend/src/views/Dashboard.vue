<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="stat-card">
          <template #header>
            <div class="card-header">
              <span>总商品数</span>
            </div>
          </template>
          <div class="stat-value">
            {{ stats.total_items }}
            <small>种</small>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="stat-card">
          <template #header>
            <div class="card-header">
              <span>库存总值</span>
            </div>
          </template>
          <div class="stat-value">
            ¥{{ formatNumber(stats.total_value) }}
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="stat-card warning">
          <template #header>
            <div class="card-header">
              <span>低库存商品</span>
            </div>
          </template>
          <div class="stat-value">
            {{ stats.low_stock_items }}
            <small>种</small>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-4">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>近7天交易趋势</span>
            </div>
          </template>
          <div ref="transactionChart" style="height: 300px"></div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>库存预警</span>
            </div>
          </template>
          <el-table :data="lowStockItems" style="width: 100%">
            <el-table-column prop="name" label="商品名称" />
            <el-table-column prop="stock" label="当前库存" width="100" />
            <el-table-column prop="warning_stock" label="警戒库存" width="100" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getInventoryStats, getInventoryList, getTransactions } from '../api/inventory';
import type { InventoryStats, Inventory, Transaction } from '../api/inventory';
import * as echarts from 'echarts';

const stats = ref<InventoryStats>({
  total_items: 0,
  total_value: 0,
  low_stock_items: 0
});

const lowStockItems = ref<Inventory[]>([]);
const transactionChart = ref<HTMLElement>();
let chart: echarts.ECharts;

// 格式化数字
const formatNumber = (num: number) => {
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
};

// 初始化交易趋势图
const initTransactionChart = (transactions: Transaction[]) => {
  if (!transactionChart.value) return;
  
  // 按日期分组交易数据
  const dateMap = new Map<string, { in: number; out: number }>();
  const now = new Date();
  for (let i = 6; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];
    dateMap.set(dateStr, { in: 0, out: 0 });
  }

  transactions.forEach(t => {
    const date = t.timestamp.split('T')[0];
    if (dateMap.has(date)) {
      const data = dateMap.get(date)!;
      if (t.type === 'in') {
        data.in += t.total;
      } else {
        data.out += t.total;
      }
    }
  });

  const dates = Array.from(dateMap.keys());
  const inData = dates.map(d => dateMap.get(d)!.in);
  const outData = dates.map(d => dateMap.get(d)!.out);

  chart = echarts.init(transactionChart.value);
  chart.setOption({
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['入库金额', '出库金额']
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '入库金额',
        type: 'line',
        data: inData
      },
      {
        name: '出库金额',
        type: 'line',
        data: outData
      }
    ]
  });
};

// 加载数据
const loadData = async () => {
  try {
    // 获取统计数据
    stats.value = await getInventoryStats();
    
    // 获取低库存商品
    const inventory = await getInventoryList();
    lowStockItems.value = inventory.filter(
      item => item.stock <= item.warning_stock
    );
    
    // 获取近7天交易记录
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 7);
    
    const transactions = await getTransactions({
      start_date: startDate.toISOString(),
      end_date: endDate.toISOString()
    });
    
    initTransactionChart(transactions);
  } catch (error) {
    console.error('加载数据失败:', error);
  }
};

onMounted(() => {
  loadData();
  
  // 监听窗口大小变化，调整图表大小
  window.addEventListener('resize', () => {
    chart?.resize();
  });
});
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-card {
  height: 160px;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  text-align: center;
  padding: 20px 0;
}

.stat-value small {
  font-size: 16px;
  margin-left: 5px;
}

.warning .stat-value {
  color: #f56c6c;
}

.mt-4 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 