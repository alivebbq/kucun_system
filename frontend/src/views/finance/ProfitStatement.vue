<template>
  <div class="page-container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-form :inline="true">
        <el-form-item label="统计时段">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            :shortcuts="dateShortcuts"
            @change="loadData"
          />
        </el-form-item>
      </el-form>
    </div>

    <!-- 统计卡片 -->
    <div class="statistics-container" v-loading="loading">
      <!-- 收入统计 -->
      <el-card class="stat-card">
        <template #header>
          <div class="card-header">
            <span>收入统计</span>
          </div>
        </template>
        <div class="stat-item">
          <span class="label">已收货款:</span>
          <span class="value income">¥{{ statistics.received_payments }}</span>
        </div>
        <div class="stat-item">
          <span class="label">其他收入:</span>
          <span class="value income">¥{{ statistics.other_income }}</span>
        </div>
        <div class="stat-item total">
          <span class="label">总收入:</span>
          <span class="value income">¥{{ statistics.total_income }}</span>
        </div>
      </el-card>

      <!-- 支出统计 -->
      <el-card class="stat-card">
        <template #header>
          <div class="card-header">
            <span>支出统计</span>
          </div>
        </template>
        <div class="stat-item">
          <span class="label">已付货款:</span>
          <span class="value expense">¥{{ statistics.paid_payments }}</span>
        </div>
        <div class="stat-item">
          <span class="label">其他支出:</span>
          <span class="value expense">¥{{ statistics.other_expense }}</span>
        </div>
        <div class="stat-item total">
          <span class="label">总支出:</span>
          <span class="value expense">¥{{ statistics.total_expense }}</span>
        </div>
      </el-card>

      <!-- 利润统计 -->
      <el-card class="stat-card">
        <template #header>
          <div class="card-header">
            <span>利润统计</span>
          </div>
        </template>
        <div class="stat-item total">
          <span class="label">利润:</span>
          <span :class="['value', statistics.profit >= 0 ? 'income' : 'expense']">
            ¥{{ statistics.profit }}
          </span>
        </div>
      </el-card>
    </div>

    <!-- 添加明细记录部分 -->
    <div class="details-container">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="已收货款明细" name="received">
          <el-table :data="receivedPayments" v-loading="detailsLoading" border>
            <el-table-column prop="payment_date" label="日期" width="120">
              <template #default="{ row }">
                {{ formatDate(row.payment_date) }}
              </template>
            </el-table-column>
            <el-table-column prop="company_name" label="客户" width="150" />
            <el-table-column prop="amount" label="金额" width="120" align="right">
              <template #default="{ row }">
                <span class="income-amount">¥{{ row.amount }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="notes" label="备注" min-width="150" show-overflow-tooltip />
            <el-table-column prop="operator_name" label="操作人" width="100" />
          </el-table>
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="total.received"
              layout="total, sizes, prev, pager, next"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="其他收入明细" name="other_income">
          <el-table :data="otherIncomes" v-loading="detailsLoading" border>
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
          </el-table>
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="total.other_income"
              layout="total, sizes, prev, pager, next"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="已付货款明细" name="paid">
          <el-table :data="paidPayments" v-loading="detailsLoading" border>
            <el-table-column prop="payment_date" label="日期" width="120">
              <template #default="{ row }">
                {{ formatDate(row.payment_date) }}
              </template>
            </el-table-column>
            <el-table-column prop="company_name" label="供应商" width="150" />
            <el-table-column prop="amount" label="金额" width="120" align="right">
              <template #default="{ row }">
                <span class="expense-amount">¥{{ row.amount }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="notes" label="备注" min-width="150" show-overflow-tooltip />
            <el-table-column prop="operator_name" label="操作人" width="100" />
          </el-table>
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="total.paid"
              layout="total, sizes, prev, pager, next"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="其他支出明细" name="other_expense">
          <el-table :data="otherExpenses" v-loading="detailsLoading" border>
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
          </el-table>
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="total.other_expense"
              layout="total, sizes, prev, pager, next"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { getProfitStatistics, getOtherTransactions, getPaymentRecords } from '@/api/finance';
import type { ProfitStatistics } from '@/types/finance';
import { TransactionType } from '@/types/finance';
import { CompanyType } from '@/types/company';
import { formatDate } from '@/utils/format';
import type { PaymentRecord } from '@/types/finance';

const dateRange = ref<[string, string] | null>(null);
const loading = ref(false);
const statistics = ref<ProfitStatistics>({
  received_payments: 0,
  other_income: 0,
  total_income: 0,
  paid_payments: 0,
  other_expense: 0,
  total_expense: 0,
  profit: 0
});

// 明细相关
const activeTab = ref('received');
const detailsLoading = ref(false);
const receivedPayments = ref<PaymentRecord[]>([]);
const otherIncomes = ref<any[]>([]);
const paidPayments = ref<PaymentRecord[]>([]);
const otherExpenses = ref<any[]>([]);

// 分页相关
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref({
  received: 0,
  other_income: 0,
  paid: 0,
  other_expense: 0
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
      const start = new Date(end.getFullYear(), end.getMonth(), 1)
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

// 处理 Tab 切换
const handleTabChange = async (tab: string) => {
  currentPage.value = 1;
  await loadDetailsData(tab);
};

// 加载明细数据
const loadDetailsData = async (type: string) => {
  if (!dateRange.value) return;

  detailsLoading.value = true;
  try {
    const [start_date, end_date] = dateRange.value;
    const params = { 
      start_date, 
      end_date,
      page: currentPage.value,
      page_size: pageSize.value
    };

    switch (type) {
      case 'received':
        const receivedResponse = await getPaymentRecords({ 
          ...params, 
          company_type: CompanyType.CUSTOMER 
        });
        receivedPayments.value = receivedResponse.items;
        total.value.received = receivedResponse.total;
        break;
      case 'other_income':
        const incomeResponse = await getOtherTransactions({ 
          ...params, 
          type: TransactionType.INCOME 
        });
        otherIncomes.value = incomeResponse.items;
        total.value.other_income = incomeResponse.total;
        break;
      case 'paid':
        const paidResponse = await getPaymentRecords({ 
          ...params, 
          company_type: CompanyType.SUPPLIER 
        });
        paidPayments.value = paidResponse.items;
        total.value.paid = paidResponse.total;
        break;
      case 'other_expense':
        const expenseResponse = await getOtherTransactions({ 
          ...params, 
          type: TransactionType.EXPENSE 
        });
        otherExpenses.value = expenseResponse.items;
        total.value.other_expense = expenseResponse.total;
        break;
    }
  } catch (error) {
    ElMessage.error('加载明细数据失败');
  } finally {
    detailsLoading.value = false;
  }
};

// 处理页码改变
const handlePageChange = async (page: number) => {
  currentPage.value = page;
  await loadDetailsData(activeTab.value);
};

// 处理每页条数改变
const handleSizeChange = async (size: number) => {
  pageSize.value = size;
  currentPage.value = 1; // 重置到第一页
  await loadDetailsData(activeTab.value);
};

// 修改 loadData 方法
const loadData = async () => {
  if (!dateRange.value) {
    ElMessage.warning('请选择统计时段');
    return;
  }

  loading.value = true;
  try {
    const [start_date, end_date] = dateRange.value;
    const response = await getProfitStatistics({ start_date, end_date });
    statistics.value = response;
    
    await loadDetailsData(activeTab.value);
  } catch (error) {
    ElMessage.error('加载数据失败');
  } finally {
    loading.value = false;
  }
};

// 设置默认时间范围为最近30天
onMounted(() => {
  const start = new Date();
  start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);  // 30天前
  const end = new Date();
  
  dateRange.value = [
    start.toISOString().split('T')[0],
    end.toISOString().split('T')[0]
  ];
  
  loadData();
});
</script>

<style scoped>
.statistics-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 20px;
}

.stat-card {
  min-height: 200px;
}

.card-header {
  font-size: 16px;
  font-weight: bold;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  font-size: 14px;
}

.stat-item.total {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #eee;
  font-weight: bold;
  font-size: 16px;
}

.value {
  font-family: monospace;
}

.value.income {
  color: #67c23a;
}

.value.expense {
  color: #f56c6c;
}

.details-container {
  margin-top: 30px;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style> 