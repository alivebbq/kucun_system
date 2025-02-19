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
          <el-table-column label="商品" width="300">
            <template #default="{ row, $index }">
              <el-autocomplete
                v-model="row.searchText"
                :fetch-suggestions="querySearch"
                placeholder="输入商品名称或条形码"
                :trigger-on-focus="false"
                @select="(item) => handleSelect(item, $index)"
                class="full-width"
              />
            </template>
          </el-table-column>
          <el-table-column prop="barcode" label="条形码" width="150" />
          <el-table-column label="数量" width="150">
            <template #default="{ row }">
              <el-input-number
                v-model="row.quantity"
                :min="1"
                @change="calculateItemTotal(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="150">
            <template #default="{ row }">
              <el-input-number
                v-model="row.price"
                :precision="2"
                :step="0.1"
                :min="0"
                @change="calculateItemTotal(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="金额" width="150">
            <template #default="{ row }">
              ¥{{ (row.quantity * row.price).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="备注" width="200">
            <template #default="{ row }">
              <el-input v-model="row.notes" placeholder="选填" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ $index }">
              <el-button 
                type="danger" 
                size="small"
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'
import type { CreateStockOrderRequest } from '@/types/inventory'
import { createStockOrder } from '@/api/stockOrder'
import { searchInventory } from '@/api/inventory'
import { getCompanies } from '@/api/company'
import { CompanyType } from '@/types/company'
const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()

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
    }))
  } catch (error) {
    return []
  }
}

// 选择商品
const handleSelect = (item: any, index: number) => {
  form.value.items[index] = {
    ...form.value.items[index],
    inventory_id: item.id,
    barcode: item.barcode,
    searchText: item.name,
    price: type === 'in' ? 0 : item.last_price || 0
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
    
    // 提交数据
    const submitData = {
      ...form.value,
      items: form.value.items.map(({ searchText, total, ...item }) => item)
    }
    
    await createStockOrder(submitData)
    ElMessage.success('保存成功')
    router.push('/stock-orders')
    
  } catch (error) {
    ElMessage.error('保存失败')
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
</style> 