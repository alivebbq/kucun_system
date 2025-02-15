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

      <!-- 出库表单 -->
      <el-form 
        ref="formRef" 
        :model="form" 
        :rules="rules" 
        label-width="100px"
        class="custom-form stock-form"
      >
        <el-form-item label="出库数量" prop="quantity">
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
            :disabled="!canSubmit"
          >
            确认出库
          </el-button>
          <span v-if="!currentProduct.is_active" class="disabled-tip">
            禁用商品不能出库
          </span>
          <span v-else-if="currentProduct.stock <= 0" class="disabled-tip">
            库存不足
          </span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 最近出库记录 -->
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>最近出库记录</span>
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
        <el-table-column prop="timestamp" label="出库时间" width="180">
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
        <el-table-column prop="stock" label="库存" width="100" align="right">
          <template #default="{ row }">
            <span :class="{ 'low-stock': row.stock <= row.warning_stock }">
              {{ row.stock }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 可以添加一个库存提示 -->
    <div v-if="currentProduct" class="stock-hint">
      当前库存: {{ currentProduct.stock }}{{ currentProduct.unit }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search, List } from '@element-plus/icons-vue';
import type { FormInstance, FormRules } from 'element-plus';
import {
  getInventoryByBarcode,
  stockOut,
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

// 表单验证规则
const rules = {
  barcode: [
    { required: true, message: '请选择商品', trigger: 'change' }
  ],
  quantity: [
    { required: true, message: '请输入数量', trigger: 'blur' },
    { 
      validator: async (rule: any, value: string) => {
        if (!value) return;
        
        const num = parseInt(value);
        if (isNaN(num) || num <= 0) {
          return Promise.reject('请输入大于0的数量');
        }
        
        // 检查是否超过库存
        if (currentProduct.value && num > currentProduct.value.stock) {
          return Promise.reject(`出库数量不能超过当前库存(${currentProduct.value.stock}${currentProduct.value.unit})`);
        }
      }
    }
  ],
  price: [
    { required: true, message: '请输入单价', trigger: 'blur' },
    {
      validator: async (rule: any, value: string) => {
        if (!value) return;
        
        const num = parseFloat(value);
        if (isNaN(num) || num < 0) {
          return Promise.reject('请输入有效的单价');
        }
      }
    }
  ]
};

// 判断是否低库存
const isLowStock = computed(() => {
  if (!currentProduct.value) return false;
  return currentProduct.value.stock <= currentProduct.value.warning_stock;
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

// 搜索查询
const searchQuery = ref('');

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
    console.error('搜索商品失败:', error);
    cb([]);
  }
};

// 商品列表相关
const productListVisible = ref(false);
const productList = ref<Inventory[]>([]);

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
const handleSelect = async (item: any) => {
  currentProduct.value = item;
  form.value.barcode = item.barcode;
  
  // 重置数量，因为可能之前有超过库存的值
  form.value.quantity = '';
  
  // 验证表单
  if (formRef.value) {
    formRef.value.validateField('quantity');
  }
};

// 监听数量输入
const handleQuantityInput = (newValue: string) => {
  if (!newValue) {
    form.value.quantity = '';
    return;
  }

  // 只允许输入数字
  if (!/^\d*$/.test(newValue)) {
    form.value.quantity = newValue.replace(/\D/g, '');
    return;
  }
};

// 处理单价输入
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

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  
  try {
    await formRef.value.validate();
    
    const quantity = parseInt(form.value.quantity);
    if (currentProduct.value && quantity > currentProduct.value.stock) {
      ElMessage.error(`出库数量不能超过当前库存(${currentProduct.value.stock}${currentProduct.value.unit})`);
      return;
    }
    
    await stockOut({
      barcode: form.value.barcode,
      quantity: quantity,
      price: form.value.price
    });
    ElMessage.success('出库成功');

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
    // 表单验证失败的处理
    console.error('表单验证失败:', error);
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

    await cancelTransaction(row.id);
    ElMessage.success('撤销成功');
    // 刷新记录列表和当前商品信息
    loadRecentRecords();
    if (currentProduct.value?.barcode === row.barcode) {
      const response = await searchInventory(row.barcode);
      if (response.length > 0) {
        currentProduct.value = response[0];
      }
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '撤销失败');
    }
  }
};

// 计算属性
const canSubmit = computed(() => {
  return currentProduct.value?.is_active && currentProduct.value?.stock > 0;
});

// 添加 loadRecentRecords 函数
const loadRecentRecords = async () => {
  try {
    const response = await getTransactions({
      type: 'out',  // 只获取出库记录
      limit: 10
    });
    recentRecords.value = response.items;
  } catch (error) {
    console.error('加载出库记录失败:', error);
    ElMessage.error('加载出库记录失败');
  }
};

// 初始化加载
loadRecentRecords();
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

.stock-hint {
  margin-top: 8px;
  color: #909399;
  font-size: 14px;
}

// 其他样式已在 common.scss 中定义
</style>