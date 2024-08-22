<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { ChatDotRound, Mic } from '@element-plus/icons-vue'
import VideoComponent from '@/components/VideoComponent.vue'
import MessageComponent from '@/components/MessageComponent.vue'

// 定义传参
const props = defineProps({
  roomId: {
    type: String,
    default: '0'
  }
})

// 输入框
const inputValue = ref('')

const messageList = ref([
  {
    role: 'streamer',
    userId: '0',
    userName: 'streamer',
    avater: '',
    message:
      '当然，很高兴今天能在这里和家人们分享我家的宝贝——[瑜伽垫]，这是一款集多功能于一身的宝贝，它不仅具有防滑材质，还能为你带来清新的空气，同时它那吸湿排汗的设计更是让每一次瑜伽练习都更舒适自然，而且它的厚度适中，不仅能够确保你的瑜伽动作自如，还能给你带来轻巧便携的感觉。      别看它只有巴掌大小，但它的“实力”不容小觑。它经过多重工艺处理，不仅保证了它的防滑性能，还增强了它的耐用度，让你在使用它的过程中不用担心它脆弱的身姿。而且，它也是一款易清洁的产品，只需要简单的打理，就可以让你的瑜伽垫焕然一新，轻松应对日常的清洁问题了。      在各种瑜伽动作中，它都能胜任。无论是力量型的体式，还是柔韧性的伸展，它都能轻松应对，让你的每一次瑜伽练习都更加轻松愉悦。      最重要的是，它还能适应各种瑜伽动作，无论是高难度还是低难度的动作，它都能完美应对，确保你在这个过程中不会感到不适。      家人们，别犹豫了，赶紧下单吧！[瑜伽垫]，不仅是你所需，它也是你所需的，是真正的舒适与便携并存的宝贝。现在就下单，让你的瑜伽之旅更加顺利，更加舒心！[家人们]，一起选购[瑜伽垫]，享受健康和乐趣并存的瑜伽体验吧！',
    datetime: '2024-08-18 12:11:53'
  },
  {
    role: 'customer',
    userId: '1',
    userName: '123666',
    avater: '',
    message: '多少钱，什么时候到货',
    datetime: '2024-08-18 12:11:53'
  }
])

const getRoomInfo = () => {
  // 获取主播视频地址
  // 获取商品信息，显示在右下角的商品缩略图
  // 获取后端对话记录 messageList ，进行渲染
}

// 发送按钮
const handelSendClick = () => {
  console.info(inputValue.value)
  // 显示在对话框-用户
  // disable 输入框
  // 显示 loading 图标 - 主播
  // 发送
  // request(roomId, userId, newValue)
  // 接收
  // 取消 loading ，更新为返回值 - 主播
  // 将对话记录更新到数据库
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
        <!-- 主播视频 http://127.0.0.1:8000/files/digital_human/vid_output/7647801c-5f50-11ef-b0c4-00155d18ca83.mp4 -->
        <VideoComponent src="xxx" :width="50" :height="50" />
      </el-col>
      <el-col :span="8">
        <el-scrollbar height="1000px">
          <!-- 对话记录显示在右上角 -->
          <MessageComponent
            v-for="(item, index) in messageList"
            :key="index"
            :role="item.role"
            :avater="item.avater"
            :userName="item.userName"
            :message="item.message"
            :datetime="item.datetime"
          />
        </el-scrollbar>

        <div class="send-items">
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
        <div class="send-items">
          显示商品信息和缩略图
          <el-button>下一个商品</el-button>
          <el-button>商品详情</el-button>
          <el-button>下播</el-button>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style lang="scss" scoped>
.send-items {
  margin-top: 10px; // 距离上面的控件有一定的距离
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
