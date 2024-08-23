<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ChatDotRound, Mic } from '@element-plus/icons-vue'
import VideoComponent from '@/components/VideoComponent.vue'
import MessageComponent from '@/components/MessageComponent.vue'
import {
  onAirRoomChatRequest,
  onAirRoomInfoRequest,
  type StreamingRoomStatusItem
} from '@/api/streamingRoom'

// 定义传参
const props = defineProps({
  roomId: {
    type: String,
    default: '0'
  }
})

// 输入框
const inputValue = ref('')

const currentStatus = ref({} as StreamingRoomStatusItem)

const getRoomInfo = async () => {
  // 获取主播视频地址
  // 获取商品信息，显示在右下角的商品缩略图
  // 获取后端对话记录 messageList ，进行渲染
  const { data } = await onAirRoomInfoRequest(Number(props.roomId))
  if (data.code === 0) {
    currentStatus.value = data.data
    console.info(currentStatus.value)
  }
}

// 发送按钮
const handelSendClick = async () => {
  console.info(inputValue.value)
  // 显示在对话框-用户
  // disable 输入框
  // 显示 loading 图标 - 主播
  // 发送
  // request(roomId, userId, newValue)
  // 接收
  // 取消 loading ，更新为返回值 - 主播
  // 将对话记录更新到数据库
  const { data } = await onAirRoomChatRequest(Number(props.roomId), '123', inputValue.value)
  if (data.code === 0) {
    await getRoomInfo()
  }
}

onMounted(() => {
  // 获取直播间实时信息格信息
  getRoomInfo()
})
</script>

<template>
  <div>
    <el-row :gutter="1">
      <el-col :span="16">
        <!-- 主播视频 -->
        <VideoComponent
          :src="currentStatus.currentStreamerVideo"
          :key="currentStatus.currentStreamerVideo"
          :autoplay="true"
          :width="50"
          :height="50"
        />
      </el-col>
      <el-col :span="8">
        <div>
          <el-scrollbar height="1000px">
            <!-- 对话记录显示在右上角 -->
            <MessageComponent
              v-for="(item, index) in currentStatus.conversation"
              :key="index"
              :role="item.role"
              :avater="item.avater"
              :userName="item.userName"
              :message="item.message"
              :datetime="item.datetime"
            />
          </el-scrollbar>

          <div class="bottom-items">
            <el-button circle>
              <el-icon><Mic /></el-icon>
            </el-button>
            <el-input
              v-model="inputValue"
              style="width: 100%; border-radius: 8px; margin: 0px 10px 0px 10px"
              :autosize="{ minRows: 1, maxRows: 12 }"
              type="textarea"
              placeholder="向主播提问"
            />
            <el-button circle @click="handelSendClick">
              <el-icon><ChatDotRound /></el-icon>
            </el-button>
          </div>
          <div class="bottom-items">
            显示商品信息和缩略图
            <el-button>商品详情</el-button>
          </div>
          <div class="bottom-items">
            <el-button>下一个商品</el-button>
            <el-button>下播</el-button>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style lang="scss" scoped>
.bottom-items {
  margin-top: 10px; // 距离上面的控件有一定的距离
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
