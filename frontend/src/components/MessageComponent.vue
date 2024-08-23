<script setup lang="ts">
import { ref, onMounted } from 'vue'

// 定义组件入参
const props = defineProps({
  avater: {
    type: String,
    default: ''
  },
  role: {
    type: String,
    default: ''
  },
  userName: {
    type: String,
    default: ''
  },
  message: {
    type: String,
    default: ''
  },
  datetime: {
    type: String,
    default: ''
  }
})
</script>

<template>
  <div class="message-block">
    <el-row :gutter="0">
      <el-col :span="2">
        <div>
          <!-- 头像: {{ props.avater }} -->
          <el-avatar :src="props.avater" />
        </div>
      </el-col>
      <el-col :span="22">
        <div class="user-info">
          <!-- 标签 -->
          <template v-if="props.role === 'streamer'">
            <el-tag type="success" style="margin-right: 5px">主播</el-tag>
          </template>
          <!-- 用户名 -->
          <div class="message-title">{{ props.userName }}</div>
          <!-- 发送时间 -->
          <div class="message-title">{{ props.datetime }}</div>
        </div>
        <div class="message-content">
          <!-- 内容 -->
          {{ props.message }}
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped lang="scss">
.message-block {
  margin-top: 20px;
}

.message-content {
  background-color: aquamarine;
  border-radius: 20px;
  padding: 15px;
  width: 400px;
}

.user-info {
  display: flex;
  align-items: center;
  margin-left: 8px;

  .message-title {
    margin-left: 8px;
  }
}
</style>
