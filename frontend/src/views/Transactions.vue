<template>
  <div class="transactions">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>交易记录</span>
          <div class="header-actions">
            <el-button type="primary" @click="handleExport">
              <el-icon><Download /></el-icon>
              导出Excel
            </el-button>
          </div>
        </div>
      </template>

      <!-- 搜索条件 -->
      <div class="search-form">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="商品条码">
            <el-input
              v-model="searchForm.barcode"
              placeholder="请输入商品条码"
              clearable
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          
          <el-form-item label="交易类型">
            <el-select v-model="searchForm.type" placeholder="请选择" clearable>
              <el-option
                label="入库"
                value="in"
              >
                <el-tag type="success" size="small">入库</el-tag>
              </el-option>
              <el-option
                label="出库"
                value="out"
              >
                <el-tag type="danger" size="small">出库</el-tag>
              </el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item label="交易时间">
            <el-date-picker
              v-model="searchForm.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button @click="handleReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 交易记录表格 -->
      <el-table
        :data="transactions"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="barcode" label="条形码" width="150" />
        <el-table-column prop="name" label="商品名称" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.type === 'in' ? 'success' : 'danger'">
              {{ row.type === 'in' ? '入库' : '出库' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="100" align="right" />
        <el-table-column
          prop="price"
          label="单价"
          width="120"
          align="right"
        >
          <template #default="{ row }">
            ¥{{ formatNumber(row.price) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="total"
          label="总金额"
          width="120"
          align="right"
        >
          <template #default="{ row }">
            ¥{{ formatNumber(row.total) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="timestamp"
          label="交易时间"
          width="180"
          sortable
        >
          <template #default="{ row }">
            {{ formatDate(row.timestamp) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Search, Refresh, Download } from '@element-plus/icons-vue';
import { getTransactions, type Transaction } from '../api/inventory';

const loading = ref(false);
const transactions = ref<Transaction[]>([]);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

const searchForm = reactive({
  barcode: '',
  type: '',
  dateRange: [] as string[]
});

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
    const params: any = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    };

    if (searchForm.barcode) {
      params.barcode = searchForm.barcode;
    }
    if (searchForm.type) {
      params.type = searchForm.type;
    }
    if (searchForm.dateRange?.length === 2) {
      params.start_date = `${searchForm.dateRange[0]}T00:00:00`;
      params.end_date = `${searchForm.dateRange[1]}T23:59:59`;
    }

    const data = await getTransactions(params);
    transactions.value = data;
    total.value = data.length; // TODO: 后端需要返回总数
  } catch (error) {
    console.error('加载交易记录失败:', error);
    ElMessage.error('加载交易记录失败');
  } finally {
    loading.value = false;
  }
};

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1;
  loadTransactions();
};

// 处理重置
const handleReset = () => {
  searchForm.barcode = '';
  searchForm.type = '';
  searchForm.dateRange = [];
  handleSearch();
};

// 处理导出
const handleExport = () => {
  // TODO: 实现导出功能
  ElMessage.warning('导出功能开发中');
};

// 处理页码变化
const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  loadTransactions();
};

// 处理每页条数变化
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  loadTransactions();
};

onMounted(() => {
  loadTransactions();
});
</script>

<style scoped>
.transactions {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-select) {
  width: 120px;
}

:deep(.el-select .el-input__wrapper) {
  background-color: var(--el-fill-color-blank);
}

:deep(.el-select-dropdown__item) {
  padding: 0 12px;
  height: 34px;
  line-height: 34px;
}

:deep(.el-tag) {
  width: 100%;
  text-align: center;
  margin: 0;
}
</style> 