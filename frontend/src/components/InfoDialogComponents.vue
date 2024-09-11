<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { MdPreview } from 'md-editor-v3'

import 'md-editor-v3/lib/preview.css'

import { genProductInstructionContentRequest } from '@/api/product'
import { genSalesDocRequest } from '@/api/llm'
import VideoComponent from '@/components/VideoComponent.vue'
import { genDigitalHuamnVideoRequest } from '@/api/digitalHuman'
import { type StreamingRoomProductList } from '@/api/streamingRoom'
import { AxiosError } from 'axios'

const dialogFormVisible = ref(false)

// AI 生成后的 文案 or 数字人视频 值双向绑定
const modelGenValue = defineModel<StreamingRoomProductList[]>({
  default: [] as StreamingRoomProductList[]
})

// 定义标题
const titleMap = { SalesDoc: '主播文案', Instruction: '说明书', DigitalHuman: '数字人视频' }
const title = ref('')
const titleName = ref('')
const infoValue = ref('')
const itemType = ref('')
const productId = ref(0)
const streamerId = ref(0)
const salesDoc = ref('')
const showItemInfoDialog = async (
  titleName_: string,
  itemType_: keyof typeof titleMap,
  itemValue: string,
  productId_: number,
  streamerId_: number = 0,
  salesDoc_: string = ''
) => {
  title.value = titleMap[itemType_]
  titleName.value = titleName_ + ' - '
  itemType.value = itemType_
  productId.value = productId_
  streamerId.value = streamerId_
  salesDoc.value = salesDoc_

  dialogFormVisible.value = true

  if (itemType_ === 'Instruction') {
    // 请求接口获取说明书数据
    try {
      const { data } = await genProductInstructionContentRequest(itemValue)
      if (data.code === 0) {
        infoValue.value = data.data
      } else {
        ElMessage.error('获取说明书失败：' + data.message)
      }
    } catch (error: unknown) {
      if (error instanceof AxiosError) {
        ElMessage.error('获取说明书失败：' + error.message)
      } else {
        ElMessage.error('未知错误：' + error)
      }
    }
  } else {
    infoValue.value = itemValue
  }
}

const handleSaveClick = () => {
  // 更新双向绑定的值
  dialogFormVisible.value = false
  updateGenValue(infoValue.value)
}

// 是否正在生成文案标识
const isGenerating = ref(false)

const updateGenValue = (newValue: string) => {
  let index = -1
  // 更新与父组件双向绑定的值
  for (let i = 0; i < modelGenValue.value.length; i++) {
    // 根据返回数据继续添加商品
    if (modelGenValue.value[i].product_id === productId.value) {
      index = i
      break
    }
  }

  if (itemType.value === 'SalesDoc') {
    modelGenValue.value[index].sales_doc = newValue
  } else if (itemType.value === 'DigitalHuman') {
    modelGenValue.value[index].start_video = newValue
  }
}

// 生成进度条
const genPercentage = ref(0)

// 定义计时器句柄
let timerId: number | null = null
let totalGenSec: number = 1 // 生成时间

// 开始/停止生成进度条
const startGenProgress = () => {
  genPercentage.value = 0
  if (timerId) {
    // 如果计时器正在运行，则清除计时器
    clearInterval(timerId)
  }

  if (itemType.value === 'DigitalHuman') {
    // 数字人生成时间
    totalGenSec = 5 * 60
  } else {
    // 文案生成时间
    totalGenSec = 10
  }

  // 启动计时器
  timerId = window.setInterval(() => {
    if (genPercentage.value < 99) {
      genPercentage.value += parseFloat((100 / totalGenSec).toFixed(2))
    }

    if (genPercentage.value > 99) {
      genPercentage.value = 99
    }
  }, 1000)
}

const stopGenProgress = () => {
  if (timerId) {
    // 如果计时器正在运行，则清除计时器
    clearInterval(timerId)
  }
}

// 生成数据人视频
const getDigitalHumanVideo = async () => {
  if (salesDoc.value === '') {
    ElMessage.error('需先生成文案')
    return
  }

  isGenerating.value = true
  ElMessage.success('正在生成，预计 3 分钟，请稍候')
  ElMessage.warning('若未生成完成，请不要离开页面！')

  startGenProgress()
  try {
    const { data } = await genDigitalHuamnVideoRequest(streamerId.value, salesDoc.value)
    console.log(data)
    if (data.code === 0) {
      infoValue.value = data.data
      updateGenValue(infoValue.value)
      genPercentage.value = 100
      ElMessage.success('生成数字人视频成功')
    } else {
      ElMessage.error('生成数字人视频失败：' + data.message)
    }
  } catch (error: unknown) {
    if (error instanceof AxiosError) {
      ElMessage.error('生成数字人视频失败：' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
  }
  isGenerating.value = false
  stopGenProgress()
}

// 生成解说文案
const handleGenSalesDocClick = async () => {
  isGenerating.value = true
  ElMessage.success('正在生成，请稍候')
  ElMessage.warning('若未生成完成，请不要离开页面！')
  try {
    startGenProgress()

    const { data } = await genSalesDocRequest(Number(productId.value), Number(streamerId.value))
    console.log(data)
    if (data.code === 0) {
      infoValue.value = data.data
      updateGenValue(infoValue.value) // 更新与父组件双向绑定的值
      ElMessage.success('生成文案成功')
    } else {
      ElMessage.error('生成文案失败：' + data.message)
    }
  } catch (error: unknown) {
    if (error instanceof AxiosError) {
      ElMessage.error('生成文案失败：' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
  }
  isGenerating.value = false
  stopGenProgress()
}

// 在组件卸载前确保计时器被清除
onBeforeUnmount(() => {
  if (timerId) {
    clearInterval(timerId)
  }
})

defineExpose({ showItemInfoDialog })
</script>

<template>
  <div>
    <!-- 显示说明书 or 文案 or 数字人视频-->
    <el-dialog
      v-model="dialogFormVisible"
      :title="titleName + title"
      width="1000"
      top="5vh"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <!-- 说明书 -->
      <template v-if="itemType === 'Instruction'">
        <div style="text-align: left">
          <MdPreview editorId="preview-SalesDoc" :modelValue="infoValue" />
        </div>
      </template>

      <!-- 主播文案  -->
      <template v-else-if="itemType === 'SalesDoc'">
        <div>
          <el-input
            type="textarea"
            v-model="infoValue"
            maxlength="2000"
            :autosize="{ minRows: 20 }"
            show-word-limit
          />
          <div class="progress-item">
            <el-progress v-show="isGenerating" :text-inside="true" :percentage="genPercentage" />
          </div>
          <div class="bottom-gen-btn">
            <el-button @click="handleGenSalesDocClick" :loading="isGenerating" type="primary">
              AI 生成
            </el-button>
          </div>
        </div>
      </template>

      <!-- 数字人视频 -->
      <template v-else-if="itemType === 'DigitalHuman'">
        <div class="make-center">
          <VideoComponent :src="infoValue" :key="infoValue" :height="600" />
        </div>

        <div class="progress-item">
          <el-progress v-show="isGenerating" :text-inside="true" :percentage="genPercentage" />
        </div>

        <div class="bottom-gen-btn">
          <el-button @click="getDigitalHumanVideo" :loading="isGenerating" type="primary">
            AI 生成数字人视频
          </el-button>
        </div>
      </template>
      <template #footer>
        <div class="dialog-footer bottom-gen-btn">
          <!-- <el-button type="primary" @click="handelEditClick"> 编辑 </el-button> -->

          <el-button
            v-show="itemType !== 'Instruction'"
            @click="handleSaveClick"
            type="success"
            :disabled="isGenerating"
          >
            保存
          </el-button>
          <el-button @click="dialogFormVisible = false" :disabled="isGenerating">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
// 每个表单底部 AI 生成按钮
.bottom-gen-btn {
  margin-top: 15px;
  display: flex;
  justify-content: center;
  align-items: center;
}

// 进度条
.progress-item {
  display: flex;
  justify-content: center;
  align-items: center;

  ::v-deep(.el-progress) {
    height: 30px;
    width: 80%;
    margin: 10px;
  }

  ::v-deep(.el-progress-bar__outer) {
    height: 16px !important;
  }
}

.make-center {
  display: flex;
  justify-content: center;
  align-items: center;
}

::v-deep(.el-input__wrapper) {
  border-radius: 14px;
}

// 使用 ::v-deep 选择器来覆盖 el-dialog 的默认样式。
::v-deep(.el-dialog) {
  border-radius: 10px;
  padding: 20px;

  --el-dialog-bg-color: #f7f8fa;
  --el-dialog-title-font-size: 20px;
}
</style>
