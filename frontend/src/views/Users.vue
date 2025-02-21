<template>
  <div class="page-container">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          添加员工
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索员工姓名..."
          class="search-input"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 员工列表 -->
    <el-card class="content-card">
      <el-table 
        :data="filteredUsers" 
        style="width: 100%" 
        v-loading="loading"
        :header-cell-class-name="'table-header'"
        :row-class-name="tableRowClassName"
      >
        <el-table-column label="员工信息" min-width="200">
          <template #default="{ row }">
            <div class="user-info">
              <el-avatar :size="40" :src="generateAvatar(row)">
                {{ row.name?.[0]?.toUpperCase() || row.username[0].toUpperCase() }}
              </el-avatar>
              <div class="user-details">
                <div class="username">{{ row.name || row.username }}</div>
                <div class="account">{{ row.username }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="身份" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="row.is_owner ? 'success' : 'info'"
              effect="plain"
            >
              {{ row.is_owner ? '店主' : '员工' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="权限" min-width="300">
          <template #default="{ row }">
            <template v-if="!row.is_owner">
              <el-tag 
                v-for="perm in sortedPermissions(row.permissions)" 
                :key="perm"
                class="permission-tag"
                effect="light"
              >
                {{ permissionLabels[perm] }}
              </el-tag>
            </template>
            <el-tag v-else type="success" effect="light">全部权限</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="row.is_active ? 'success' : 'danger'"
              effect="light"
              class="status-tag"
            >
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="last_login" label="最后登录" width="180">
          <template #default="{ row }">
            {{ row.last_login ? formatDate(row.last_login) : '从未登录' }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons" v-if="!row.is_owner">
              <el-button 
                type="primary" 
                link
                @click="handleEdit(row)"
              >
                编辑
              </el-button>
              <el-button 
                :type="row.is_active ? 'danger' : 'success'" 
                link
                @click="handleToggleStatus(row)"
              >
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑员工' : '添加员工'"
      width="500px"
      class="custom-dialog"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="custom-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input 
            v-model="form.username" 
            :disabled="isEdit"
            placeholder="登录账号"
          />
        </el-form-item>
        
        <el-form-item label="姓名" prop="name">
          <el-input 
            v-model="form.name"
            placeholder="员工姓名"
          />
        </el-form-item>
        
        <el-form-item 
          label="密码" 
          prop="password"
          :rules="isEdit ? [] : rules.password"
        >
          <el-input
            v-model="form.password"
            type="password"
            placeholder="不修改请留空"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="权限" prop="permissions">
          <el-checkbox-group v-model="form.permissions">
            <el-checkbox 
              v-for="(label, key) in permissionLabels" 
              :key="key" 
              :label="key"
            >
              {{ label }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { Plus, Search, Edit, Lock, Unlock } from '@element-plus/icons-vue';
import { getUsers, createUser, updateUser } from '../api/user';

const loading = ref(false);
const users = ref([]);
const dialogVisible = ref(false);
const isEdit = ref(false);
const formRef = ref<FormInstance>();

const form = ref({
  username: '',
  name: '',
  password: '',
  permissions: []
});

const permissionOrder = [
  'dashboard',
  'stock_order',
  'inventory',
  'finance',
  'other_transactions',
  'transactions',
  'performance',
  'analysis',
  'profit_statement',
];

const permissionLabels: Record<string, string> = {
  'dashboard': '仪表盘',
  'stock_order': '出入库管理',
  'inventory': '库存管理',
  'finance': '应收应付',
  'other_transactions': '其他收支',
  'transactions': '商品记录',
  'performance': '业绩统计',
  'analysis': '商品分析',
  'profit_statement': '利润表'
};

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度应在 3 到 50 个字符之间', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  permissions: [
    { required: true, message: '请至少选择一个权限', trigger: 'change' },
    { 
      validator: (rule: any, value: string[]) => {
        if (!value || value.length === 0) {
          return Promise.reject('请至少选择一个权限');
        }
        return Promise.resolve();
      }, 
      trigger: 'change' 
    }
  ]
};

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const loadUsers = async () => {
  loading.value = true;
  try {
    users.value = await getUsers();
  } catch (error) {
    ElMessage.error('加载用户列表失败');
  } finally {
    loading.value = false;
  }
};

const handleAdd = () => {
  isEdit.value = false;
  form.value = {
    username: '',
    name: '',
    password: '',
    permissions: []
  };
  dialogVisible.value = true;
};

const handleEdit = (row: any) => {
  // 不允许编辑店主账号
  if (row.is_owner) {
    ElMessage.warning('不能编辑店主账号');
    return;
  }
  
  isEdit.value = true;
  form.value = {
    ...row,
    password: ''  // 编辑时不显示密码
  };
  dialogVisible.value = true;
};

const handleToggleStatus = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要${row.is_active ? '禁用' : '启用'}员工"${row.name}"吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await updateUser(row.id, {
      is_active: !row.is_active,
      name: row.name,  // 保持其他字段不变
      permissions: row.permissions  // 保持其他字段不变
    });
    
    ElMessage.success(`${row.is_active ? '禁用' : '启用'}成功`);
    loadUsers();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败');
    }
  }
};

const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (isEdit.value) {
          await updateUser(form.value.id, {
            name: form.value.name,
            permissions: form.value.permissions
          });
          ElMessage.success('更新成功');
        } else {
          await createUser(form.value);
          ElMessage.success('添加成功');
        }
        dialogVisible.value = false;
        loadUsers();
      } catch (error) {
        ElMessage.error('操作失败');
      }
    }
  });
};

// 添加计算属性来对用户列表进行排序
const sortedUsers = computed(() => {
  return [...users.value].sort((a, b) => {
    // 店主始终在第一位
    if (a.is_owner) return -1;
    if (b.is_owner) return 1;
    // 其他用户按创建时间降序排列
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
});

const sortedPermissions = (permissions: string[]) => {
  return [...permissions].sort((a, b) => 
    permissionOrder.indexOf(a) - permissionOrder.indexOf(b)
  );
};

const handleAddUser = async (formEl: FormInstance | null) => {
  if (!formEl) return;
  
  try {
    await formEl.validate();
    const userData = {
      username: form.username,
      name: form.name,
      password: form.password,
      permissions: form.permissions,
      is_owner: false  // 添加员工时默认为 false
    };
    
    await createUser(userData);
    ElMessage.success('添加成功');
    dialogVisible.value = false;
    await loadUsers();
    formEl.resetFields();
  } catch (error) {
    ElMessage.error('添加失败');
  }
};

// 添加搜索功能
const searchQuery = ref('');

const filteredUsers = computed(() => {
  const query = searchQuery.value.toLowerCase();
  return sortedUsers.value.filter(user => 
    user.username.toLowerCase().includes(query) ||
    user.name?.toLowerCase().includes(query)
  );
});

const handleSearch = () => {
  // 搜索逻辑已通过计算属性实现
};

// 生成头像背景色
const generateAvatar = (name: string) => {
  const colors = [
    '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', 
    '#909399', '#9B59B6', '#3498DB', '#1ABC9C'
  ];
  const index = name?.length ? name.charCodeAt(0) % colors.length : 0;
  return colors[index];
};

// 表格行样式
const tableRowClassName = ({ row }: { row: any }) => {
  if (row.is_owner) return 'owner-row';
  if (!row.is_active) return 'inactive-row';
  return '';
};

const permissionOptions = [
  { label: '仪表盘', value: 'dashboard' },
  { label: '出入库管理', value: 'stock_order' },
  { label: '商品管理', value: 'inventory' },
  { label: '财务管理', value: 'finance' },
  { label: '其他收支', value: 'other_transactions' },
  { label: '商品记录', value: 'transactions' },
  { label: '业绩统计', value: 'performance' },
  { label: '商品分析', value: 'analysis' },
  { label: '利润表', value: 'profit_statement' }
];

onMounted(() => {
  loadUsers();
});
</script>

<style lang="scss" scoped>
.user-info {
  display: flex;
  align-items: center;
  gap: 12px;

  .user-details {
    .username {
      font-size: 14px;
      font-weight: 500;
      color: #303133;
      margin-bottom: 4px;
    }

    .account {
      font-size: 12px;
      color: #909399;
    }
  }
}

.permission-tag {
  margin: 2px 4px;
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

:deep(.owner-row) {
  background-color: #f0f9eb !important;
}

:deep(.inactive-row) {
  background-color: #fef0f0 !important;
  color: #909399;
}

:deep(.el-avatar) {
  background: linear-gradient(135deg, #409EFF, #67C23A);
  color: white;
  font-weight: bold;
}

// 其他样式已在 common.scss 中定义
</style> 