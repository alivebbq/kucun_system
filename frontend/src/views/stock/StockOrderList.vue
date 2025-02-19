<template>
  <div class="page-container">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button type="primary" @click="createOrder('in')">
          <el-icon><Plus /></el-icon>新建入库单
        </el-button>
        <el-button type="primary" @click="createOrder('out')">
          <el-icon><Plus /></el-icon>新建出库单
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-form :inline="true" class="search-form">
          <el-form-item>
            <el-input
              v-model="searchQuery"
              placeholder="输入单号或供应商/客户名称"
              clearable
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item>
            <el-select v-model="filterType" placeholder="单据类型" clearable>
              <el-option label="入库单" value="in" />
              <el-option label="出库单" value="out" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-select v-model="filterStatus" placeholder="单据状态" clearable>
              <el-option label="草稿" value="draft" />
              <el-option label="已确认" value="confirmed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-table
      v-loading="loading"
      :data="orders"
      border
      style="width: 100%"
    >
      <el-table-column prop="order_no" label="单据编号" width="180">
        <template #default="{ row }">
          <router-link 
            :to="`/stock-orders/${row.id}`"
            class="link-type"
          >
            {{ row.order_no }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column prop="type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.type === 'in' ? 'success' : 'warning'">
            {{ row.type === 'in' ? '入库' : '出库' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="company_name" label="供应商/客户" width="180">
        <template #default="{ row }">
          {{ row.company_name || '未知' }}
        </template>
      </el-table-column>
      <el-table-column 
        prop="total_amount" 
        label="总金额" 
        align="right">
        <template #default="{ row }">
          ¥{{ row.total_amount }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="operator_name" label="操作人" width="120">
        <template #default="{ row }">
          {{ row.operator_name || '未知' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'draft'"
            type="primary"
            size="small"
            @click="handleConfirm(row)"
          >
            确认
          </el-button>
          <el-button
            v-if="row.status === 'draft'"
            type="danger"
            size="small"
            @click="handleCancel(row)"
          >
            取消
          </el-button>
          <el-button
            size="small"
            @click="handleView(row)"
          >
            查看
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/format'
import type { StockOrder } from '@/types/inventory'
import { 
    getStockOrders, 
    confirmStockOrder, 
    cancelStockOrder 
} from '@/api/stockOrder'

const router = useRouter()
const loading = ref(false)
const orders = ref<StockOrder[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const filterType = ref('')
const filterStatus = ref('')

// 获取订单列表
const loadOrders = async () => {
  loading.value = true
  try {
    const response = await getStockOrders({
      page: currentPage.value,
      limit: pageSize.value,
      search: searchQuery.value,
      type: filterType.value,
      status: filterStatus.value
    })
    orders.value = response.items
    total.value = response.total
  } catch (error) {
    ElMessage.error('加载订单列表失败')
  } finally {
    loading.value = false
  }
}

// 状态相关
const getStatusType = (status: string) => {
  const types = {
    draft: '',
    confirmed: 'success',
    cancelled: 'danger'
  }
  return types[status] || ''
}

const getStatusText = (status: string) => {
  const texts = {
    draft: '草稿',
    confirmed: '已确认',
    cancelled: '已取消'
  }
  return texts[status] || status
}

// 操作处理
const createOrder = (type: 'in' | 'out') => {
  router.push({
    path: '/stock-orders/create',
    query: { type }
  })
}

const handleView = (row: StockOrder) => {
  router.push(`/stock-orders/${row.id}`)
}

const handleConfirm = async (row: StockOrder) => {
  try {
    await ElMessageBox.confirm('确认此出入库单？确认后将无法修改', '提示', {
      type: 'warning'
    })
    await confirmStockOrder(row.id)
    ElMessage.success('确认成功')
    loadOrders()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('确认失败')
    }
  }
}

const handleCancel = async (row: StockOrder) => {
  try {
    await ElMessageBox.confirm('确定要取消此出入库单吗？', '提示', {
      type: 'warning'
    })
    await cancelStockOrder(row.id)
    ElMessage.success('取消成功')
    loadOrders()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消失败')
    }
  }
}

// 搜索和分页
const handleSearch = () => {
  currentPage.value = 1
  loadOrders()
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  loadOrders()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  loadOrders()
}

// 监听筛选条件变化
watch([filterType, filterStatus], () => {
  currentPage.value = 1
  loadOrders()
})

onMounted(() => {
  loadOrders()
})
</script>

<style scoped lang="scss">
.link-type {
  color: #409eff;
  text-decoration: none;
  
  &:hover {
    text-decoration: underline;
  }
}

// 其他样式已在 common.scss 中定义
</style> 