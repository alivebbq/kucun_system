<template>
  <div class="login-container">
    <div class="login-box">
      <!-- Logo和标题 -->
      <div class="header">
        <div class="logo">
          <img src="/inventory.svg" alt="Logo">
        </div>
        <h1>顶顶库存管理系统</h1>
        <p class="subtitle">专业的批发商进销存管理解决方案</p>
      </div>

      <!-- 添加演示账号信息 -->
      <div class="demo-account">
        <div class="demo-title">
          <el-icon><InfoFilled /></el-icon>
          <span>演示账号</span>
        </div>
        <div class="demo-content">
          <p>账号：demo</p>
          <p>密码：123456</p>
          <el-button 
            type="primary" 
            link 
            @click="useDemoAccount"
          >
            一键体验
          </el-button>
        </div>
        <div class="demo-tips">
          <p>* 演示账号拥有完整的系统功能权限</p>
          <p>* 系统每小时自动重置数据，请谨慎操作</p>
          <p>* 如需正式使用，请添加客服微信开通正式账号</p>
        </div>
      </div>

      <!-- 登录表单 -->
      <el-form 
        ref="formRef" 
        :model="form" 
        :rules="rules" 
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            :prefix-icon="User"
            size="large"
            @keyup.enter="focusPassword"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            ref="passwordInput"
            v-model="form.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item class="login-button">
          <el-button
            type="primary"
            :loading="loading"
            size="large"
            class="submit-btn"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 修改底部信息，添加申请试用入口 -->
      <div class="footer">
        <div class="contact-info">
          <p class="contact">系统购买或试用请添加客服微信：</p>
          <p class="contact-detail">
            <el-icon><ChatDotRound /></el-icon>
            Curiosity_Alive / 15520768906
          </p>
        </div>
        <p class="copyright">© {{ new Date().getFullYear() }} 海南顶顶软件科技有限公司 版权所有</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { User, Lock, InfoFilled, ChatDotRound } from '@element-plus/icons-vue';
import type { FormInstance, FormRules } from 'element-plus';
import { login } from '../api/user';
import { useUserStore } from '../stores/user';

const router = useRouter();
const userStore = useUserStore();
const formRef = ref<FormInstance>();
const passwordInput = ref<InstanceType<typeof ElInput>>();
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

const focusPassword = () => {
  passwordInput.value?.focus();
};

const handleLogin = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const response = await login(form.value.username, form.value.password);
        
        if (response.access_token) {
          userStore.setToken(response.access_token);
          userStore.setUser(response.user);
          ElMessage.success('登录成功');
          router.push('/');
        }
      } catch (error: any) {
        console.error('登录失败:', error);
        ElMessage.error(error.response?.data?.detail || '登录失败');
      } finally {
        loading.value = false;
      }
    }
  });
};

// 一键使用演示账号
const useDemoAccount = () => {
  form.value.username = 'demo';
  form.value.password = '123456';
  handleLogin();
};
</script>

<style lang="scss" scoped>
.login-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1890ff11 0%, #1890ff05 100%);
  position: relative;
  overflow: hidden;

  // 背景动画效果
  &::before {
    content: "";
    position: absolute;
    width: 200%;
    height: 200%;
    background: linear-gradient(
      45deg,
      rgba(24, 144, 255, 0.1) 0%,
      rgba(24, 144, 255, 0.05) 100%
    );
    animation: wave 15s infinite linear;
  }
}

@keyframes wave {
  0% {
    transform: translate(-50%, -50%) rotate(0deg);
  }
  100% {
    transform: translate(-50%, -50%) rotate(360deg);
  }
}

.login-box {
  position: relative;
  width: 420px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.header {
  text-align: center;
  margin-bottom: 40px;

  .logo {
    width: 80px;
    height: 80px;
    margin: 0 auto 20px;

    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
  }

  h1 {
    font-size: 28px;
    color: #303133;
    margin: 0 0 8px;
    font-weight: 600;
  }

  .subtitle {
    font-size: 16px;
    color: #909399;
    margin: 0;
  }
}

.login-form {
  .el-form-item {
    margin-bottom: 24px;
  }

  :deep(.el-input__wrapper) {
    box-shadow: 0 0 0 1px #dcdfe6 inset;
    padding: 0 12px;
    height: 44px;
    transition: all 0.3s;

    &:hover {
      box-shadow: 0 0 0 1px #c0c4cc inset;
    }

    &.is-focus {
      box-shadow: 0 0 0 1px #409eff inset !important;
    }
  }

  :deep(.el-input__prefix) {
    font-size: 18px;
    color: #909399;
  }
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  letter-spacing: 4px;
  background: linear-gradient(135deg, #409eff, #1890ff);
  border: none;
  transition: all 0.3s;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
  }

  &:active {
    transform: translateY(0);
  }
}

.demo-account {
  background: #f0f9ff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
  border: 1px solid #91d5ff;

  .demo-title {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #1890ff;
    font-weight: 500;
    margin-bottom: 12px;
  }

  .demo-content {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 8px 0;
    
    p {
      margin: 0;
      color: #666;
    }
  }

  .demo-tips {
    margin-top: 12px;
    font-size: 12px;
    color: #999;
    
    p {
      margin: 4px 0;
    }
  }
}

.contact-info {
  margin-bottom: 16px;
  
  .contact {
    margin-bottom: 8px;
    color: #606266;
  }

  .contact-detail {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: #409EFF;
    font-weight: 500;
  }
}

.copyright {
  color: #909399;
  margin: 0;
}

// 响应式设计
@media screen and (max-width: 576px) {
  .login-box {
    width: 90%;
    padding: 20px;
  }

  .header {
    margin-bottom: 30px;

    .logo {
      width: 60px;
      height: 60px;
    }

    h1 {
      font-size: 24px;
    }

    .subtitle {
      font-size: 14px;
    }
  }
}
</style> 