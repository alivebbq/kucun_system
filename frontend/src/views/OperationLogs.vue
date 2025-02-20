<template>
  <div class="operation-logs">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>操作日志</span>
        </div>
      </template>

      <el-table :data="logs" style="width: 100%">
        <el-table-column prop="created_at" label="操作时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="operator.name" label="操作人" width="120" />
        <el-table-column prop="operation_type" label="操作类型" width="120">
          <template #default="{ row }">
            <el-tag>{{ formatOperationType(row.operation_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="details" label="操作详情">
          <template #default="{ row }">
            <div v-if="row.operation_type === 'cancel_transaction'">
              撤销了 {{ row.details.product_name }} 的
              {{ row.details.type === 'in' ? '入库' : '出库' }}记录
              (数量: {{ row.details.quantity }}, 
              单价: ¥{{ row.details.price }})
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { getOperationLogs } from '../api/log';

const logs = ref([]);

const formatDate = (date: string) => {
  return new Date(date).toLocaleString();
};

const formatOperationType = (type: string) => {
  const types = {
    'cancel_transaction': '撤销交易'
  };
  return types[type] || type;
};

const loadLogs = async () => {
  try {
    const response = await getOperationLogs();
    logs.value = response;
  } catch (error) {
    ElMessage.error('加载日志失败');
  }
};

onMounted(() => {
  loadLogs();
});
</script>

<style scoped>
.operation-logs {
  padding: 20px;
  height: 100%;
  box-sizing: border-box;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 