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
          <!-- 普通操作按钮组 -->
          <div class="button-group">
            <el-button 
              type="info"
              plain
              @click="handlePrint"
            >
              <el-icon><Printer /></el-icon>
              打印单据
            </el-button>
            <el-button 
              type="primary"
              @click="router.push('/stock-orders')"
            >
              返回列表
            </el-button>
          </div>
        </div>
      </div>

      <!-- 基本信息 -->
      <el-form 
        v-if="order?.status === 'draft' && isEditing"
        :model="editForm"
        label-width="100px"
      >
        <el-form-item :label="order?.type === 'in' ? '供应商' : '客户'">
          <el-select
            v-model="editForm.company_id"
            filterable
            placeholder="请选择"
            class="form-select"
          >
            <el-option
              v-for="company in companies"
              :key="company.id"
              :label="company.name"
              :value="company.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="editForm.notes"
            type="textarea"
            :rows="2"
            placeholder="请输入备注信息（选填）"
          />
        </el-form-item>
      </el-form>

      <el-descriptions 
        v-else
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
          ¥{{ order?.total_amount }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDateTime(order?.created_at).slice(0, -3) }}
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
        <div class="items-header">
          <h3>商品明细</h3>
          <el-button 
            v-if="order?.status === 'draft' && isEditing"
            type="primary" 
            @click="addItem"
          >
            <el-icon><Plus /></el-icon>添加商品
          </el-button>
        </div>
        
        <el-table :data="editForm.items" border>
          <el-table-column label="商品" width="300">
            <template #default="{ row, $index }">
              <div v-if="order?.status === 'draft' && isEditing" class="product-select">
                <el-autocomplete
                  v-model="row.searchText"
                  :fetch-suggestions="querySearch"
                  placeholder="输入商品名称或条形码"
                  :trigger-on-focus="false"
                  @select="(item) => handleSelect(item, $index)"
                  class="product-input"
                >
                  <template #default="{ item }">
                    <div>{{ item.name }}</div>
                    <small style="color: #999">{{ item.barcode }}</small>
                  </template>
                </el-autocomplete>
                <el-button @click="() => showProductList($index)">
                  <el-icon><List /></el-icon>
                </el-button>
              </div>
              <span v-else>{{ getInventoryName(row.inventory_id) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="barcode" label="条形码" width="150" />
          <el-table-column label="数量" width="180">
            <template #default="{ row }">
              <div class="quantity-cell">
                <div class="input-wrapper">
                  <el-input-number
                    v-if="order?.status === 'draft' && isEditing"
                    v-model="row.quantity"
                    :min="1"
                    :max="order?.type === 'out' ? row.maxQuantity : undefined"
                    :controls="false"
                    class="no-controls"
                    @change="(value) => handleQuantityChange(value, row)"
                  />
                  <span v-else>{{ row.quantity }}</span>
                </div>
                <div v-if="order?.type === 'out' && isEditing" class="stock-info">
                  库存:{{ row.maxQuantity || '-' }}
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="单价" width="150">
            <template #default="{ row }">
              <el-input-number
                v-if="order?.status === 'draft' && isEditing"
                v-model="row.price"
                :precision="2"
                :step="0.1"
                :min="0"
                :controls="false"
                class="no-controls"
              />
              <span v-else>¥{{ row.price }}</span>
            </template>
          </el-table-column>
          <el-table-column label="金额" width="120" align="right">
            <template #default="{ row }">
              ¥{{ (row.quantity * row.price).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="备注">
            <template #default="{ row }">
              <el-input
                v-if="order?.status === 'draft' && isEditing"
                v-model="row.notes"
                placeholder="选填"
              />
              <span v-else>{{ row.notes || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column 
            v-if="order?.status === 'draft' && isEditing"
            label="操作" 
            width="80"
            fixed="right"
          >
            <template #default="{ $index }">
              <el-button 
                type="danger" 
                link
                @click="removeItem($index)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 待处理状态的操作按钮 -->
      <div v-if="order?.status === 'draft'" class="draft-actions">
        <template v-if="isEditing">
          <el-button 
            type="success"
            @click="handleSave"
            :loading="saving"
          >
            保存修改
          </el-button>
          <el-button @click="cancelEdit">取消编辑</el-button>
        </template>
        <template v-else>
          <el-button 
            type="warning"
            @click="startEdit"
          >
            编辑单据
          </el-button>
          <el-button 
            type="primary"
            @click="handleConfirm"
          >
            确认单据
          </el-button>
          <el-button 
            type="danger"
            @click="handleCancel"
          >
            取消单据
          </el-button>
        </template>
      </div>

      <!-- 添加商品列表对话框 -->
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
        <!-- 添加分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Printer, Plus, List } from '@element-plus/icons-vue'
import { formatDateTime, formatDateTimeMinute } from '@/utils/format'
import type { StockOrder, StockOrderItem } from '@/types/inventory'
import { getStockOrder, updateStockOrder, confirmStockOrder, cancelStockOrder } from '@/api/stockOrder'
import { getInventory, searchInventory, getInventoryList } from '@/api/inventory'
import { getCompanies } from '@/api/company'
import { CompanyType } from '@/types/company'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const order = ref<StockOrder | undefined>()
const inventoryNames = ref<Record<number, string>>({})  // 使用 ref 存储商品名称
const saving = ref(false)
const companies = ref<any[]>([])
const editForm = ref({
  company_id: undefined as number | undefined,
  notes: '',
  items: [] as StockOrderItem[]
})

// 是否处于编辑模式
const isEditing = ref(false)

// 商品列表相关
const productListVisible = ref(false);
const productList = ref<Inventory[]>([]);
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);
const currentSelectIndex = ref<number>(-1);

// 获取订单详情
const loadOrder = async () => {
  loading.value = true
  try {
    const response = await getStockOrder(Number(route.params.id))
    order.value = response
    
    // 先加载所有商品信息
    if (order.value?.items) {
      await loadInventoryNames(order.value.items.map(item => item.inventory_id))
    }
    
    // 初始化编辑表单
    editForm.value = {
      company_id: order.value?.company_id,
      notes: order.value?.notes || '',
      items: order.value?.items.map(item => ({
        ...item,
        searchText: inventoryNames.value[item.inventory_id] || '' // 使用已加载的商品名称
      })) || []
    }
    
    // 如果是待处理状态，加载供应商/客户列表
    if (order.value?.status === 'draft') {
      await loadCompanies()
    }
  } catch (error) {
    ElMessage.error('加载订单详情失败')
  } finally {
    loading.value = false
  }
}

// 加载商品名称
const loadInventoryNames = async (inventoryIds: number[]) => {
  try {
    const promises = inventoryIds.map(async (id) => {
      try {
        const response = await getInventory(id)
        if (response) {
          inventoryNames.value[id] = response.name
        }
      } catch (error) {
      }
    })
    await Promise.all(promises)
  } catch (error) {
  }
}

// 获取商品名称
const getInventoryName = (id: number) => {
  return inventoryNames.value[id] || '-'
}

// 状态相关
const getStatusType = (status?: string) => {
  if (!status) return ''
  const types: Record<string, string> = {
    draft: '',
    confirmed: 'success',
    cancelled: 'danger'
  }
  return types[status] || ''
}

const getStatusText = (status?: string) => {
  if (!status) return ''
  const texts: Record<string, string> = {
    draft: '待处理',
    confirmed: '已确认',
    cancelled: '已取消'
  }
  return texts[status] || status
}

// 加载供应商/客户列表
const loadCompanies = async () => {
  try {
    const response = await getCompanies({
      type: order.value?.type === 'in' ? CompanyType.SUPPLIER : CompanyType.CUSTOMER
    })
    companies.value = response.items
  } catch (error) {
    ElMessage.error('加载供应商/客户列表失败')
  }
}

// 搜索商品
const querySearch = async (queryString: string) => {
  if (!queryString) return []
  try {
    const response = await searchInventory(queryString)
    return response.map(item => ({
      value: item.name,
      ...item
    })).filter(item => item.is_active)
  } catch (error) {
    return []
  }
}

// 选择商品
const handleSelect = async (item: any, index: number) => {
  // 先检查商品是否被禁用
  if (!item.is_active) {
    ElMessage.warning(`商品 ${item.name} 已被禁用，无法${order.value?.type === 'in' ? '入库' : '出库'}`);
    return;
  }

  if (order.value?.type === 'out') {
    try {
      if (item.stock <= 0) {
        ElMessage.warning(`商品 ${item.name} 当前库存为0，无法出库`);
        return;
      }
      editForm.value.items[index] = {
        ...editForm.value.items[index],
        inventory_id: item.id,
        barcode: item.barcode,
        searchText: item.name,
        price: order.value?.type === 'in' ? 0 : item.last_price || 0,
        maxQuantity: item.stock  // 使用搜索结果中的库存数量
      }
    } catch (error) {
      ElMessage.error('获取商品库存信息失败');
      return;
    }
  } else {
    editForm.value.items[index] = {
      ...editForm.value.items[index],
      inventory_id: item.id,
      barcode: item.barcode,
      searchText: item.name,
      price: 0
    };
  }
}

// 添加商品行
const addItem = () => {
  editForm.value.items.push({
    inventory_id: undefined,
    barcode: '',
    searchText: '',
    quantity: 1,
    price: 0,
    notes: ''
  })
}

// 删除商品行
const removeItem = (index: number) => {
  editForm.value.items.splice(index, 1)
}

// 开始编辑
const startEdit = async () => {
  isEditing.value = true
  // 如果是出库单，需要获取所有商品的库存信息
  if (order.value?.type === 'out' && order.value?.items) {
    try {
      const promises = order.value.items.map(async (item) => {
        const response = await getInventory(item.inventory_id)
        return {
          ...item,
          maxQuantity: response.stock
        }
      })
      const itemsWithStock = await Promise.all(promises)
      
      // 初始化编辑表单
      editForm.value = {
        company_id: order.value?.company_id,
        notes: order.value?.notes || '',
        items: itemsWithStock.map(item => ({
          ...item,
          searchText: inventoryNames.value[item.inventory_id] || ''
        }))
      }
    } catch (error) {
      ElMessage.error('获取商品库存信息失败')
      isEditing.value = false
      return
    }
  } else {
    // 入库单不需要检查库存
    editForm.value = {
      company_id: order.value?.company_id,
      notes: order.value?.notes || '',
      items: order.value?.items.map(item => ({
        ...item,
        searchText: inventoryNames.value[item.inventory_id] || ''
      })) || []
    }
  }
}

// 取消编辑
const cancelEdit = () => {
  isEditing.value = false
  loadOrder() // 重新加载订单信息
}

// 保存修改
const handleSave = async () => {
  try {
    // 验证是否添加了商品
    if (editForm.value.items.length === 0) {
      ElMessage.warning('请至少添加一个商品')
      return
    }
    
    // 验证商品数据
    const invalidItems = editForm.value.items.filter(item => !item.inventory_id)
    if (invalidItems.length > 0) {
      ElMessage.warning('请完善商品信息')
      return
    }

    saving.value = true
    await updateStockOrder(Number(route.params.id), {
      company_id: editForm.value.company_id,
      notes: editForm.value.notes,
      items: editForm.value.items.map(({ searchText, ...item }) => item)
    })
    
    ElMessage.success('保存成功')
    isEditing.value = false // 保存成功后退出编辑模式
    loadOrder() // 重新加载订单信息
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 确认订单
const handleConfirm = async () => {
  try {
    await ElMessageBox.confirm('确认此出入库单？确认后将无法修改', '提示', {
      type: 'warning'
    })
    await confirmStockOrder(Number(route.params.id))
    ElMessage.success('确认成功')
    loadOrder()  // 重新加载订单信息
  } catch (error: any) {
    if (error !== 'cancel') {
      // 显示具体的错误信息
      const errorMsg = error.response?.data?.detail || '确认失败'
      ElMessage.error(errorMsg)
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

// 监听数量变化
const handleQuantityChange = (value: number, row: any) => {
  if (order.value?.type === 'out' && row.maxQuantity !== undefined) {
    if (value > row.maxQuantity) {
      ElMessage.warning(`商品库存不足，当前库存: ${row.maxQuantity}`)
      row.quantity = row.maxQuantity
    }
  }
}

// 处理打印
const handlePrint = () => {
  if (!order.value) return

  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    ElMessage.error('无法打开打印窗口')
    return
  }

  // 构建打印内容
  const content = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>${order.value.type === 'in' ? '入库单' : '出库单'} - ${order.value.order_no}</title>
      <style>
        body {
          font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
          padding: 20px;
          max-width: 800px;
          margin: 0 auto;
          color: #333;
        }
        .header {
          text-align: center;
          margin-bottom: 20px;
          padding-bottom: 15px;
          border-bottom: 2px solid #eee;
        }
        .header h2 {
          font-size: 22px;
          margin: 0;
          color: #1a1a1a;
        }
        .info {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
          margin-bottom: 10px;
          padding: 15px;
          background: #f8f9fa;
          border-radius: 4px;
        }
        .info-item {
          margin-bottom: 0px;
          line-height: 1.4;
          font-size: 13px;
        }
        .info-item.company-name {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .info-item span {
          color: #666;
          margin-right: 6px;
          font-weight: 500;
        }
        .notes-item {
          padding: 10px 15px;
          margin-top: -10px;
          margin-bottom: 20px;
          background: #f8f9fa;
          border-radius: 4px;
          font-size: 13px;
          line-height: 1.4;
        }
        .notes-item span {
          color: #666;
          margin-right: 6px;
          font-weight: 500;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 30px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        th, td {
          border: 1px solid #e0e0e0;
          padding: 12px;
          text-align: left;
          font-size: 14px;
        }
        th {
          background-color: #f4f6f8;
          font-weight: 600;
          color: #1a1a1a;
        }
        tr:nth-child(even) {
          background-color: #f8f9fa;
        }
        tr:hover {
          background-color: #f5f5f5;
        }
        .amount {
          text-align: right;
          font-family: Monaco, monospace;
        }
        tfoot tr {
          background-color: #f4f6f8;
          font-weight: bold;
        }
        tfoot td {
          border-top: 2px solid #ddd;
        }
        .print-footer {
          margin-top: 40px;
          padding-top: 20px;
          border-top: 1px solid #eee;
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 20px;
        }
        .signature-box {
          margin-top: 15px;
        }
        .signature-line {
          border-top: 1px solid #999;
          width: 200px;
          margin-top: 50px;
        }
        @media print {
          body {
            padding: 0;
          }
          .no-print {
            display: none;
          }
          @page {
            margin: 2cm;
          }
        }
        .no-print {
          text-align: center;
          margin: 20px 0;
        }
        .no-print button {
          padding: 10px 20px;
          background: #409eff;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }
        .no-print button:hover {
          background: #66b1ff;
        }
      </style>
    </head>
    <body>
      <div class="header">
        <h2>${order.value.type === 'in' ? '入库单' : '出库单'}</h2>
      </div>
      <div class="info">
        <div class="info-item">
          <span>单据编号：</span>${order.value.order_no}
        </div>
        <div class="info-item company-name">
          <span>${order.value.type === 'in' ? '供应商' : '客户'}：</span>${order.value.company_name || '未知'}
        </div>
        <div class="info-item">
          <span>状态：</span>${getStatusText(order.value.status)}
        </div>
        <div class="info-item">
          <span>创建时间：</span>${formatDateTime(order.value.created_at).slice(0, -3)}
        </div>
        <div class="info-item">
          <span>操作人：</span>${order.value.operator_name || '未知'}
        </div>
      </div>
      <div class="notes-item">
        <span>备注：</span>${order.value.notes || '-'}
      </div>
      <table>
        <thead>
          <tr>
            <th>条形码</th>
            <th>商品名称</th>
            <th>数量</th>
            <th>单价</th>
            <th>金额</th>
            <th>备注</th>
          </tr>
        </thead>
        <tbody>
          ${order.value.items.map(item => `
            <tr>
              <td>${item.barcode}</td>
              <td>${getInventoryName(item.inventory_id)}</td>
              <td class="amount">${item.quantity}</td>
              <td class="amount">¥${item.price}</td>
              <td class="amount">¥${(item.quantity * item.price)}</td>
              <td>${item.notes || '-'}</td>
            </tr>
          `).join('')}
        </tbody>
        <tfoot>
          <tr>
            <td colspan="4" style="text-align: right;"><strong>总金额：</strong></td>
            <td class="amount"><strong>¥${order.value.total_amount}</strong></td>
            <td></td>
          </tr>
        </tfoot>
      </table>
      <div class="print-footer">
        <div class="signature-box">
          <div>经办人：</div>
          <div class="signature-line"></div>
        </div>
        <div class="signature-box">
          <div>审核人：</div>
          <div class="signature-line"></div>
        </div>
      </div>
      <div class="no-print">
        <button onclick="window.print()">打印单据</button>
      </div>
    </body>
    </html>
  `

  // 写入打印内容
  printWindow.document.write(content)
  printWindow.document.close()
}

// 显示商品列表
const showProductList = async (index: number) => {
  currentSelectIndex.value = index;
  try {
    const response = await getInventoryList({
      page: currentPage.value,
      page_size: pageSize.value
    });
    productList.value = response.items;
    total.value = response.total;
    productListVisible.value = true;
  } catch (error) {
    ElMessage.error('加载商品列表失败');
  }
};

// 处理页码变化
const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  showProductList(currentSelectIndex.value);
};

// 处理每页数量变化
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  showProductList(currentSelectIndex.value);
};

// 从列表选择商品
const handleProductSelect = (row: Inventory) => {
  handleSelect(row, currentSelectIndex.value);
  productListVisible.value = false;
};

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
  flex-direction: column;
  margin-bottom: 30px;
  
  .header-left {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
    
    h2 {
      margin: 0;
      margin-right: 15px;
      font-size: 20px;
    }
    
    .status-tag {
      margin-left: 10px;
    }
  }

  .header-right {
    display: flex;
    justify-content: flex-end;
    
    .button-group {
      display: flex;
      gap: 10px;
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

.draft-actions {
  display: flex;
  gap: 10px;
  padding: 20px 0;
  border-top: 1px solid #eee;
  border-bottom: 1px solid #eee;
  margin-bottom: 20px;
}

.form-select {
  width: 100%;
}

.full-width {
  width: 100%;
}

.items-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

:deep(.el-autocomplete) {
  width: 100%;
  
  .el-input__inner {
    font-size: 14px;
  }
}

:deep(.el-autocomplete-suggestion__list) {
  li {
    line-height: 1.2;
    padding: 8px 10px;
    
    small {
      display: block;
      margin-top: 4px;
    }
  }
}

.quantity-cell {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  
  .input-wrapper {
    width: 80px;
    flex-shrink: 0;
  }
  
  .stock-info {
    font-size: 12px;
    color: #909399;
    white-space: nowrap;
    margin-left: auto;
    padding-right: 8px;
  }
}

:deep(.no-controls) {
  width: 100%;
  
  .el-input-number__decrease,
  .el-input-number__increase {
    display: none;
  }
  
  .el-input__inner {
    padding: 0 2px !important;
    text-align: center;
    min-height: 32px;
  }
}

.product-select {
  display: flex;
  gap: 8px;
  align-items: center;
  
  .product-input {
    flex: 1;
  }
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-dialog__body) {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style> 
