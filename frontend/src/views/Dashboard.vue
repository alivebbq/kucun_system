<template>
  <div class="dashboard">
    <!-- 顶部数据卡片 -->
    <el-row :gutter="20" class="top-row">
      <el-col :span="8">
        <el-card class="data-card">
          <div class="card-content">
            <div class="title">库存总值</div>
            <div class="value">¥{{ formatNumber(stats.total_value) }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="data-card">
          <div class="card-content">
            <div class="title">今日销售额</div>
            <div class="value warning">¥{{ formatNumber(stats.today_sales) }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="data-card">
          <div class="card-content">
            <div class="title">近7天销售额</div>
            <div class="value success">¥{{ formatNumber(stats.week_sales) }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 主要内容区 -->
    <el-row :gutter="20" class="main-row">
      <!-- 左侧：热销商品 -->
      <el-col :span="12">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>近7天热销产品</span>
              <el-tag type="success" v-if="stats.hot_products.length">
                销售额 TOP {{ stats.hot_products.length }}
              </el-tag>
            </div>
          </template>
          <div v-if="stats.hot_products.length" class="hot-list">
            <div v-for="(product, index) in stats.hot_products" :key="product.barcode" class="hot-item">
              <span class="rank" :class="`rank-${index + 1}`">{{ index + 1 }}</span>
              <div class="product-info">
                <div class="name">{{ product.name }}</div>
                <div class="details">
                  <span class="quantity">销量: {{ product.quantity }}</span>
                  <span class="revenue">销售额: ¥{{ formatNumber(product.revenue) }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="empty-hot">
            <el-empty description="暂无销售数据" />
          </div>
        </el-card>
      </el-col>
      
      <!-- 右侧：库存预警 -->
      <el-col :span="12">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>库存预警</span>
              <el-tag type="danger" v-if="stats.low_stock_items.length">
                {{ stats.low_stock_items.length }} 个商品库存不足
              </el-tag>
            </div>
          </template>
          <el-table
            v-if="stats.low_stock_items.length"
            :data="stats.low_stock_items"
            style="width: 100%"
            size="small"
            :max-height="tableMaxHeight"
          >
            <el-table-column prop="name" label="商品名称" min-width="120" show-overflow-tooltip />
            <el-table-column prop="barcode" label="条形码" width="120" />
            <el-table-column 
              label="剩余库存" 
              width="100" 
              align="center"
            >
              <template #default="{ row }">
                {{ row.stock }}{{ row.unit }}
              </template>
            </el-table-column>
            <el-table-column label="库存状态" width="200" align="center">
              <template #default="{ row }">
                <el-progress
                  :percentage="Math.round((row.stock / row.warning_stock) * 100)"
                  :status="row.stock === 0 ? 'exception' : 'warning'"
                  :stroke-width="10"
                  :format="() => `${row.stock}/${row.warning_stock}`"
                />
              </template>
            </el-table-column>
          </el-table>
          <div v-else class="empty-warning">
            <el-empty description="暂无库存预警">
              <template #image>
                <el-icon class="success-icon"><CircleCheckFilled /></el-icon>
              </template>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { CircleCheckFilled } from '@element-plus/icons-vue';
import { getInventoryStats, type HotProduct } from '../api/inventory';
import { api } from '../api/config';

interface LowStockItem {
  barcode: string;
  name: string;
  stock: number;
  warning_stock: number;
  unit: string;
}

interface Stats {
  total_value: number;
  today_sales: number;
  week_sales: number;
  low_stock_items: LowStockItem[];
  hot_products: HotProduct[];
}

const stats = ref<Stats>({
  total_value: 0,
  today_sales: 0,
  week_sales: 0,
  low_stock_items: [],
  hot_products: []
});

const formatNumber = (num: number) => {
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
};

const loading = ref(false);

const loadStatistics = async () => {
  try {
    loading.value = true;
    console.log('=== Loading Statistics ===');
    const response = await api.get('/api/v1/statistics');
    console.log('Statistics response:', response);
    stats.value = response;
  } catch (error: any) {
    console.error('Error loading statistics:', {
      error,
      response: error.response,
      status: error.response?.status,
      data: error.response?.data
    });
    ElMessage.error(error.response?.data?.detail || '加载统计数据失败');
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadStatistics();
});

// 设置表格最大高度
const tableMaxHeight = 'calc(100vh - 280px)';
</script>

<style scoped>
.dashboard {
  padding: 12px;
  height: 100%;
  background-color: #f5f7fa;
  max-width: 1600px;
  margin: 0 auto;
}

.top-row {
  margin-bottom: 12px;
}

.el-row {
  margin-left: -6px !important;
  margin-right: -6px !important;
}

.el-col {
  padding-left: 6px !important;
  padding-right: 6px !important;
}

.data-card {
  height: 120px;
  background-color: #fff;
  border-radius: 8px;
  transition: all 0.3s;
}

.data-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.card-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.card-content .title {
  font-size: 16px;
  color: #909399;
  margin-bottom: 15px;
}

.card-content .value {
  font-size: 28px;
  font-weight: bold;
  color: #409EFF;
}

.value.warning {
  color: #E6A23C;
}

.value.success {
  color: #67C23A;
}

.content-card {
  height: calc(100vh - 192px);
  background-color: #fff;
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 10px;
}

.hot-list {
  padding: 10px;
  height: calc(100% - 55px);
  overflow-y: auto;
}

.hot-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  background-color: #f8f9fa;
  transition: all 0.3s;
}

.hot-item:hover {
  transform: translateX(5px);
  background-color: #ecf5ff;
}

.rank {
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  color: white;
  border-radius: 50%;
  margin-right: 12px;
  font-weight: bold;
  font-size: 12px;
}

.rank-1 { background-color: #f56c6c; }
.rank-2 { background-color: #e6a23c; }
.rank-3 { background-color: #409eff; }
.rank-4 { background-color: #67c23a; }
.rank-5 { background-color: #909399; }
.rank-6, .rank-7, .rank-8, .rank-9, .rank-10 { 
  background-color: #a0cfff;
}

.product-info {
  flex: 1;
}

.product-info .name {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 4px;
}

.product-info .details {
  color: #909399;
  font-size: 12px;
}

.details .quantity {
  margin-right: 20px;
}

.details .revenue {
  color: #67C23A;
  font-weight: bold;
}

.empty-warning, .empty-hot {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.success-icon {
  font-size: 48px;
  color: #67C23A;
}

:deep(.el-progress-bar__innerText) {
  color: #666;
}

:deep(.el-card__body) {
  height: calc(100% - 55px);
  padding: 10px;
}
</style> 