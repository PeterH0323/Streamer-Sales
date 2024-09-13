<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound, Microphone, VideoPause } from '@element-plus/icons-vue'

import VideoComponent from '@/components/VideoComponent.vue'
import MessageComponent from '@/components/MessageComponent.vue'
import {
  streamRoomOffline,
  genAsrResult,
  onAirRoomChatRequest,
  onAirRoomInfoRequest,
  onAirRoomNextProductRequest,
  sendAudioToServer,
  type StreamingRoomStatusItem
} from '@/api/streamingRoom'
import type { ProductItem, StreamerInfo } from '@/api/product'
import { ElMessage, ElMessageBox } from 'element-plus'
import { AxiosError } from 'axios'
import { getUserInfoRequest, type UserInfo } from '@/api/user'

const router = useRouter()

// 定义传参
const props = defineProps({
  roomId: {
    type: String,
    default: '0'
  }
})

// 用户信息
const userInfoItem = ref({} as UserInfo)

const getUserInfo = async () => {
  try {
    const { data } = await getUserInfoRequest()

    if (data.code === 0) {
      userInfoItem.value = data.data
    } else {
      ElMessage.error('获取用户信息失败: ' + data.message)
    }
  } catch (error: unknown) {
    if (error instanceof AxiosError) {
      ElMessage.error('获取用户信息失败: ' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
  }
}

// 输入框
const inputValue = ref('')

const currentStatus = ref({} as StreamingRoomStatusItem)
currentStatus.value.currentProductInfo = {} as ProductItem
currentStatus.value.streamerInfo = {} as StreamerInfo

const getRoomInfo = async () => {
  // 获取主播视频地址
  // 获取商品信息，显示在右下角的商品缩略图
  // 获取后端对话记录 messageList ，进行渲染
  try {
    const { data } = await onAirRoomInfoRequest(Number(props.roomId))
    if (data.code === 0) {
      currentStatus.value = data.data
      console.info(currentStatus.value)
    } else {
      ElMessage.error('获取直播间信息失败' + data.message)
    }
  } catch (error: unknown) {
    if (error instanceof AxiosError) {
      ElMessage.error('获取直播间信息失败' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
  }
}

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
    userId: userInfoItem.value.user_id,
    userName: userInfoItem.value.username,
    avatar: userInfoItem.value.avatar,
    message: inputValue.value,
    send_time: ''
  })
  // disable 输入框
  disableInput.value = true
  // 显示 loading 图标 - 主播
  loadingStreamRes.value = true

  // request(roomId, userId, newValue)
  // 将对话记录更新到数据库
  try {
    const { data } = await onAirRoomChatRequest(Number(props.roomId), inputValue.value)

    // 取消 loading
    loadingStreamRes.value = false
    if (data.code === 0) {
      // 更新 list
      await getRoomInfo()
    } else {
      ElMessage.error('更新对话信息失败' + data.message)
    }
  } catch (error: unknown) {
    if (error instanceof AxiosError) {
      ElMessage.error('更新对话信息失败' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
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
  if (scrollbarRef.value) {
    // scrollbarRef.value.setScrollTop(10000) // TODO 先设置一个比较大的值，后续需要获取控件的高度进行赋值
    scrollbarRef.value.scrollTop = 10000 // TODO 先设置一个比较大的值，后续需要获取控件的高度进行赋值
  }
}

// 下一个商品
const handleNextProductClick = async () => {
  try {
    const { data } = await onAirRoomNextProductRequest(Number(props.roomId))
    if (data.code === 0) {
      console.info('Next Product')
      await getRoomInfo()
    } else {
      ElMessage.error('失败' + data.message)
    }
  } catch (error: unknown) {
    if (error instanceof AxiosError) {
      ElMessage.error('失败' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
  }
}

// 结束直播按钮
const handleOffLineClick = async () => {
  ElMessageBox.confirm(`确定要下播吗？`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      try {
        const { data } = await streamRoomOffline(Number(props.roomId))
        if (data.code === 0) {
          ElMessage.success('下播成功')
          router.push({ name: 'StreamingOverview' })
        } else {
          ElMessage.error('下播失败' + data.message)
        }
      } catch (error: unknown) {
        if (error instanceof AxiosError) {
          ElMessage.error('失败' + error.message)
        } else {
          ElMessage.error('未知错误：' + error)
        }
      }
    })
    .catch((error) => {
      ElMessage.error('下播失败: ' + error.message)
    })
}

onMounted(() => {
  // 获取用户信息
  getUserInfo()

  // 获取直播间实时信息格信息
  getRoomInfo()
})

// 录音
// 状态管理
const isRecording = ref(false)
let mediaRecorder: MediaRecorder | null = null
let chunks: Blob[] = []
let stream: MediaStream | null = null

// 开始录音
const startRecording = () => {
  navigator.mediaDevices
    .getUserMedia({ audio: true })
    .then((s) => {
      stream = s
      mediaRecorder = new MediaRecorder(s)
      mediaRecorder.start()
      mediaRecorder.addEventListener('dataavailable', handleDataAvailable)
      mediaRecorder.addEventListener('stop', handleStop)
    })
    .catch((err) => {
      ElMessage.error('无法访问麦克风: ' + err.message)
    })
}

// 停止录音
const stopRecording = () => {
  if (mediaRecorder) {
    mediaRecorder.stop()
  }
  if (stream) {
    stream.getTracks().forEach((track) => track.stop())
  }
}

// 切换录音状态
const handleRecord = () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
  isRecording.value = !isRecording.value
}

// 处理录音数据
const handleDataAvailable = (e: BlobEvent) => {
  chunks.push(e.data)
}

// 处理录音停止事件
const handleStop = async () => {
  const blob = new Blob(chunks, { type: 'audio/webm' })
  try {
    // 将 asr 文件发送到服务器
    const { data } = await sendAudioToServer(blob)
    if (data.code === 0) {
      ElMessage.success('正在进行语音转文字，请稍候！')
      // 调取接口开始进行 asr 识别

      console.info(data)
      const { data: asr_data } = await genAsrResult(Number(props.roomId), data.data)
      ElMessage.success('语音转文字成功！')

      // 自动进行对话
      if (asr_data.code === 0) {
        inputValue.value = asr_data.data
        handelSendClick()
      }
    }
  } catch (error: unknown) {
    if (error instanceof AxiosError) {
      ElMessage.error('语音转文字失败: ' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
  }
  chunks = []
}
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
          <el-scrollbar height="1110px" ref="scrollbarRef" id="scrollbarRef">
            <!-- 对话记录显示在右上角 -->
            <MessageComponent
              v-for="(item, index) in currentStatus.conversation"
              :key="index"
              :role="item.role"
              :avatar="item.avatar"
              :userName="item.userName"
              :message="item.message"
              :datetime="item.send_time"
            />

            <!-- 加载标识 -->
            <!-- <el-button :loading="loadingStreamRes" v-show="loadingStreamRes" /> -->
          </el-scrollbar>

          <!-- 聊天记录右下角商品展示 -->
          <div class="floating-card">
            <el-card shadow="never">
              <div class="product-info">
                <p class="title">当前商品</p>

                <!-- 商品图片 -->
                <el-image
                  style="width: 100px; height: 100px"
                  :src="currentStatus.currentProductInfo.image_path"
                  fit="contain"
                />

                <!-- 商品信息 -->
                <p class="title">{{ currentStatus.currentProductInfo.product_name }}</p>
                <p class="content">{{ currentStatus.currentProductInfo.heighlights }}</p>
                <p class="price">¥ {{ currentStatus.currentProductInfo.selling_price }}</p>
              </div>
            </el-card>
          </div>

          <!-- 对话框 -->
          <div class="bottom-items">
            <el-button
              circle
              size="large"
              :type="isRecording ? 'danger' : 'primary'"
              @click="handleRecord"
            >
              <el-icon v-if="!isRecording">
                <Microphone />
              </el-icon>
              <el-icon v-else>
                <VideoPause />
              </el-icon>
            </el-button>
            <el-input
              v-model="inputValue"
              style="width: 100%; border-radius: 8px; margin: 0px 10px 0px 10px"
              :autosize="{ minRows: 2, maxRows: 12 }"
              type="textarea"
              placeholder="向主播提问"
              :disabled="disableInput"
              size="large"
            />
            <el-button circle @click="handelSendClick" size="large">
              <el-icon>
                <ChatDotRound />
              </el-icon>
            </el-button>
          </div>

          <div style="margin-top: 10px">
            <div class="bottom-button">
              <el-button
                type="primary"
                @click="handleNextProductClick"
                v-show="!currentStatus.finalProduct"
              >
                下一个商品
              </el-button>
              <el-button type="danger" @click="handleOffLineClick">下播</el-button>
            </div>
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
  align-items: center;
  width: auto;
}

.bottom-button {
  display: flex;
  margin-top: 10px;
  float: right;
}

::v-deep(.el-input__wrapper) {
  border-radius: 14px;
}

.el-card {
  margin-top: 10px;
  border-radius: 10px;
}

.floating-card {
  position: absolute;
  right: 10px; /* 调整到右边的距离 */
  bottom: 200px; /* 调整到底部的距离 */
  z-index: 30; /* 确保 card 显示在最上层 */
  width: 200px; /* 可以根据需要调整 */

  .product-info {
    display: flex;
    flex-direction: column; /* 将子元素垂直排列 */
    justify-content: center; /* 垂直居中 */
    align-items: center; /* 水平居中 */

    .title {
      font-size: 18px;
      font-weight: 600;
    }

    .content {
      font-size: 15px;
      color: #b1b3b8;
    }

    .price {
      font-size: 16px;
      color: #fda100;
    }
  }
}
</style>
