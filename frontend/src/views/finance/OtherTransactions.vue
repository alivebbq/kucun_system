<template>
  <div class="page-container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-form :inline="true">
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            :shortcuts="dateShortcuts"
            @change="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>新增记录
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 左右布局容器 -->
    <div class="split-container">
      <!-- 支出记录 -->
      <div class="split-panel">
        <div class="panel-header">
          <h3>支出记录</h3>
        </div>
        <el-table :data="expenseTransactions" v-loading="loading" border>
          <el-table-column prop="transaction_date" label="日期" width="120">
            <template #default="{ row }">
              {{ formatDate(row.transaction_date) }}
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="金额" width="120" align="right">
            <template #default="{ row }">
              <span class="expense-amount">¥{{ row.amount }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="notes" label="备注" min-width="150" show-overflow-tooltip />
          <el-table-column prop="operator_name" label="操作人" width="100" />
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="expenseQueryParams.page"
            v-model:page-size="expenseQueryParams.page_size"
            :page-sizes="[10, 20, 50]"
            :total="expenseTotal"
            layout="total, sizes, prev, pager, next"
            @size-change="(size) => handleSizeChange(size, 'expense')"
            @current-change="(page) => handleCurrentChange(page, 'expense')"
          />
        </div>
      </div>

      <!-- 收入记录 -->
      <div class="split-panel">
        <div class="panel-header">
          <h3>收入记录</h3>
        </div>
        <el-table :data="incomeTransactions" v-loading="loading" border>
          <el-table-column prop="transaction_date" label="日期" width="120">
            <template #default="{ row }">
              {{ formatDate(row.transaction_date) }}
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="金额" width="120" align="right">
            <template #default="{ row }">
              <span class="income-amount">¥{{ row.amount }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="notes" label="备注" min-width="150" show-overflow-tooltip />
          <el-table-column prop="operator_name" label="操作人" width="100" />
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="incomeQueryParams.page"
            v-model:page-size="incomeQueryParams.page_size"
            :page-sizes="[10, 20, 50]"
            :total="incomeTotal"
            layout="total, sizes, prev, pager, next"
            @size-change="(size) => handleSizeChange(size, 'income')"
            @current-change="(page) => handleCurrentChange(page, 'income')"
          />
        </div>
      </div>
    </div>

    <!-- 新增对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="新增记录"
      width="500px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="收支类型" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio-button label="expense">支出</el-radio-button>
            <el-radio-button label="income">收入</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="金额" prop="amount">
          <el-input-number
            v-model="form.amount"
            :precision="2"
            :step="0"
            :min="0"
            :controls="false"
            class="form-input"
            placeholder="请输入金额"
          />
        </el-form-item>
        <el-form-item label="日期" prop="transaction_date">
          <el-date-picker
            v-model="form.transaction_date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            class="form-select"
          />
        </el-form-item>
        <el-form-item label="备注" prop="notes">
          <el-input
            v-model="form.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息(选填)"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import { getTransactions, createTransaction, deleteTransaction } from '@/api/finance';
import { formatDateTime, formatDate } from '@/utils/format';
import type { FormInstance } from 'element-plus';
import type { OtherTransaction, TransactionType } from '@/types/finance';

// 查询参数
const incomeQueryParams = ref({
  page: 1,
  page_size: 20,
  type: 'income' as TransactionType
});

const expenseQueryParams = ref({
  page: 1,
  page_size: 20,
  type: 'expense' as TransactionType
});

// 日期快捷选项
const dateShortcuts = [
  {
    text: '最近一周',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    }
  },
  {
    text: '本月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setDate(1)
      return [start, end]
    }
  },
  {
    text: '最近一月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
      return [start, end]
    }
  },
  {
    text: '最近三月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 90)
      return [start, end]
    }
  },
  {
    text: '最近半年',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 180)
      return [start, end]
    }
  },
  {
    text: '最近一年',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 365)
      return [start, end]
    }
  }
]

// 设置默认日期范围为最近30天
const initDefaultDateRange = () => {
  const end = new Date()
  const start = new Date()
  start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
  return [formatDate(start), formatDate(end)]
}

// 修改日期范围的定义，设置默认值
const dateRange = ref<[string, string]>(initDefaultDateRange())

// 数据列表
const incomeTransactions = ref<OtherTransaction[]>([]);
const expenseTransactions = ref<OtherTransaction[]>([]);
const incomeTotal = ref(0);
const expenseTotal = ref(0);
const loading = ref(false);

// 对话框相关
const dialogVisible = ref(false);
const formRef = ref<FormInstance>();
const submitting = ref(false);

// 表单数据
const form = ref({
  type: 'expense' as TransactionType,
  amount: 0,
  transaction_date: formatDate(new Date()),
  notes: ''
});

// 表单校验规则
const rules = {
  type: [
    { required: true, message: '请选择收支类型', trigger: 'change' }
  ],
  amount: [
    { required: true, message: '请输入金额', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '金额必须大于0', trigger: 'blur' }
  ],
  transaction_date: [
    { required: true, message: '请选择日期', trigger: 'change' }
  ]
};

// 计算总金额
const calculateTotal = (type: TransactionType) => {
  const transactions = type === 'income' ? incomeTransactions.value : expenseTransactions.value;
  return transactions.reduce((sum, item) => sum + Number(item.amount), 0).toFixed(2);
};

// 加载数据
const loadData = async (type: TransactionType) => {
  loading.value = true;
  try {
    const params = type === 'income' ? incomeQueryParams.value : expenseQueryParams.value;
    const { items, total } = await getTransactions({
      ...params,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1]
    });
    
    if (type === 'income') {
      incomeTransactions.value = items;
      incomeTotal.value = total;
    } else {
      expenseTransactions.value = items;
      expenseTotal.value = total;
    }
  } catch (error) {
    ElMessage.error('加载数据失败');
  } finally {
    loading.value = false;
  }
};

// 处理搜索
const handleSearch = () => {
  incomeQueryParams.value.page = 1;
  expenseQueryParams.value.page = 1;
  loadData('income');
  loadData('expense');
};

// 处理分页
const handleSizeChange = (size: number, type: TransactionType) => {
  if (type === 'income') {
    incomeQueryParams.value.page_size = size;
    incomeQueryParams.value.page = 1;
    loadData('income');
  } else {
    expenseQueryParams.value.page_size = size;
    expenseQueryParams.value.page = 1;
    loadData('expense');
  }
};

const handleCurrentChange = (page: number, type: TransactionType) => {
  if (type === 'income') {
    incomeQueryParams.value.page = page;
    loadData('income');
  } else {
    expenseQueryParams.value.page = page;
    loadData('expense');
  }
};

// 显示创建对话框
const showCreateDialog = () => {
  dialogVisible.value = true;
};

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields();
  }
  form.value = {
    type: 'expense' as TransactionType,
    amount: 0,
    transaction_date: formatDate(new Date()),
    notes: ''
  };
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true;
      try {
        const data: CreateOtherTransactionRequest = {
          type: form.value.type as TransactionType,
          amount: form.value.amount,
          transaction_date: form.value.transaction_date,
          notes: form.value.notes
        };
        await createTransaction(data);
        ElMessage.success('创建成功');
        dialogVisible.value = false;
        loadData(form.value.type as TransactionType);
      } catch (error) {
        ElMessage.error('创建失败');
      } finally {
        submitting.value = false;
      }
    }
  });
};

// 添加删除方法
const handleDelete = async (row: OtherTransaction) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条记录吗？此操作不可恢复',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    await deleteTransaction(row.id);
    ElMessage.success('删除成功');
    loadData(row.type as TransactionType);
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败');
    }
  }
};

onMounted(() => {
  loadData('income');
  loadData('expense');
});
</script>

<style scoped>
.page-container {
  padding: 20px;
}

.toolbar {
  margin-bottom: 20px;
}

.split-container {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.split-panel {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.panel-header h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.total-amount {
  font-size: 16px;
  font-weight: bold;
}

.total-amount.income {
  color: #67c23a;
}

.total-amount.expense {
  color: #f56c6c;
}

.income-amount {
  color: #67c23a;
  font-weight: bold;
}

.expense-amount {
  color: #f56c6c;
  font-weight: bold;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-input-number) {
  width: 100%;
}

.form-select {
  width: 100%;
}

:deep(.el-input-number .el-input__wrapper) {
  padding-right: 8px;  /* 调整右侧内边距 */
}
</style> 