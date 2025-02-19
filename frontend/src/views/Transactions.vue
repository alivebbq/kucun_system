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
                    <span>库存: {{ item.stock }}</span>
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
          <el-form-item label="公司">
            <el-select 
              v-model="filters.company_id" 
              placeholder="全部" 
              clearable
              class="company-select"
            >
              <el-option
                v-for="company in companies"
                :key="company.id"
                :label="company.name"
                :value="company.id"
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
            <el-button type="primary" @click="showProductList">
              <el-icon><List /></el-icon>
              选择商品
            </el-button>
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

    <!-- 添加商品列表对话框 -->
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
    </el-dialog>

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
        <el-table-column 
          label="公司" 
          min-width="120"
        >
          <template #default="{ row }">
            {{ row.company?.name || row.company_name || '-' }}
          </template>
        </el-table-column>
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
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search, Refresh, List } from '@element-plus/icons-vue';
import { getTransactions, cancelTransaction, searchInventory, getInventoryList } from '../api/inventory';
import type { Inventory } from '../types/inventory';
import { getCompanies } from '../api/company';
import type { Company } from '../types/company';
import { CompanyType } from '../types/company';

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
  company_id: undefined as number | undefined,
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

// 添加公司列表
const companies = ref<Company[]>([]);

// 加载公司列表
const loadCompanies = async () => {
  try {
    const [suppliers, customers] = await Promise.all([
      getCompanies(CompanyType.SUPPLIER),
      getCompanies(CompanyType.CUSTOMER)
    ]);
    // 合并供应商和客户列表
    companies.value = [...suppliers, ...customers];
  } catch (error) {
    console.error('加载公司列表失败:', error);
    ElMessage.error('加载公司列表失败');
  }
};

// 加载交易记录
const loadTransactions = async () => {
  loading.value = true;
  try {
    const params: any = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    };

    // 添加公司筛选条件
    if (filters.value.company_id) {
      params.company_id = filters.value.company_id;
    }
    // 只添加有值的参数
    if (filters.value.barcode) {
      params.barcode = filters.value.barcode;
    }
    if (filters.value.type) {
      params.type = filters.value.type;
    }
    if (filters.value.startDate) {
      params.start_date = new Date(filters.value.startDate).toISOString();
    }
    if (filters.value.endDate) {
      params.end_date = new Date(filters.value.endDate).toISOString();
    }

    const response = await getTransactions(params);
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
    company_id: undefined,
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

// 添加新的响应式变量
const productListVisible = ref(false);
const productList = ref<Inventory[]>([]);

// 显示商品列表
const showProductList = async () => {
  try {
    const response = await getInventoryList();
    productList.value = response.data;
    productListVisible.value = true;
  } catch (error) {
    console.error('加载商品列表失败:', error);
    ElMessage.error('加载商品列表失败');
  }
};

// 从列表选择商品
const handleProductSelect = (row: Inventory) => {
  searchQuery.value = row.name;
  filters.value.barcode = row.barcode;
  productListVisible.value = false;
  handleSearch();
};

// 搜索商品
const searchProduct = async (query: string) => {
  if (!query) return [];
  try {
    const response = await searchInventory(query);
    return response.data.map((item: Inventory) => ({
      value: item.barcode,
      label: `${item.name} (${item.barcode})`,
      ...item
    }));
  } catch (error) {
    console.error('搜索商品失败:', error);
    return [];
  }
};

// 选择商品
const handleSelect = (item: any) => {
  searchQuery.value = item.name;
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
onMounted(() => {
  loadCompanies();
  loadTransactions();
});
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
    display: flex;
    gap: 10px;
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

.search-input {
  width: 300px;
}

.company-select {
  width: 200px;
}

// 其他样式已在 common.scss 中定义
</style> 