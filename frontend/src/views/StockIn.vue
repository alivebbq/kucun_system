<template>
  <div class="stock-in">
    <el-card class="stock-in-form">
      <template #header>
        <div class="card-header">
          <span>商品入库</span>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="form">
        <el-form-item label="条形码" prop="barcode">
          <el-input v-model="form.barcode" placeholder="请扫描或输入商品条形码" @keyup.enter="handleSearch">
            <template #append>
              <el-button @click="handleSearch">
                <el-icon>
                  <Search />
                </el-icon>
              </el-button>
            </template>
          </el-input>
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
        <el-table-column prop="timestamp" label="入库时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.timestamp) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Search } from '@element-plus/icons-vue';
import type { FormInstance, FormRules } from 'element-plus';
import {
  getInventoryByBarcode,
  stockIn,
  getTransactions,
  type Inventory,
  type Transaction
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

// 搜索商品
const handleSearch = async () => {
  if (!form.value.barcode) {
    ElMessage.warning('请输入条形码');
    return;
  }

  try {
    currentProduct.value = await getInventoryByBarcode(form.value.barcode);
    if (currentProduct.value) {
      // 移除设置默认价格
      // form.value.price = currentProduct.value.avg_purchase_price;
    }
  } catch (error) {
    console.error('查询商品失败:', error);
    ElMessage.error('商品不存在');
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
</style>