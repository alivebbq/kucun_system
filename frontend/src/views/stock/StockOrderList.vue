<template>
  <div class="page-container">
    <!-- 添加待办单据统计 -->
    <div class="draft-count" v-if="draftCount > 0">
      <el-alert
        :title="`您有 ${draftCount} 个待处理的出入库单据`"
        type="info"
        show-icon
        :closable="false"
      />
    </div>

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
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              :shortcuts="dateShortcuts"
              value-format="YYYY-MM-DD"
              @change="handleSearch"
            />
          </el-form-item>
          <el-form-item>
            <el-input
              v-model="searchQuery"
              placeholder="输入单号或供应商/客户名称"
              clearable
              style="width: 220px;"
              @input="handleSearch"
              @clear="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item>
            <el-select 
              v-model="filterType" 
              placeholder="单据类型" 
              clearable
              style="width: 120px;"
            >
              <el-option label="入库单" value="in" />
              <el-option label="出库单" value="out" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-select 
              v-model="filterStatus" 
              placeholder="单据状态" 
              clearable
              style="width: 120px;"
            >
              <el-option label="待处理" value="draft" />
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
      <el-table-column prop="company_name" label="供应商/客户" width="180" />
      <el-table-column 
        prop="total_amount" 
        label="总金额" 
        width="120"
        align="right"
      >
        <template #default="{ row }">
          ¥{{ row.total_amount }}
        </template>
      </el-table-column>
      <el-table-column 
        prop="notes" 
        label="备注" 
        min-width="120"
        show-overflow-tooltip
      >
        <template #default="{ row }">
          {{ row.notes || '-' }}
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
      <el-table-column prop="operator_name" label="操作人" width="120" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <div class="operation-buttons">
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
          </div>
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
const draftCount = ref(0)


// 添加日期范围
const dateRange = ref<[string, string] | null>(null);

// 修改日期快捷选项
const dateShortcuts = [
  {
    text: '最近一周',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    },
  },
  {
    text: '本月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setDate(1) // 设置为本月第一天
      return [start, end]
    },
  },
  {
    text: '最近一月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
      return [start, end]
    },
  },
  {
    text: '最近三月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 90)
      return [start, end]
    },
  },
  {
    text: '最近半年',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 180)
      return [start, end]
    },
  },
  {
    text: '最近一年',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 365)
      return [start, end]
    },
  }
]

// 使用防抖函数优化搜索
const debounce = (fn: Function, delay: number) => {
  let timer: NodeJS.Timeout | null = null
  return (...args: any[]) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(null, args)
    }, delay)
  }
}

// 处理搜索
const handleSearch = debounce(() => {
  currentPage.value = 1  // 重置页码
  loadOrders()
}, 300)  // 300ms 的防抖延迟

// 获取订单列表
const loadOrders = async () => {
  loading.value = true
  try {
    const [ordersResponse, draftResponse] = await Promise.all([
      getStockOrders({
        page: currentPage.value,
        page_size: pageSize.value,
        type: filterType.value || undefined,
        status: filterStatus.value || undefined,
        keyword: searchQuery.value || undefined,
        start_date: dateRange.value ? dateRange.value[0] : undefined,
        end_date: dateRange.value ? dateRange.value[1] : undefined        
      }),
      // 单独获取待处理状态的单据数量
      getStockOrders({
        status: 'draft',
        page_size: 1  // 只需要总数，所以设置最小的页大小
      })
    ])
    
    orders.value = ordersResponse.items
    total.value = ordersResponse.total
    draftCount.value = draftResponse.total
  } catch (error) {
    ElMessage.error('加载订单列表失败')
  } finally {
    loading.value = false
  }
}

// 状态相关
const getStatusType = (status: 'draft' | 'confirmed' | 'cancelled') => {
  const types: Record<'draft' | 'confirmed' | 'cancelled', string> = {
    draft: '',
    confirmed: 'success',
    cancelled: 'danger'
  }
  return types[status] || ''
}

const getStatusText = (status: 'draft' | 'confirmed' | 'cancelled') => {
  const texts: Record<'draft' | 'confirmed' | 'cancelled', string> = {
    draft: '待处理',
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
  } catch (error: any) {
    if (error !== 'cancel') {
      // 显示具体的错误信息
      const errorMsg = error.response?.data?.detail || '确认失败'
      ElMessage.error(errorMsg)
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

.toolbar-right {
  .el-select {
    margin-right: 10px;
  }
  
  .el-input {
    margin-right: 10px;
  }
}

.search-form {
  display: flex;
  align-items: center;
  
  .el-form-item {
    margin-bottom: 0;
    margin-right: 10px;
    
    &:last-child {
      margin-right: 0;
    }
  }
}

// 其他样式已在 common.scss 中定义

/* 调整操作列按钮间距 */
.el-button {
  margin-right: 5px;
  &:last-child {
    margin-right: 0;
  }
}

.operation-buttons {
  display: flex;
  gap: 5px;  // 按钮之间的间距
  flex-wrap: nowrap;  // 防止按钮换行
  
  .el-button {
    margin-right: 0;  // 覆盖默认的按钮右边距
  }
}

.draft-count {
  margin-bottom: 16px;
  
  :deep(.el-alert) {
    border-radius: 4px;
  }
}

.search-form :deep(.el-date-editor) {
  width: 320px;
}
</style> 