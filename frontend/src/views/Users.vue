<template>
  <div class="users">
    <div class="toolbar">
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        添加员工
      </el-button>
    </div>

    <el-table :data="users" style="width: 100%" v-loading="loading">
      <el-table-column prop="username" label="用户名" width="150" />
      <el-table-column prop="name" label="姓名" width="150" />
      <el-table-column label="权限" min-width="300">
        <template #default="{ row }">
          <el-tag v-for="perm in row.permissions" :key="perm" class="permission-tag">
            {{ permissionLabels[perm] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="last_login" label="最后登录时间" width="180">
        <template #default="{ row }">
          {{ row.last_login ? formatDate(row.last_login) : '从未登录' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button-group>
            <el-button type="primary" link @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="danger" link @click="handleDelete(row)">
              删除
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <!-- 添加/编辑员工对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑员工' : '添加员工'" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="用户名" prop="username" v-if="!isEdit">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" type="password" />
        </el-form-item>
        <el-form-item label="权限" prop="permissions">
          <el-checkbox-group v-model="form.permissions">
            <el-checkbox v-for="(label, value) in permissionLabels" 
              :key="value" :label="value">
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
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import { getUsers, createUser, updateUser, deleteUser } from '../api/user';

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

const permissionLabels = {
  inventory: '库存管理',
  stock_in: '商品入库',
  stock_out: '商品出库',
  transactions: '交易记录',
  performance: '业绩统计',
  analysis: '商品分析'
};

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3到50个字符', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码不能少于6个字符', trigger: 'blur' }
  ],
  permissions: [
    { required: true, message: '请选择权限', trigger: 'change' }
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
    console.error('加载用户列表失败:', error);
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
  isEdit.value = true;
  form.value = {
    ...row,
    password: ''  // 编辑时不显示密码
  };
  dialogVisible.value = true;
};

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除员工"${row.name}"吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await deleteUser(row.id);
    ElMessage.success('删除成功');
    loadUsers();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除员工失败:', error);
      ElMessage.error('删除失败');
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
        console.error('操作失败:', error);
        ElMessage.error('操作失败');
      }
    }
  });
};

onMounted(() => {
  loadUsers();
});
</script>

<style scoped>
.users {
  padding: 20px;
  height: 100%;
  box-sizing: border-box;
}

.toolbar {
  margin-bottom: 20px;
}

.permission-tag {
  margin-right: 5px;
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style> 