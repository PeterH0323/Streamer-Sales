<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { ChatDotRound, Mic } from '@element-plus/icons-vue'

import VideoComponent from '@/components/VideoComponent.vue'
import MessageComponent from '@/components/MessageComponent.vue'
import {
  onAirRoomChatRequest,
  onAirRoomInfoRequest,
  onAirRoomNextProductRequest,
  type StreamingRoomStatusItem
} from '@/api/streamingRoom'
import type { ProductListItem, StreamerInfo } from '@/api/product'

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
currentStatus.value.currentProductInfo = {} as ProductListItem
currentStatus.value.streamerInfo = {} as StreamerInfo

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

const userInfo = ref({
  userId: '123',
  userName: 'no1-user',
  avater: 'xxxx'
})

// 主播回答提示符
const loadingStreamRes = ref(false)

// 输入框使能与否
const disableInput = ref(false)

// 发送按钮
const handelSendClick = async () => {
  console.info(inputValue.value)
  // 显示在对话框-用户
  currentStatus.value.conversation.push({
    role: 'user',
    userId: userInfo.value.userId,
    userName: userInfo.value.userName,
    avater: userInfo.value.avater,
    message: inputValue.value,
    datetime: ''
  })
  // disable 输入框
  disableInput.value = true
  // 显示 loading 图标 - 主播
  loadingStreamRes.value = true

  // request(roomId, userId, newValue)
  // 将对话记录更新到数据库
  const { data } = await onAirRoomChatRequest(
    Number(props.roomId),
    userInfo.value.userId,
    inputValue.value
  )

  // 取消 loading
  loadingStreamRes.value = false
  if (data.code === 0) {
    // 更新 list
    await getRoomInfo()
  }

  // 启动输入框
  disableInput.value = false

  // 在 DOM 更新后滚动到底部
  nextTick(scrollToBottom)
}

// 用于滚动条
const scrollbarRef = ref<HTMLElement | null>(null)
const scrollToBottom = async () => {
  // 注意：需要通过 nextTick 以等待 DOM 更新完成
  await nextTick()
  scrollbarRef.value.setScrollTop(10000) // TODO 先设置一个比较大的值，后续需要获取控件的高度进行赋值
}

// 下一个商品
const handleNextProductClick = async () => {
  const { data } = await onAirRoomNextProductRequest(Number(props.roomId))
  if (data.code === 0) {
    console.info('Next Product')
    currentStatus.value = data.data
    console.info(currentStatus.value)
  }
}

// 结束直播按钮
const handleOffLineClick = () => {}

onMounted(() => {
  // 获取直播间实时信息格信息
  getRoomInfo()
})
</script>

<template>
  <div>
    <el-row :gutter="1">
      <el-col :span="14">
        <!-- 主播视频 -->
        <VideoComponent
          :src="currentStatus.currentStreamerVideo"
          :key="currentStatus.currentStreamerVideo"
          :autoplay="true"
          :width="1300"
          :height="1300"
          :videoAfterEnd="currentStatus.streamerInfo.base_mp4_path"
          style="display: flex; justify-content: center; align-items: center"
        />
      </el-col>
      <el-col :span="10">
        <div>
          <el-scrollbar height="1000px" ref="scrollbarRef" id="scrollbarRef">
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

            <!-- 加载标识 -->
            <!-- <el-button :loading="loadingStreamRes" v-show="loadingStreamRes" /> -->
          </el-scrollbar>

          <!-- 对话框 -->
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
              :disabled="disableInput"
            />
            <el-button circle @click="handelSendClick">
              <el-icon><ChatDotRound /></el-icon>
            </el-button>
          </div>

          <!-- 商品展示 -->
          <div class="bottom-items">
            <el-card style="border-radius: 5px">
              <el-image
                style="width: 100px; height: 100px"
                :src="currentStatus.currentProductInfo.image_path"
                fit="contain"
              />
              <el-button @click="handleNextProductClick">下一个商品</el-button>
              <el-button @click="handleOffLineClick">下播</el-button>
            </el-card>
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
  width: auto;
}
</style>
