<template>
  <el-container class="layout-container">
    <el-aside width="180px">
      <el-menu
        :default-active="route.path"
        class="el-menu-vertical"
        @select="handleSelect"
        :collapse-transition="false"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/inventory">
          <el-icon><Box /></el-icon>
          <span>库存管理</span>
        </el-menu-item>
        <el-menu-item index="/stock-in">
          <el-icon><Plus /></el-icon>
          <span>商品入库</span>
        </el-menu-item>
        <el-menu-item index="/stock-out">
          <el-icon><Minus /></el-icon>
          <span>商品出库</span>
        </el-menu-item>
        <el-menu-item index="/transactions">
          <el-icon><List /></el-icon>
          <span>交易记录</span>
        </el-menu-item>
        <el-menu-item index="/performance">
          <el-icon><TrendCharts /></el-icon>
          <span>业绩统计</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header>
        <div class="header-content">
          <h2>库存管理系统</h2>
          <div class="header-right">
            <el-button type="primary" @click="handleScannerConnect">
              {{ isConnected ? '断开扫码枪' : '连接扫码枪' }}
            </el-button>
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
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import {
  DataLine,
  Box,
  Plus,
  Minus,
  List,
  TrendCharts
} from '@element-plus/icons-vue';

const router = useRouter();
const route = useRoute();
const isConnected = ref(false);

const handleSelect = (index: string) => {
  router.push(index);
};

const handleScannerConnect = () => {
  isConnected.value = !isConnected.value;
  // TODO: 实现扫码枪连接/断开逻辑
};
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.el-aside {
  background-color: #304156;
  color: #fff;
  width: 180px !important;  /* 确保宽度固定 */
}

.el-menu {
  border-right: none;
  width: 100%;  /* 确保菜单占满侧边栏 */
}

.el-header {
  background-color: #fff;
  color: #333;
  line-height: 60px;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
  padding: 0 20px;  /* 添加左右内边距 */
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  max-width: 100%;  /* 确保内容不会溢出 */
}

.header-right {
  display: flex;
  align-items: center;
}

.el-main {
  background-color: #f0f2f5;
  padding: 20px;
  height: calc(100vh - 60px);  /* 减去头部高度 */
  overflow-y: auto;  /* 内容过多时显示滚动条 */
}

.el-menu-vertical {
  height: 100%;
  width: 100%;  /* 确保菜单占满侧边栏 */
}
</style> 