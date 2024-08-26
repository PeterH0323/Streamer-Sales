<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es'

import { type StreamingRoomInfo, streamerRoomListRequest } from '@/api/streamingRoom'

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

const tagMap = { 0: '未开播', 1: '直播中', 2: '已下播' }
</script>

<template>
  <div>
    <div style="margin-bottom: 20px">
      <el-button @click="router.push({ name: 'StreamingCreate' })" type="primary">
        新建直播间
      </el-button>
    </div>
    <div v-for="(row, rowIndex) in chunkedArray" :key="rowIndex" class="row">
      <el-row :gutter="20">
        <el-col v-for="(item, index) in row" :key="index" :span="8">
          <el-card style="max-width: 480px">
            <img :src="item.room_poster" style="width: 100%" />
            <div class="title">
              <h3>{{ item.name }}</h3>
              <el-tag type="success" effect="light"> {{ tagMap[item.status.live_status] }}</el-tag>
            </div>
            <div>
              <p>主播：{{ item.streamer_info.name }}</p>
              <p>商品数：{{ item.product_list.length }}</p>
              <p>
                开播时间: {{ item.status.live_status === 1 ? item.status.start_time : '未开播' }}
              </p>
            </div>
            <div class="bottom-button">
              <el-button
                type="primary"
                @click="router.push({ name: 'StreamingEdit', params: { roomId: item.room_id } })"
              >
                编辑直播间
              </el-button>
              <el-button
                type="primary"
                :disabled="item.status.live_status !== 1"
                @click="router.push({ name: 'StreamingOnAir', params: { roomId: item.room_id } })"
              >
                进入直播间
              </el-button>
              <el-button type="danger" :disabled="item.status.live_status === 1"> 删除 </el-button>
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

.el-card {
  padding: 20px;
  border-radius: 20px;
}

.title {
  display: flex;
  justify-content: space-between;
  .h3 {
    font-size: 50px;
    font-weight: 600;
    margin: 24px 0px 8px 0px;
  }
}

.bottom-button {
  margin-top: 20px; // 距离上面的控件有一定的距离
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
