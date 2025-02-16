<script setup lang="ts">
import 'element-plus/dist/index.css';
import { onMounted } from 'vue';
import { useUserStore } from './stores/user';

const userStore = useUserStore();

onMounted(async () => {
  if (userStore.token && !userStore.user) {
    await userStore.restoreUser();
  }
});
</script>

<template>
  <router-view></router-view>
</template>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100vh;
  width: 100vw;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  overflow: hidden; /* 防止出现滚动条 */
}

#app {
  height: 100vh;
  width: 100vw;
}
</style>
