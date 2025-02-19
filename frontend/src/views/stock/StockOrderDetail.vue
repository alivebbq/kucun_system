<template>
  <div class="page-container">
    <div v-loading="loading" class="detail-container">
      <!-- 头部信息 -->
      <div class="detail-header">
        <div class="header-left">
          <h2>{{ order?.type === 'in' ? '入库单' : '出库单' }}</h2>
          <el-tag 
            :type="getStatusType(order?.status)"
            class="status-tag"
          >
            {{ getStatusText(order?.status) }}
          </el-tag>
        </div>
        <div class="header-right">
          <el-button @click="$router.back()">返回</el-button>
          <template v-if="order?.status === 'draft'">
            <el-button 
              type="primary"
              @click="handleConfirm"
            >
              确认
            </el-button>
            <el-button 
              type="danger"
              @click="handleCancel"
            >
              取消
            </el-button>
          </template>
        </div>
      </div>

      <!-- 基本信息 -->
      <el-descriptions 
        title="基本信息" 
        :column="3" 
        border
      >
        <el-descriptions-item label="单据编号">
          {{ order?.order_no }}
        </el-descriptions-item>
        <el-descriptions-item :label="order?.type === 'in' ? '供应商' : '客户'">
          {{ order?.company_name }}
        </el-descriptions-item>
        <el-descriptions-item label="总金额">
          ¥{{ order?.total_amount.toFixed(2) }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDateTime(order?.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="操作人">
          {{ order?.operator_name }}
        </el-descriptions-item>
        <el-descriptions-item label="备注">
          {{ order?.notes || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 商品明细 -->
      <div class="items-container">
        <h3>商品明细</h3>
        <el-table :data="order?.items" border>
          <el-table-column prop="barcode" label="条形码" width="150" />
          <el-table-column label="商品名称" width="200">
            <template #default="{ row }">
              {{ getInventoryName(row.inventory_id) }}
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="120" />
          <el-table-column prop="price" label="单价" width="120">
            <template #default="{ row }">
              ¥{{ row.price.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="金额" width="120">
            <template #default="{ row }">
              ¥{{ (row.quantity * row.price).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="notes" label="备注" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDateTime } from '@/utils/format'
import type { StockOrder } from '@/types/inventory'
import { getStockOrder, confirmStockOrder, cancelStockOrder } from '@/api/stockOrder'
import { getInventory } from '@/api/inventory'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const order = ref<StockOrder>()
const inventoryCache = new Map()

// 获取订单详情
const loadOrder = async () => {
  loading.value = true
  try {
    const response = await getStockOrder(Number(route.params.id))
    order.value = response
    // 预加载商品信息
    await Promise.all(
      response.items.map(item => loadInventory(item.inventory_id))
    )
  } catch (error) {
    ElMessage.error('加载订单详情失败')
  } finally {
    loading.value = false
  }
}

// 加载商品信息
const loadInventory = async (id: number) => {
  if (inventoryCache.has(id)) return
  try {
    const response = await getInventory(id)
    inventoryCache.set(id, response)
  } catch (error) {
    console.error('加载商品信息失败:', error)
  }
}

// 获取商品名称
const getInventoryName = (id: number) => {
  return inventoryCache.get(id)?.name || '-'
}

// 状态相关
const getStatusType = (status?: string) => {
  const types = {
    draft: '',
    confirmed: 'success',
    cancelled: 'danger'
  }
  return types[status as keyof typeof types] || ''
}

const getStatusText = (status?: string) => {
  const texts = {
    draft: '草稿',
    confirmed: '已确认',
    cancelled: '已取消'
  }
  return texts[status as keyof typeof texts] || status
}

// 确认订单
const handleConfirm = async () => {
  try {
    await ElMessageBox.confirm('确认此出入库单？确认后将无法修改', '提示', {
      type: 'warning'
    })
    await confirmStockOrder(Number(route.params.id))
    ElMessage.success('确认成功')
    loadOrder()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('确认失败')
    }
  }
}

// 取消订单
const handleCancel = async () => {
  try {
    await ElMessageBox.confirm('确定要取消此出入库单吗？', '提示', {
      type: 'warning'
    })
    await cancelStockOrder(Number(route.params.id))
    ElMessage.success('取消成功')
    loadOrder()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消失败')
    }
  }
}

onMounted(() => {
  loadOrder()
})
</script>

<style scoped lang="scss">
.detail-container {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  
  .header-left {
    display: flex;
    align-items: center;
    
    h2 {
      margin: 0;
      margin-right: 15px;
      font-size: 20px;
    }
    
    .status-tag {
      margin-left: 10px;
    }
  }
}

.items-container {
  margin-top: 30px;
  
  h3 {
    margin-bottom: 20px;
    font-size: 16px;
  }
}

:deep(.el-descriptions) {
  margin-top: 20px;
}
</style> 