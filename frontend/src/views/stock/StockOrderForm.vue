<template>
  <div class="page-container">
    <div class="form-container">
      <div class="form-header">
        <h2>{{ type === 'in' ? '新建入库单' : '新建出库单' }}</h2>
      </div>
      
      <!-- 基本信息 -->
      <el-form 
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="order-form"
      >
        <el-form-item 
          :label="type === 'in' ? '供应商' : '客户'" 
          prop="company_id"
        >
          <el-select
            v-model="form.company_id"
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
        
        <el-form-item label="备注" prop="notes">
          <el-input
            v-model="form.notes"
            type="textarea"
            :rows="2"
            placeholder="请输入备注信息（选填）"
          />
        </el-form-item>
      </el-form>

      <!-- 商品列表 -->
      <div class="items-container">
        <div class="items-header">
          <h3>商品明细</h3>
          <el-button type="primary" @click="addItem">
            <el-icon><Plus /></el-icon>添加商品
          </el-button>
        </div>

        <el-table :data="form.items" border>
          <el-table-column label="商品" width="500">
            <template #default="{ row, $index }">
              <div class="product-select">
                <el-autocomplete
                  v-model="row.searchText"
                  :fetch-suggestions="querySearch"
                  placeholder="输入商品名称或条形码"
                  :trigger-on-focus="false"
                  @select="(item) => handleSelect(item, $index)"
                  class="product-input"
                />
                <el-button @click="() => showProductList($index)">
                  <el-icon><List /></el-icon>
                </el-button>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="barcode" label="条形码" width="150" />
          <el-table-column label="数量" width="180">
            <template #default="{ row }">
              <div class="quantity-cell">
                <el-input-number
                  v-model="row.quantity"
                  :min="1"
                  :max="type === 'out' ? row.maxQuantity : undefined"
                  :controls="false"
                  class="no-controls"
                  @change="(value) => handleQuantityChange(value, row)"
                />
                <div v-if="type === 'out' && row.maxQuantity" class="stock-info">
                  (库存:{{ row.maxQuantity }})
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row }">
              <el-input-number
                v-model="row.price"
                :precision="2"
                :step="0.1"
                :min="0"
                :controls="false"
                class="no-controls"
              />
            </template>
          </el-table-column>
          <el-table-column label="金额" width="120">
            <template #default="{ row }">
              ¥{{ (row.quantity * row.price).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="200">
            <template #default="{ row }">
              <el-input
                v-model="row.notes"
                placeholder="选填"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
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

      <!-- 底部操作栏 -->
      <div class="form-footer">
        <div class="total-amount">
          总金额：<span class="amount">¥{{ totalAmount.toFixed(2) }}</span>
        </div>
        <div class="buttons">
          <el-button @click="$router.back()">取消</el-button>
          <el-button type="primary" @click="handleSubmit">保存</el-button>
        </div>
      </div>
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, List } from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'
import type { CreateStockOrderRequest } from '@/types/inventory'
import { createStockOrder } from '@/api/stockOrder'
import { searchInventory, getInventory, getInventoryList } from '@/api/inventory'
import { getCompanies } from '@/api/company'
import { CompanyType } from '@/types/company'
import type { Inventory } from '@/types/inventory'

const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

// 表单数据
const type = route.query.type as 'in' | 'out'
const companies = ref<any[]>([])
const form = ref<CreateStockOrderRequest>({
  type,
  company_id: undefined,
  notes: '',
  items: []
})

// 表单验证规则
const rules = {
  company_id: [
    { required: true, message: '请选择供应商/客户', trigger: 'change' }
  ]
}

// 计算总金额
const totalAmount = computed(() => {
  return form.value.items.reduce((sum, item) => {
    return sum + (item.quantity * item.price)
  }, 0)
})

// 加载供应商/客户列表
const loadCompanies = async () => {
  try {
    const response = await getCompanies({
      type: type === 'in' ? CompanyType.SUPPLIER : CompanyType.CUSTOMER
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

// 商品列表相关
const productListVisible = ref(false)
const productList = ref<Inventory[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const currentSelectIndex = ref<number>(-1)

// 显示商品列表
const showProductList = async (index: number) => {
  currentSelectIndex.value = index
  try {
    const response = await getInventoryList({
      page: currentPage.value,
      page_size: pageSize.value
    })
    productList.value = response.items
    total.value = response.total
    productListVisible.value = true
  } catch (error) {
    ElMessage.error('加载商品列表失败')
  }
}

// 处理页码变化
const handleCurrentChange = (page: number) => {
  currentPage.value = page
  showProductList(currentSelectIndex.value)
}

// 处理每页数量变化
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  showProductList(currentSelectIndex.value)
}

// 从列表选择商品
const handleProductSelect = (row: Inventory) => {
  handleSelect(row, currentSelectIndex.value)
  productListVisible.value = false
}

// 选择商品
const handleSelect = async (item: any, index: number) => {
  // 先检查商品是否被禁用
  if (!item.is_active) {
    ElMessage.warning(`商品 ${item.name} 已被禁用，无法${type === 'in' ? '入库' : '出库'}`);
    return;
  }

  // 如果是出库单，先获取商品详情检查库存
  if (type === 'out') {
    try {
      if (item.stock <= 0) {
        ElMessage.warning(`商品 ${item.name} 当前库存为0，无法出库`);
        return;
      }
      // 保存库存数量，用于后续校验
      form.value.items[index] = {
        ...form.value.items[index],
        inventory_id: item.id,
        barcode: item.barcode,
        searchText: item.name,
        price: item.last_price || 0,
        maxQuantity: item.stock
      };
    } catch (error) {
      ElMessage.error('获取商品库存信息失败');
      return;
    }
  } else {
    // 入库单不需要检查库存
    form.value.items[index] = {
      ...form.value.items[index],
      inventory_id: item.id,
      barcode: item.barcode,
      searchText: item.name,
      price: 0
    };
  }
}

// 监听数量变化
const handleQuantityChange = (value: number, row: any) => {
  if (type === 'out' && row.maxQuantity !== undefined) {
    if (value > row.maxQuantity) {
      ElMessage.warning(`商品库存不足，当前库存: ${row.maxQuantity}`)
      row.quantity = row.maxQuantity
    }
  }
}

// 计算单项金额
const calculateItemTotal = (item: any) => {
  item.total = item.quantity * item.price
}

// 添加商品行
const addItem = () => {
  form.value.items.push({
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
  form.value.items.splice(index, 1)
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    // 验证是否添加了商品
    if (form.value.items.length === 0) {
      ElMessage.warning('请至少添加一个商品')
      return
    }
    
    // 验证商品数据
    const invalidItems = form.value.items.filter(item => !item.inventory_id)
    if (invalidItems.length > 0) {
      ElMessage.warning('请完善商品信息')
      return
    }
    
    const response = await createStockOrder({
      type: type,
      company_id: form.value.company_id,
      notes: form.value.notes,
      items: form.value.items.map(item => ({
        inventory_id: item.inventory_id,
        barcode: item.barcode,
        quantity: item.quantity,
        price: item.price,
        notes: item.notes
      }))
    })
    
    ElMessage.success('创建成功')
    // 直接跳转到详情页
    router.push(`/stock-orders/${response.id}`)
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCompanies()
})
</script>

<style scoped lang="scss">
.form-container {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}

.form-header {
  margin-bottom: 20px;
  
  h2 {
    margin: 0;
    font-size: 20px;
  }
}

.order-form {
  max-width: 800px;
}

.items-container {
  margin-top: 30px;
}

.items-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  h3 {
    margin: 0;
    font-size: 16px;
  }
}

.form-footer {
  margin-top: 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .total-amount {
    font-size: 16px;
    
    .amount {
      font-size: 24px;
      color: #f56c6c;
      font-weight: bold;
    }
  }
}

.full-width {
  width: 100%;
}

.form-select {
  width: 100%;
}

.quantity-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .el-input-number {
    width: 80px;
  }
  
  .stock-info {
    font-size: 12px;
    color: #909399;
    white-space: nowrap;
  }
}

:deep(.no-controls) {
  .el-input-number__decrease,
  .el-input-number__increase {
    display: none;
  }
  
  .el-input__inner {
    padding-left: 15px !important;
    padding-right: 15px !important;
    text-align: center;
  }
}

:deep(.el-table) {
  // 确保表格填满容器
  width: 100%;
  
  .el-input,
  .el-input-number {
    width: 100%;
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