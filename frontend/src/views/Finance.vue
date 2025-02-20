<template>
  <div class="page-container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button type="primary" @click="handleAddCompany">
          <el-icon><Plus /></el-icon>
          添加公司
        </el-button>
      </div>
    </div>

    <div class="finance-container">
      <!-- 应收账款（客户） -->
      <el-card class="content-card">
        <template #header>
          <div class="card-header">
            <div class="header-left">
              <span>客户应收账款</span>
              <el-text type="info" class="total-amount">
                总应收：<span class="positive">¥{{ formatNumber(totalReceivable) }}</span>
              </el-text>
            </div>
            <div class="search-box">
              <el-input
                v-model="customerSearch"
                placeholder="客户名称/联系人/电话/地址"
                clearable
                @input="handleCustomerSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>
          </div>
        </template>
        <el-table :data="filteredCustomerBalances" v-loading="loading">
          <el-table-column prop="company.name" label="客户名称" min-width="120" />
          <el-table-column prop="company.contact" label="联系人" width="100" />
          <el-table-column prop="company.phone" label="电话" width="120" />
          <el-table-column prop="company.address" label="地址" min-width="200" show-overflow-tooltip />
          <el-table-column prop="receivable" label="应收金额" width="120" align="right">
            <template #default="{ row }">
              <span :class="{ 'positive': row.receivable > 0 }">
                ¥{{ formatNumber(row.receivable) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button-group>
                <el-button 
                  type="primary" 
                  link 
                  @click="handleEdit(row.company)"
                >
                  编辑
                </el-button>
                <el-button 
                  type="primary" 
                  link 
                  @click="handleReceive(row)"
                >
                  收款
                </el-button>
                <el-button 
                  type="primary" 
                  link 
                  @click="handleViewHistory(row)"
                >
                  查看记录
                </el-button>
              </el-button-group>
            </template>
          </el-table-column>
        </el-table>
        <!-- 添加分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="customerQuery.page"
            v-model:page-size="customerQuery.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="customerTotal"
            layout="total, sizes, prev, pager, next"
            @size-change="handleCustomerSizeChange"
            @current-change="handleCustomerPageChange"
          />
        </div>
      </el-card>

      <!-- 应付账款（供应商） -->
      <el-card class="content-card">
        <template #header>
          <div class="card-header">
            <div class="header-left">
              <span>供应商应付账款</span>
              <el-text type="info" class="total-amount">
                总应付：<span class="negative">¥{{ formatNumber(totalPayable) }}</span>
              </el-text>
            </div>
            <div class="search-box">
              <el-input
                v-model="supplierSearch"
                placeholder="供应商名称/联系人/电话/地址"
                clearable
                @input="handleSupplierSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>
          </div>
        </template>
        <el-table :data="filteredSupplierBalances" v-loading="loading">
          <el-table-column prop="company.name" label="供应商名称" min-width="120" />
          <el-table-column prop="company.contact" label="联系人" width="100" />
          <el-table-column prop="company.phone" label="电话" width="120" />
          <el-table-column prop="company.address" label="地址" min-width="200" show-overflow-tooltip />
          <el-table-column prop="payable" label="应付金额" width="120" align="right">
            <template #default="{ row }">
              <span :class="{ 'negative': row.payable > 0 }">
                ¥{{ formatNumber(row.payable) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button-group>
                <el-button 
                  type="primary" 
                  link 
                  @click="handlePay(row)"
                >
                  付款
                </el-button>
                <el-button 
                  type="primary" 
                  link 
                  @click="handleViewHistory(row)"
                >
                  查看记录
                </el-button>
              </el-button-group>
            </template>
          </el-table-column>
        </el-table>
        <!-- 添加分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="supplierQuery.page"
            v-model:page-size="supplierQuery.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="supplierTotal"
            layout="total, sizes, prev, pager, next"
            @size-change="handleSupplierSizeChange"
            @current-change="handleSupplierPageChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 添加公司对话框 -->
    <el-dialog
      v-model="companyDialogVisible"
      title="添加公司"
      width="500px"
    >
      <el-form
        ref="companyFormRef"
        :model="companyForm"
        :rules="companyRules"
        label-width="80px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="companyForm.name" />
        </el-form-item>
        <el-form-item label="公司类型" prop="type">
          <el-select v-model="companyForm.type" class="form-select">
            <el-option
              v-for="option in companyTypeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="联系人" prop="contact">
          <el-input v-model="companyForm.contact" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="companyForm.phone" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="companyForm.address" type="textarea" />
        </el-form-item>
        <el-form-item 
          label="初始应收" 
          prop="initial_receivable"
          v-if="companyForm.type === CompanyType.CUSTOMER"
        >
          <el-input-number 
            v-model="companyForm.initial_receivable"
            :min="0"
            :precision="2"
            :step="100"
          />
        </el-form-item>
        <el-form-item 
          label="初始应付" 
          prop="initial_payable"
          v-if="companyForm.type === CompanyType.SUPPLIER"
        >
          <el-input-number 
            v-model="companyForm.initial_payable"
            :min="0"
            :precision="2"
            :step="100"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="companyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCompany">确定</el-button>
      </template>
    </el-dialog>

    <!-- 收付款对话框 -->
    <el-dialog
      v-model="paymentDialogVisible"
      :title="paymentType === 'receive' ? '收款' : '付款'"
      width="400px"
    >
      <el-form
        ref="paymentFormRef"
        :model="paymentForm"
        :rules="paymentRules"
        label-width="80px"
      >
        <el-form-item label="金额" prop="amount">
          <div class="amount-input">
            <el-input-number 
              v-model="paymentForm.amount"
              :min="-999999999"
              :max="999999999"
              :precision="2"
              :step="100"
              style="width: 100%"
            />
            <div class="amount-tip">
              <el-text type="info" size="small">
                {{ paymentType === 'receive' ? '负数表示退款' : '负数表示退付款' }}
              </el-text>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="备注" prop="notes">
          <el-input 
            v-model="paymentForm.notes"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="paymentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPayment">确定</el-button>
      </template>
    </el-dialog>

    <!-- 交易记录对话框 -->
    <el-dialog
      v-model="historyDialogVisible"
      :title="`${currentCompany?.company.name} 的交易记录`"
      width="900px"
      class="custom-dialog"
    >
      <div class="dialog-toolbar">
        <el-select v-model="historyQuery.type" placeholder="全部类型" clearable>
          <template v-if="currentCompany?.company.type === CompanyType.CUSTOMER">
            <el-option label="出库单" value="stock_out" />
            <el-option label="收款" value="receive" />
          </template>
          <template v-else>
            <el-option label="入库单" value="stock_in" />
            <el-option label="付款" value="pay" />
          </template>
        </el-select>
      </div>
      
      <el-table :data="filteredTransactionHistory" v-loading="historyLoading">
        <el-table-column prop="order_no" label="单据编号" width="180">
          <template #default="{ row }">
            <router-link 
              v-if="row.order_no"
              :to="`/stock-orders/${row.order_id}`"
              class="link-type"
            >
              {{ row.order_no }}
            </router-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTransactionTagType(row)">
              {{ getTransactionTypeText(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="150" align="right">
          <template #default="{ row }">
            <span :class="getAmountClass(row)">
              ¥{{ formatNumber(row.amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作人" width="120" />
        <el-table-column prop="notes" label="备注" min-width="200" show-overflow-tooltip />
      </el-table>

      <!-- 添加分页器 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="historyQuery.page"
          v-model:page-size="historyQuery.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="transactionHistory.length"
          layout="total, sizes, prev, pager, next"
          @size-change="handleHistorySizeChange"
          @current-change="handleHistoryPageChange"
        />
      </div>
    </el-dialog>

    <!-- 编辑公司对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑公司信息"
      width="500px"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="80px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="联系人" prop="contact">
          <el-input v-model="editForm.contact" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="editForm.phone" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="editForm.address" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { ElMessage } from 'element-plus';
import type { FormInstance } from 'element-plus';
import { formatDateTime } from '@/utils/format'
import { debounce } from 'lodash';
import {
  getCompanyBalances,
  createCompany,
  createPayment,
  getCompanyTransactions,
  updateCompany,
  getCompanyTotalBalance
} from '../api/company';
import type { CompanyBalance, CompanyTransaction, Company } from '../types/company';
import { CompanyType } from '../types/company';
import { Search, Plus } from '@element-plus/icons-vue';

const loading = ref(false);
const balances = ref<CompanyBalance[]>([]);
const companyDialogVisible = ref(false);
const paymentDialogVisible = ref(false);
const paymentType = ref<'receive' | 'pay'>('receive');
const currentCompany = ref<CompanyBalance | null>(null);

// 公司表单相关
const companyFormRef = ref<FormInstance>();
const companyForm = ref({
  name: '',
  type: CompanyType.CUSTOMER,
  contact: '',
  phone: '',
  address: '',
  initial_receivable: 0,
  initial_payable: 0
});

// 公司表单规则
const companyRules = {
  name: [
    { required: true, message: '请输入公司名称', trigger: 'blur' },
    { min: 2, message: '公司名称至少2个字符', trigger: 'blur' },
    { max: 50, message: '公司名称不能超过50个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择公司类型', trigger: 'change' }
  ]
};

// 付款表单相关
const paymentFormRef = ref<FormInstance>();
const paymentForm = ref({
  company_id: 0,
  amount: 0,
  type: 'receive',
  notes: ''
});

const paymentRules = {
  amount: [
    { required: true, message: '请输入金额', trigger: 'blur' }
  ]
};

// 公司类型选项
const companyTypeOptions = [
  { label: '客户', value: CompanyType.CUSTOMER },
  { label: '供应商', value: CompanyType.SUPPLIER }
];

// 添加新的响应式变量
const historyDialogVisible = ref(false);
const historyLoading = ref(false);
const transactionHistory = ref<CompanyTransaction[]>([]);

// 修改查询参数，添加分页
const historyQuery = ref({
  type: '',
  page: 1,
  pageSize: 10
});

// 添加总记录数
const historyTotal = ref(0);

// 添加搜索状态
const customerSearch = ref('');
const supplierSearch = ref('');

// 分离客户和供应商余额
const customerBalances = ref<CompanyBalance[]>([]);
const supplierBalances = ref<CompanyBalance[]>([]);

// 修改计算属性，添加搜索过滤
const filteredCustomerBalances = computed(() => {
  const searchText = customerSearch.value.toLowerCase().trim();
  return customerBalances.value.filter(b => {
    if (!searchText) return true;
    return (
      b.company.name.toLowerCase().includes(searchText) ||
      (b.company.contact && b.company.contact.toLowerCase().includes(searchText)) ||
      (b.company.phone && b.company.phone.includes(searchText))
    );
  });
});

const filteredSupplierBalances = computed(() => {
  const searchText = supplierSearch.value.toLowerCase().trim();
  return supplierBalances.value.filter(b => {
    if (!searchText) return true;
    return (
      b.company.name.toLowerCase().includes(searchText) ||
      (b.company.contact && b.company.contact.toLowerCase().includes(searchText)) ||
      (b.company.phone && b.company.phone.includes(searchText))
    );
  });
});

// 添加查询参数
const customerQuery = ref({
  page: 1,
  pageSize: 10,
  type: CompanyType.CUSTOMER
});

const supplierQuery = ref({
  page: 1,
  pageSize: 10,
  type: CompanyType.SUPPLIER
});

// 添加总记录数
const customerTotal = ref(0);
const supplierTotal = ref(0);

// 总金额
const totalReceivable = ref(0);
const totalPayable = ref(0);

// 加载数据
const loadData = async () => {
  loading.value = true;
  try {
    // 加载客户数据
    const customerResponse = await getCompanyBalances({
      type: CompanyType.CUSTOMER,
      skip: (customerQuery.value.page - 1) * customerQuery.value.pageSize,
      limit: customerQuery.value.pageSize,
      search: customerSearch.value || undefined  // 添加搜索参数
    });
    customerBalances.value = customerResponse.items;
    customerTotal.value = customerResponse.total;

    // 加载供应商数据
    const supplierResponse = await getCompanyBalances({
      type: CompanyType.SUPPLIER,
      skip: (supplierQuery.value.page - 1) * supplierQuery.value.pageSize,
      limit: supplierQuery.value.pageSize,
      search: supplierSearch.value || undefined  // 添加搜索参数
    });
    supplierBalances.value = supplierResponse.items;
    supplierTotal.value = supplierResponse.total;

    // 加载总金额
    const customerTotalResponse = await getCompanyTotalBalance(CompanyType.CUSTOMER);
    totalReceivable.value = Number(customerTotalResponse.total_receivable);
    
    const supplierTotalResponse = await getCompanyTotalBalance(CompanyType.SUPPLIER);
    totalPayable.value = Number(supplierTotalResponse.total_payable);
  } catch (error) {
    ElMessage.error('加载数据失败');
  } finally {
    loading.value = false;
  }
};

// 处理分页变化
const handleCustomerSizeChange = (val: number) => {
  customerQuery.value.pageSize = val;
  customerQuery.value.page = 1;
  loadData();
};

const handleCustomerPageChange = (val: number) => {
  customerQuery.value.page = val;
  loadData();
};

const handleSupplierSizeChange = (val: number) => {
  supplierQuery.value.pageSize = val;
  supplierQuery.value.page = 1;
  loadData();
};

const handleSupplierPageChange = (val: number) => {
  supplierQuery.value.page = val;
  loadData();
};

// 格式化数字
const formatNumber = (num: number) => {
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
};

// 处理收款
const handleReceive = (row: CompanyBalance) => {
  currentCompany.value = row;
  paymentType.value = 'receive';
  paymentForm.value = {
    company_id: row.company.id,
    amount: 0,
    type: 'receive',
    notes: ''
  };
  paymentDialogVisible.value = true;
};

// 处理付款
const handlePay = (row: CompanyBalance) => {
  currentCompany.value = row;
  paymentType.value = 'pay';
  paymentForm.value = {
    company_id: row.company.id,
    amount: 0,
    type: 'pay',
    notes: ''
  };
  paymentDialogVisible.value = true;
};

// 提交收付款
const submitPayment = async () => {
  if (!paymentFormRef.value) return;
  
  try {
    await paymentFormRef.value.validate();
    await createPayment(paymentForm.value);
    ElMessage.success('操作成功');
    paymentDialogVisible.value = false;
    loadData();
  } catch (error) {
    console.error('操作失败:', error);
    ElMessage.error('操作失败');
  }
};

// 处理添加公司
const handleAddCompany = () => {
  companyForm.value = {
    name: '',
    type: CompanyType.CUSTOMER,
    contact: '',
    phone: '',
    address: '',
    initial_receivable: 0,
    initial_payable: 0
  };
  companyDialogVisible.value = true;
};

// 修改提交新公司的处理函数
const submitCompany = async () => {
  if (!companyFormRef.value) return;
  
  try {
    await companyFormRef.value.validate();
    const newCompany = await createCompany(companyForm.value);
    ElMessage.success('添加成功');
    companyDialogVisible.value = false;
    loadData(); // 直接重新加载数据，而不是手动添加到列表中
  } catch (error: any) {
    console.error('添加失败:', error);
    if (error.response?.detail === '公司名称已存在') {
      ElMessage.error('公司名称已存在');
    } else {
      ElMessage.error('添加失败');
    }
  }
};

// 格式化日期
const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 获取交易类型文本
const getTransactionTypeText = (row: CompanyTransaction) => {
  const typeMap = {
    stock_in: '入库单',
    stock_out: '出库单',
    receive: '收款',
    pay: '付款'
  };
  return typeMap[row.type] || row.type;
};

// 获取交易类型标签样式
const getTransactionTagType = (row: CompanyTransaction) => {
  const typeMap = {
    stock_in: 'success',
    stock_out: 'warning',
    receive: 'success',
    pay: 'danger'
  } as const;
  return typeMap[row.type] || 'info';
};

// 获取金额样式
const getAmountClass = (row: CompanyTransaction) => {
  const amount = Number(row.amount);
  if (amount === 0) return '';
  if (row.type === 'stock_out' || row.type === 'pay') {
    return amount > 0 ? 'negative' : 'positive';
  }
  if (row.type === 'stock_in' || row.type === 'receive') {
    return amount > 0 ? 'positive' : 'negative';
  }
  return '';
};

// 添加金额显示的提示信息
const getAmountTooltip = (row: CompanyTransaction) => {
  const amount = Number(row.amount);
  if (amount === 0) return '';
  
  if (row.type === 'receive') {
    return amount > 0 ? '收款' : '退款';
  }
  if (row.type === 'pay') {
    return amount > 0 ? '付款' : '退款';
  }
  return '';
};

// 加载交易记录
const loadHistory = async () => {
  if (!currentCompany.value) return;
  
  historyLoading.value = true;
  try {
    const response = await getCompanyTransactions(
      currentCompany.value.company.id
    );
    // 直接使用返回的数组，因为后端已经不再包装在 items 中
    transactionHistory.value = response;
  } catch (error) {
    console.error('加载交易记录失败:', error);
    ElMessage.error('加载交易记录失败');
  } finally {
    historyLoading.value = false;
  }
};

// 添加计算属性进行前端分页
const filteredTransactionHistory = computed(() => {
  let result = [...transactionHistory.value];
  
  // 按类型筛选
  if (historyQuery.value.type) {
    result = result.filter(item => item.type === historyQuery.value.type);
  }
  
  // 分页
  const start = (historyQuery.value.page - 1) * historyQuery.value.pageSize;
  const end = start + historyQuery.value.pageSize;
  return result.slice(start, end);
});

// 处理分页变化
const handleHistorySizeChange = (val: number) => {
  historyQuery.value.pageSize = val;
  historyQuery.value.page = 1;
};

const handleHistoryPageChange = (val: number) => {
  historyQuery.value.page = val;
};

// 修改查看记录函数
const handleViewHistory = async (row: CompanyBalance) => {
  currentCompany.value = row;
  historyDialogVisible.value = true;
  // 重置查询条件
  historyQuery.value = {
    type: '',
    page: 1,
    pageSize: 10
  };
  await loadHistory();
};

// 编辑相关
const editDialogVisible = ref(false);
const editFormRef = ref<FormInstance>();
const editForm = ref({
  id: 0,
  name: '',
  contact: '',
  phone: '',
  address: ''
});

// 编辑表单验证规则
const editRules = {
  name: [
    { required: true, message: '请输入公司名称', trigger: 'blur' },
    { min: 2, message: '公司名称至少2个字符', trigger: 'blur' },
    { max: 50, message: '公司名称不能超过50个字符', trigger: 'blur' }
  ]
};

// 处理编辑按钮点击
const handleEdit = (company: Company) => {
  editForm.value = {
    id: company.id,
    name: company.name,
    contact: company.contact || '',
    phone: company.phone || '',
    address: company.address || ''
  };
  editDialogVisible.value = true;
};

// 提交编辑
const submitEdit = async () => {
  if (!editFormRef.value) return;
  
  try {
    await editFormRef.value.validate();
    await updateCompany(editForm.value.id, {
      name: editForm.value.name,
      contact: editForm.value.contact,
      phone: editForm.value.phone,
      address: editForm.value.address
    });
    ElMessage.success('修改成功');
    editDialogVisible.value = false;
    loadData(); // 重新加载数据
  } catch (error: any) {
    console.error('修改失败:', error);
    if (error.response?.detail === '公司名称已存在') {
      ElMessage.error('公司名称已存在');
    } else {
      ElMessage.error('修改失败');
    }
  }
};

// 修改搜索处理函数
const handleCustomerSearch = debounce(async () => {
  customerQuery.value.page = 1; // 重置页码
  await loadData();
}, 300);

const handleSupplierSearch = debounce(async () => {
  supplierQuery.value.page = 1; // 重置页码
  await loadData();
}, 300);

onMounted(() => {
  loadData();
});
</script>

<style lang="scss" scoped>
.finance-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 20px;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 16px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .total-amount {
    font-size: 14px;
    font-weight: normal;
  }

  .search-box {
    width: 200px;
  }
}

.custom-dialog {
  :deep(.el-dialog__body) {
    padding: 20px;
  }
}

.dialog-toolbar {
  margin-bottom: 16px;
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.amount-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  
  .amount-info {
    font-size: 12px;
    color: #909399;
  }
}

.amount-input {
  .amount-tip {
    margin-top: 4px;
    font-size: 12px;
  }
}
</style> 