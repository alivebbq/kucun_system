<template>
  <div class="page-container">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-form :inline="true" class="search-form">
          <el-form-item label="商品">
            <el-autocomplete
              v-model="searchQuery"
              :fetch-suggestions="searchProduct"
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
                  </div>
                </div>
              </template>
            </el-autocomplete>
          </el-form-item>
          <el-form-item label="类型">
            <el-select 
              v-model="filters.type" 
              placeholder="全部" 
              clearable
              class="type-select"
            >
              <el-option 
                v-for="(label, value) in transactionTypes" 
                :key="value" 
                :label="label" 
                :value="value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="日期">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              :shortcuts="dateShortcuts"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button @click="resetFilters">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 交易记录表格 -->
    <el-card class="content-card">
      <el-table 
        :data="transactions" 
        style="width: 100%"
        v-loading="loading"
        :header-cell-class-name="'table-header'"
      >
        <el-table-column prop="barcode" label="条形码" width="150" />
        <el-table-column prop="name" label="商品名称" min-width="150" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="row.type === 'in' ? 'success' : 'warning'"
              effect="light"
            >
              {{ transactionTypes[row.type] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="100" align="right" />
        <el-table-column prop="price" label="单价" width="120" align="right">
          <template #default="{ row }">
            <span class="amount">¥{{ formatNumber(row.price) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="total" label="总金额" width="120" align="right">
          <template #default="{ row }">
            <span class="amount">¥{{ formatNumber(row.total) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作人" width="120" />
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="danger" 
              link 
              @click="handleCancel(row)"
            >
              撤销
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search, Refresh } from '@element-plus/icons-vue';
import { getTransactions, cancelTransaction, searchInventory } from '../api/inventory';

const loading = ref(false);
const transactions = ref([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

// 搜索和筛选
const searchQuery = ref('');
const filters = ref({
  barcode: '',
  type: '',
  startDate: '',
  endDate: ''
});

// 日期范围
const dateRange = ref([]);

// 日期快捷选项
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
    text: '最近一个月',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
      return [start, end];
    },
  },
  {
    text: '最近三个月',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
      return [start, end];
    },
  },
];

// 交易类型映射
const transactionTypes = {
  'in': '入库',
  'out': '出库'
};

// 格式化数字
const formatNumber = (num: number) => {
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
};

// 格式化日期
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 加载交易记录
const loadTransactions = async () => {
  loading.value = true;
  try {
    const response = await getTransactions({
      barcode: filters.value.barcode,
      type: filters.value.type,
      start_date: filters.value.startDate,
      end_date: filters.value.endDate,
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    });
    transactions.value = response.items;
    total.value = response.total;
  } catch (error) {
    console.error('加载交易记录失败:', error);
    ElMessage.error('加载交易记录失败');
  } finally {
    loading.value = false;
  }
};

// 处理搜索
const handleSearch = () => {
  if (dateRange.value?.length === 2) {
    filters.value.startDate = dateRange.value[0];
    filters.value.endDate = dateRange.value[1];
  } else {
    filters.value.startDate = '';
    filters.value.endDate = '';
  }
  currentPage.value = 1;
  loadTransactions();
};

// 重置筛选条件
const resetFilters = () => {
  searchQuery.value = '';
  filters.value = {
    barcode: '',
    type: '',
    startDate: '',
    endDate: ''
  };
  dateRange.value = [];
  currentPage.value = 1;
  loadTransactions();
};

// 处理分页
const handleSizeChange = (val: number) => {
  pageSize.value = val;
  loadTransactions();
};

const handleCurrentChange = (val: number) => {
  currentPage.value = val;
  loadTransactions();
};

// 搜索商品
const searchProduct = async (query: string) => {
  if (!query) return [];
  try {
    const items = await searchInventory(query);
    return items.map(item => ({
      value: item.barcode,
      ...item
    }));
  } catch (error) {
    console.error('搜索商品失败:', error);
    return [];
  }
};

// 选择商品
const handleSelect = (item: any) => {
  filters.value.barcode = item.barcode;
  handleSearch();
};

// 处理撤销
const handleCancel = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      '确定要撤销这条记录吗？这将会相应调整库存数量。',
      '撤销确认',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    );

    await cancelTransaction(row.id);
    ElMessage.success('撤销成功');
    loadTransactions();
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('撤销失败:', error);
      ElMessage.error(error.response?.data?.detail || '撤销失败');
    }
  }
};

// 初始化
loadTransactions();
</script>

<style lang="scss" scoped>
.search-form {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.search-item {
  padding: 4px 0;

  .name {
    font-weight: bold;
  }

  .info {
    font-size: 12px;
    color: #666;
  }
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.type-select {
  width: 120px;
}

// 其他样式已在 common.scss 中定义
</style> 