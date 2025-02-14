<template>
  <div class="stock-in">
    <el-card class="stock-in-form">
      <template #header>
        <div class="card-header">
          <span>商品入库</span>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="form">
        <el-form-item label="商品搜索" prop="barcode">
          <div class="search-with-button">
            <el-autocomplete
              v-model="form.barcode"
              :fetch-suggestions="querySearch"
              placeholder="请输入商品条形码或名称"
              :trigger-on-focus="false"
              @select="handleSelect"
              @keyup.enter="handleSearch"
              class="search-input"
            >
              <template #default="{ item }">
                <div class="search-item">
                  <div class="name">{{ item.name }}</div>
                  <div class="info">
                    <span>条码: {{ item.barcode }}</span>
                    <span>库存: {{ item.stock }}{{ item.unit }}</span>
                  </div>
                </div>
              </template>
            </el-autocomplete>
            <el-button @click="showProductList">
              <el-icon><List /></el-icon>
              从列表选择
            </el-button>
          </div>
        </el-form-item>

        <div v-if="currentProduct" class="product-info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="商品名称">
              {{ currentProduct.name }}
            </el-descriptions-item>
            <el-descriptions-item label="单位">
              {{ currentProduct.unit }}
            </el-descriptions-item>
            <el-descriptions-item label="当前库存">
              {{ currentProduct.stock }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <el-form-item label="入库数量" prop="quantity" v-if="currentProduct">
          <el-input v-model="form.quantity" placeholder="请输入入库数量" type="number" @input="handleQuantityInput" :disabled="!currentProduct.is_active" />
        </el-form-item>

        <el-form-item label="进货单价" prop="price" v-if="currentProduct">
          <el-input v-model="form.price" placeholder="请输入进货单价" type="number" @input="handlePriceInput" :disabled="!currentProduct.is_active" />
        </el-form-item>

        <el-form-item v-if="currentProduct">
          <el-button type="primary" :loading="loading" @click="handleSubmit" :disabled="!currentProduct.is_active">
            确认入库
          </el-button>
          <span v-if="!currentProduct.is_active" class="disabled-tip">
            该商品已禁用，无法入库
          </span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 最近入库记录 -->
    <el-card class="recent-records">
      <template #header>
        <div class="card-header">
          <span>最近入库记录</span>
        </div>
      </template>

      <el-table :data="recentRecords" style="width: 100%">
        <el-table-column prop="barcode" label="条形码" width="150" />
        <el-table-column prop="name" label="商品名称" />
        <el-table-column prop="quantity" label="数量" width="100" align="right" />
        <el-table-column prop="price" label="单价" width="120" align="right">
          <template #default="{ row }">
            ¥{{ formatNumber(row.price) }}
          </template>
        </el-table-column>
        <el-table-column prop="total" label="总金额" width="120" align="right">
          <template #default="{ row }">
            ¥{{ formatNumber(row.total) }}
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
    >
      <el-table
        :data="productList"
        style="width: 100%"
        height="500px"
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
    { required: true, message: '请输入入库数量', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        const num = parseInt(value);
        if (isNaN(num) || num <= 0 || !Number.isInteger(num)) {
          callback(new Error('请输入大于0的整数'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ],
  price: [
    { required: true, message: '请输入进货单价', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        const num = parseFloat(value);
        if (isNaN(num) || num <= 0) {
          callback(new Error('请输入大于0的数字'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ]
};

// 商品列表相关
const productListVisible = ref(false);
const productList = ref<Inventory[]>([]);

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
const querySearch = async (queryString: string, cb: (arg: any[]) => void) => {
  if (!queryString) {
    cb([]);
    return;
  }

  try {
    const response = await searchInventory(queryString);
    cb(response);
  } catch (error) {
    console.error('搜索商品失败:', error);
    cb([]);
  }
};

// 选择商品
const handleSelect = (item: Inventory) => {
  currentProduct.value = item;
  form.value.barcode = item.barcode;
};

// 处理搜索
const handleSearch = async () => {
  if (!form.value.barcode) {
    ElMessage.warning('请输入商品条形码或名称');
    return;
  }

  try {
    const response = await searchInventory(form.value.barcode);
    if (response.length === 0) {
      ElMessage.warning('未找到商品');
      currentProduct.value = null;
    } else if (response.length === 1) {
      currentProduct.value = response[0];
      form.value.barcode = response[0].barcode;
    } else {
      // 如果有多个结果，显示选择对话框
      ElMessageBox.select({
        title: '请选择商品',
        message: '找到多个匹配的商品，请选择：',
        options: response.map(item => ({
          label: `${item.name} (${item.barcode})`,
          value: item
        })),
        cancelButtonText: '取消',
        confirmButtonText: '确定'
      }).then(selected => {
        if (selected) {
          currentProduct.value = selected;
          form.value.barcode = selected.barcode;
        }
      }).catch(() => {
        // 用户取消选择
      });
    }
  } catch (error) {
    console.error('搜索商品失败:', error);
    ElMessage.error('搜索商品失败');
    currentProduct.value = null;
  }
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
  // 移除非数字字符
  const cleanValue = value.replace(/[^\d]/g, '');
  // 允许为空，否则确保是正整数
  form.value.quantity = cleanValue === '' ? '' : parseInt(cleanValue) || '';
};

// 处理单价输入
const handlePriceInput = (value: string) => {
  // 移除非数字和小数点以外的字符
  let cleanValue = value.replace(/[^\d.]/g, '');
  // 确保只有一个小数点
  const parts = cleanValue.split('.');
  if (parts.length > 2) {
    cleanValue = parts[0] + '.' + parts.slice(1).join('');
  }
  // 限制小数位数为2位
  if (parts.length === 2 && parts[1].length > 2) {
    cleanValue = parts[0] + '.' + parts[1].slice(0, 2);
  }
  // 确保是正数
  const num = parseFloat(cleanValue);
  form.value.price = num > 0 ? num : 0;
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

// 搜索商品信息
const searchProduct = async (barcode: string) => {
  try {
    const response = await getInventoryByBarcode(barcode);
    currentProduct.value = response;
    return response;
  } catch (error) {
    console.error('获取商品信息失败:', error);
    ElMessage.error('获取商品信息失败');
    return null;
  }
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
      await searchProduct(row.barcode);
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

<style scoped>
.stock-in {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
  box-sizing: border-box;
}

.stock-in-form {
  width: 100%;
}

.form {
  max-width: 500px;
  /* 限制表单宽度，使其不会太宽 */
  padding: 20px 0;
}

.product-info {
  margin: 15px 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-input) {
  width: 100%;
}

/* 隐藏number类型输入框的上下箭头 */
:deep(.el-input__inner[type="number"]) {
  -moz-appearance: textfield;
}

:deep(.el-input__inner[type="number"]::-webkit-outer-spin-button),
:deep(.el-input__inner[type="number"]::-webkit-inner-spin-button) {
  -webkit-appearance: none;
  margin: 0;
}

:deep(.el-descriptions) {
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

:deep(.el-form-item) {
  margin-bottom: 15px;
}

:deep(.el-descriptions__title) {
  font-size: 16px;
}

.recent-records {
  flex: 1;
  overflow: auto;
  /* 允许表格内容滚动 */
  min-height: 300px;
  /* 设置最小高度 */
}

.disabled-tip {
  margin-left: 10px;
  color: #f56c6c;
  font-size: 14px;
}

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
  width: 100%;
}

.search-with-button {
  display: flex;
  gap: 10px;
}

.search-with-button .el-autocomplete {
  flex: 1;
}

:deep(.el-dialog__body) {
  padding: 10px 20px;
}
</style>