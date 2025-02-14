<template>
  <el-container class="layout">
    <!-- 侧边栏 -->
    <el-aside width="180px">
      <el-menu :default-active="route.path" router class="menu">
        <el-menu-item v-for="item in filteredMenuItems" :key="item.path" :index="'/' + item.path">
          <el-icon>
            <component :is="item.meta.icon" />
          </el-icon>
          <span>{{ item.meta.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主要内容区域 -->
    <el-container class="main-container">
      <el-header height="60px">
        <div class="header-content">
          <h2>库存管理系统</h2>
          <div class="user-info">
            <span>{{ userStore.user?.name || userStore.user?.username }}</span>
            <el-button type="text" @click="handleLogout">退出</el-button>
          </div>
        </div>
      </el-header>
      <el-main>
        <router-view></router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from '../stores/user';
import { ElMessageBox } from 'element-plus';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

// 根据权限过滤菜单项
const filteredMenuItems = computed(() => {
  const mainRoute = router.options.routes.find(r => r.path === '/');
  return mainRoute?.children?.filter(item => {
    // 需要店主权限的页面
    if (item.meta?.requiresOwner) {
      return userStore.isOwner;
    }
    // 需要特定权限的页面
    if (item.meta?.permission) {
      return userStore.hasPermission(item.meta.permission);
    }
    return true;
  });
});

// 处理退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    userStore.logout();
    router.push('/login');
  } catch {
    // 用户取消退出
  }
};
</script>

<style scoped>
.layout {
  height: 100vh;
  width: 100vw;
}

.main-container {
  flex: 1;
  width: calc(100% - 180px);
}

.el-main {
  padding: 0;
  /* 移除默认内边距 */
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
}

.menu {
  height: 100%;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.el-aside {
  background-color: #304156;
  width: 180px !important;
}

.el-menu {
  border-right: none;
}

.el-header {
  background-color: #fff;
  border-bottom: 1px solid #dcdfe6;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-info span {
  color: #606266;
}
</style>