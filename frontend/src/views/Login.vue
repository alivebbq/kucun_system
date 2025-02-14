<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2 class="login-title">库存管理系统</h2>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="0" class="login-form">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" 
            @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="login-button" @click="handleLogin">
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { login } from '../api/user';
import { useUserStore } from '../stores/user';
import api from '../api/config';

const router = useRouter();
const userStore = useUserStore();
const formRef = ref<FormInstance>();
const loading = ref(false);

const form = ref({
  username: '',
  password: ''
});

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3到50个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码不能少于6个字符', trigger: 'blur' }
  ]
};

const handleLogin = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        console.log('=== Login Request Starting ===');
        
        // 实际登录请求
        const response = await login(form.value.username, form.value.password);
        console.log('Login response:', response);
        
        if (response.access_token) {  // 确保有 token
          userStore.setToken(response.access_token);
          userStore.setUser(response.user);
          ElMessage.success('登录成功');
          router.push('/');
        } else {
          throw new Error('Invalid response format');
        }
      } catch (error: any) {
        console.error('=== Login Error ===');
        console.error('Error details:', {
          name: error.name,
          message: error.message,
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          headers: error.response?.headers,
          config: {
            url: error.config?.url,
            method: error.config?.method,
            headers: error.config?.headers,
            data: error.config?.data,
            baseURL: error.config?.baseURL
          }
        });
        ElMessage.error(error.response?.data?.detail || '登录失败');
      } finally {
        loading.value = false;
        console.log('=== Login Request End ===');
      }
    }
  });
};
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
}

.login-card {
  width: 400px;
}

.login-title {
  text-align: center;
  margin: 0;
  color: #303133;
}

.login-form {
  padding: 20px 0;
}

.login-button {
  width: 100%;
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #dcdfe6 inset;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #409eff inset !important;
}
</style> 