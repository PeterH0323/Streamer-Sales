<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { ElMessage } from 'element-plus/es'

import { type StreamingRoomInfo, streamerRoomListRequest } from '@/api/streamingRoom'
import { useRouter } from 'vue-router'

// 获取主播信息
const streamingList = ref([] as StreamingRoomInfo[])
const router = useRouter()

onMounted(async () => {
  // 获取主播信息
  const { data } = await streamerRoomListRequest()
  if (data.code === 0) {
    streamingList.value = data.data
    ElMessage.success('获取直播间信息成功')
  }
})

const chunkArray = (array: StreamingRoomInfo[], chunkSize: number) => {
  // 切割每 n 个为一行（即一个数组），方便后续进行 v-for 遍历
  const result = []
  for (let i = 0; i < array.length; i += chunkSize) {
    result.push(array.slice(i, i + chunkSize))
  }
  return result
}

const chunkedArray = computed(() => chunkArray(streamingList.value, 4))
</script>

<template>
  <div>
    <div v-for="(row, rowIndex) in chunkedArray" :key="rowIndex" class="row">
      <el-row :gutter="20">
        <el-col v-for="(item, index) in row" :key="index" :span="8">
          <el-card style="max-width: 480px">
            <img :src="item.room_poster" style="width: 100%" />
            <div>{{ item.name }}</div>
            <div>商品数：{{ item.product_list.length }}</div>
            <div class="bottom-button">
              <el-button
                type="primary"
                plain
                @click="router.push({ name: 'StreamingEdit', params: { roomId: item.id } })"
              >
                详情
              </el-button>
              <el-button type="primary" plain> 开启直播 </el-button>
              <el-button type="danger" plain> 删除 </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.row {
  margin-bottom: 20px;
}

.bottom-button {
  margin-top: 10px; // 距离上面的控件有一定的距离
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
