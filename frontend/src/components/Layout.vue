<template>
  <el-container class="layout">
    <!-- 侧边栏 -->
    <el-aside width="180px">
      <el-menu :default-active="route.path" router class="menu">
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="'/' + item.path">
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

const route = useRoute();
const router = useRouter();

// 获取菜单项
const menuItems = computed(() => {
  const mainRoute = router.options.routes.find(r => r.path === '/');
  return mainRoute?.children || [];
});
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
</style>