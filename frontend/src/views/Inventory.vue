<template>
  <div class="page-container">
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          添加商品
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索商品..."
          class="search-input"
          clearable
          @clear="handleSearch"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <el-card class="content-card">
      <el-table 
        :data="inventory" 
        style="width: 100%"
        v-loading="loading"
        :header-cell-class-name="'table-header'"
      >
        <el-table-column prop="barcode" label="条形码" width="150" />
        <el-table-column prop="name" label="商品名称" />
        <el-table-column prop="unit" label="单位" width="100" />
        <el-table-column prop="stock" label="库存" width="100" align="right" class="inventory-status">
          <template #default="{ row }">
            <span :class="row.stock <= row.warning_stock ? 'low' : ''">
              {{ formatNumber(row.stock) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="warning_stock" label="警戒库存" width="100" align="right" class="inventory-status">
          <template #default="{ row }">
            <span :class="row.stock <= row.warning_stock ? 'low' : ''">
              {{ formatNumber(row.warning_stock) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150">
          <template #default="{ row }">
            <el-tooltip 
              v-if="row.remark" 
              :content="row.remark" 
              placement="top" 
              :hide-after="2000"
            >
              <span class="remark-text">{{ row.remark }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button type="primary" link @click="handleEdit(row)">
                编辑
              </el-button>
              <el-button 
                :type="row.is_active ? 'danger' : 'success'" 
                link 
                @click="handleToggleStatus(row)"
              >
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 添加分页组件 -->
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
    </el-card>

    <!-- 添加/编辑商品对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑商品' : '添加商品'"
      width="500px"
      class="custom-dialog"
      :close-on-click-modal="false"
      :before-close="handleDialogClose"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="custom-form"
      >
        <el-form-item label="条形码" prop="barcode">
          <el-input v-model="form.barcode" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="商品名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="单位" prop="unit">
          <el-input v-model="form.unit" />
        </el-form-item>
        <el-form-item label="警戒库存" prop="warning_stock">
          <el-input-number v-model="form.warning_stock" :min="0" :precision="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input 
            v-model="form.remark" 
            type="textarea" 
            :rows="3" 
            placeholder="请输入商品备注信息（选填）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleDialogClose">取消</el-button>
          <el-button type="primary" @click="handleSubmit">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search, Plus } from '@element-plus/icons-vue';
import type { FormInstance, FormRules } from 'element-plus';
import {
  getInventoryList,
  createInventory,
  updateInventory,
  deleteInventory,
  toggleInventoryStatus,
  type Inventory
} from '../api/inventory';
import { count } from 'echarts/types/src/component/dataZoom/history.js';

const loading = ref(false);
const inventory = ref<Inventory[]>([]);
const searchQuery = ref('');
const dialogVisible = ref(false);
const isEdit = ref(false);
const formRef = ref<FormInstance>();
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);
const searchTimeout = ref<number | null>(null);

const form = ref({
  barcode: '',
  name: '',
  unit: '',
  warning_stock: 10,
  remark: ''
});

const rules: FormRules = {
  barcode: [
    { required: true, message: '请输入条形码', trigger: 'blur' },
    { min: 1, max: 13, message: '条形码长度在1到13个字符', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入商品名称', trigger: 'blur' }
  ],
  unit: [
    { required: true, message: '请输入单位', trigger: 'blur' }
  ],
  warning_stock: [
    { required: true, message: '请输入警戒库存', trigger: 'blur' }
  ]
};

// 格式化数字
const formatNumber = (num: number | null) => {
  if (num === null || num === undefined) return '0.00';
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
};

// 加载库存数据
const loadInventory = async () => {
  loading.value = true;
  try {
    const response = await getInventoryList({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchQuery.value
    });
    inventory.value = response.items;
    total.value = response.total;
  } catch (error) {
    ElMessage.error('加载库存数据失败');
  } finally {
    loading.value = false;
  }
};

// 处理搜索 - 添加防抖
const handleSearch = () => {
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value);
  }
  
  searchTimeout.value = window.setTimeout(() => {
    currentPage.value = 1; // 重置到第一页
    loadInventory();
  }, 300);
};

// 处理页码变化
const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  loadInventory();
};

// 处理每页条数变化
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1; // 重置到第一页
  loadInventory();
};

// 处理添加商品
const handleAdd = () => {
  isEdit.value = false;
  form.value = {
    barcode: '',
    name: '',
    unit: '',
    warning_stock: 10,
    remark: ''
  };
  formRef.value?.clearValidate();  // 清除表单验证状态
  dialogVisible.value = true;
};

// 处理编辑商品
const handleEdit = (row: Inventory) => {
  isEdit.value = true;
  form.value = {
    barcode: row.barcode,
    name: row.name,
    unit: row.unit,
    warning_stock: row.warning_stock,
    remark: row.remark || ''
  };
  formRef.value?.clearValidate();
  dialogVisible.value = true;
};

// 处理删除商品
const handleDelete = async (row: Inventory) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除商品"${row.name}"吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await deleteInventory(row.barcode);
    ElMessage.success('删除成功');
    // 刷新库存列表
    await loadInventory();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败');
    }
  }
};

// 处理对话框关闭
const handleDialogClose = () => {
  dialogVisible.value = false;
  formRef.value?.resetFields();
  form.value = {
    barcode: '',
    name: '',
    unit: '',
    warning_stock: 10,
    remark: ''
  };
};

// 处理表单提交
const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (isEdit.value) {
          await updateInventory(form.value.barcode, form.value);
          ElMessage.success('更新成功');
        } else {
          await createInventory(form.value);
          ElMessage.success('添加成功');
        }
        handleDialogClose();
        loadInventory(); // 重新加载当前页数据
      } catch (error: any) {
        // 直接显示错误信息
        ElMessage.error(error.message);
      }
    }
  });
};

// 处理切换状态
const handleToggleStatus = async (row: Inventory) => {
  try {
    const action = row.is_active ? '禁用' : '启用';
    await ElMessageBox.confirm(
      `确定要${action}商品"${row.name}"吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: row.is_active ? 'warning' : 'info'
      }
    );

    await toggleInventoryStatus(row.barcode);
    ElMessage.success(`${action}成功`);
    await loadInventory();
  } catch (error: any) {
    if (error !== 'cancel') {
      // 显示后端返回的具体错误信息
      ElMessage.error(error.response?.detail || '操作失败');
    }
  }
};

onMounted(() => {
  loadInventory();
});

// 确保组件卸载时清理状态
onUnmounted(() => {
  inventory.value = [];
  searchQuery.value = '';
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value);
  }
  if (dialogVisible.value) {
    handleDialogClose();
  }
});
</script>

<style lang="scss" scoped>
.inventory-status {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .stock-value {
    font-weight: 500;
    
    &.low {
      color: #E6A23C;
    }
    
    &.empty {
      color: #F56C6C;
    }
  }
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.remark-text {
  display: inline-block;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>