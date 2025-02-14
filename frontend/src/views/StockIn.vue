<template>
  <div class="page-container">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-form :inline="true" class="search-form">
          <el-form-item>
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
        </el-form>
      </div>
    </div>

    <!-- 商品信息卡片 -->
    <el-card v-if="currentProduct" class="content-card product-info">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="商品名称">{{ currentProduct.name }}</el-descriptions-item>
        <el-descriptions-item label="条形码">{{ currentProduct.barcode }}</el-descriptions-item>
        <el-descriptions-item label="单位">{{ currentProduct.unit }}</el-descriptions-item>
        <el-descriptions-item label="当前库存">
          <span :class="{ 'low-stock': currentProduct.stock <= currentProduct.warning_stock }">
            {{ currentProduct.stock }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="警戒库存">{{ currentProduct.warning_stock }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentProduct.is_active ? 'success' : 'danger'">
            {{ currentProduct.is_active ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 入库表单 -->
      <el-form 
        ref="formRef" 
        :model="form" 
        :rules="rules" 
        label-width="100px"
        class="custom-form stock-form"
      >
        <el-form-item label="入库数量" prop="quantity">
          <el-input
            v-model="form.quantity"
            placeholder="请输入数量"
            class="number-input"
            @input="handleQuantityInput"
          >
            <template #suffix>{{ currentProduct?.unit }}</template>
          </el-input>
        </el-form-item>
        <el-form-item label="单价" prop="price">
          <el-input
            v-model="form.price"
            placeholder="请输入单价"
            class="number-input"
            @input="handlePriceInput"
          >
            <template #prefix>¥</template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            @click="handleSubmit"
            :disabled="!currentProduct?.is_active"
          >
            确认入库
          </el-button>
          <span v-if="!currentProduct?.is_active" class="disabled-tip">
            禁用商品不能入库
          </span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 最近入库记录 -->
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>最近入库记录</span>
        </div>
      </template>

      <el-table 
        :data="recentRecords" 
        style="width: 100%"
        :header-cell-class-name="'table-header'"
      >
        <el-table-column prop="barcode" label="条形码" width="150" />
        <el-table-column prop="name" label="商品名称" />
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
        <el-table-column prop="timestamp" label="入库时间" width="180">
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
    </el-card>

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
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search, List } from '@element-plus/icons-vue';
import type { FormInstance, FormRules } from 'element-plus';
import {
  getInventoryByBarcode,
  stockIn,
  getTransactions,
  cancelTransaction,
  type Inventory,
  type Transaction,
  searchInventory,
  getInventoryList
} from '../api/inventory';

const formRef = ref<FormInstance>();
const loading = ref(false);
const currentProduct = ref<Inventory | null>(null);
const recentRecords = ref<Transaction[]>([]);

const form = ref({
  barcode: '',
  quantity: '',
  price: ''
});

const rules: FormRules = {
  barcode: [
    { required: true, message: '请输入条形码', trigger: 'blur' }
  ],
  quantity: [
    { required: true, message: '请输入数量', trigger: 'blur' },
    { 
      validator: (rule: any, value: string) => {
        const num = parseInt(value);
        if (isNaN(num) || num <= 0) {
          return Promise.reject('请输入大于0的数量');
        }
        return Promise.resolve();
      },
      trigger: 'blur'
    }
  ],
  price: [
    { required: true, message: '请输入单价', trigger: 'blur' },
    {
      validator: (rule: any, value: string) => {
        const num = parseFloat(value);
        if (isNaN(num) || num < 0) {
          return Promise.reject('请输入有效的单价');
        }
        return Promise.resolve();
      },
      trigger: 'blur'
    }
  ]
};

// 商品列表相关
const productListVisible = ref(false);
const productList = ref<Inventory[]>([]);

// 搜索查询
const searchQuery = ref('');

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

// 搜索建议
const querySearch = async (queryString: string) => {
  if (!queryString) return [];
  try {
    const response = await searchInventory(queryString);
    return response.map(item => ({
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
  if (!item.is_active) {
    ElMessage.warning('该商品已禁用，无法选择');
    searchQuery.value = '';
    return;
  }
  currentProduct.value = item;
  form.value.barcode = item.barcode;
};

// 加载最近入库记录
const loadRecentRecords = async () => {
  try {
    const response = await getTransactions({
      type: 'in',  // 只获取入库记录
      limit: 10
    });
    recentRecords.value = response.items;  // 使用 response.items
  } catch (error) {
    console.error('加载入库记录失败:', error);
    ElMessage.error('加载入库记录失败');
  }
};

// 处理数量输入
const handleQuantityInput = (value: string) => {
  // 只允许输入正整数
  const newValue = value.replace(/[^\d]/g, '');
  if (newValue === '') {
    form.value.quantity = '';
  } else {
    const num = parseInt(newValue);
    form.value.quantity = num > 0 ? num : '';
  }
};

// 处理价格输入
const handlePriceInput = (value: string) => {
  // 移除非数字和小数点
  let newValue = value.replace(/[^\d.]/g, '');
  // 确保只有一个小数点
  const parts = newValue.split('.');
  if (parts.length > 2) {
    newValue = parts[0] + '.' + parts.slice(1).join('');
  }
  // 限制小数位数为2位
  if (parts.length === 2 && parts[1].length > 2) {
    newValue = parts[0] + '.' + parts[1].slice(0, 2);
  }
  form.value.price = newValue;
};

// 提交入库
const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const quantity = parseInt(form.value.quantity);
        await stockIn({
          barcode: form.value.barcode,
          quantity: quantity,
          price: form.value.price
        });
        ElMessage.success('入库成功');

        // 重置表单
        form.value = {
          barcode: '',
          quantity: '',
          price: ''
        };
        currentProduct.value = null;
        formRef.value.resetFields();

        // 刷新记录
        loadRecentRecords();
      } catch (error) {
        console.error('入库失败:', error);
        ElMessage.error('入库失败');
      } finally {
        loading.value = false;
      }
    }
  });
};

// 显示商品列表
const showProductList = async () => {
  try {
    const response = await getInventoryList();
    productList.value = response;
    productListVisible.value = true;
  } catch (error) {
    console.error('加载商品列表失败:', error);
    ElMessage.error('加载商品列表失败');
  }
};

// 选择商品
const handleProductSelect = (row: Inventory) => {
  if (!row.is_active) {
    ElMessage.warning('该商品已禁用，无法选择');
    return;
  }
  currentProduct.value = row;
  form.value.barcode = row.barcode;
  productListVisible.value = false;
};

// 处理撤销
const handleCancel = async (row: Transaction) => {
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

    console.log('Cancelling transaction:', row.id);
    await cancelTransaction(row.id);
    ElMessage.success('撤销成功');
    // 刷新记录列表和当前商品信息
    loadRecentRecords();
    if (currentProduct.value?.barcode === row.barcode) {
      await querySearch(row.barcode);
    }
  } catch (error: any) {
    console.error('Cancel error:', error);
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '撤销失败');
    }
  }
};

onMounted(() => {
  loadRecentRecords();
});
</script>

<style lang="scss" scoped>
.stock-form {
  margin-top: 20px;
  max-width: 500px;
}

.search-form {
  display: flex;
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

.low-stock {
  color: #F56C6C;
  font-weight: bold;
}

.disabled-tip {
  margin-left: 10px;
  color: #F56C6C;
  font-size: 14px;
}

.number-input {
  width: 100%;
  
  :deep(.el-input__wrapper) {
    padding-right: 8px;
  }
  
  :deep(.el-input__prefix) {
    color: #909399;
    font-weight: bold;
  }
  
  :deep(.el-input__suffix) {
    color: #909399;
  }
}

// 其他样式已在 common.scss 中定义
</style>