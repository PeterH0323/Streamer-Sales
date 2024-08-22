<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MdPreview } from 'md-editor-v3'

import 'md-editor-v3/lib/preview.css'

import { genProductInstructionContentRequest } from '@/api/product'
import { genSalesDocRequest } from '@/api/llm'
import VideoComponent from '@/components/VideoComponent.vue'
import { genDigitalHuamnVideoRequest } from '@/api/digitalHuman'

const dialogFormVisible = ref(false)
const router = useRouter()

// AI 生成后的 文案 or 数字人视频 值双向绑定
const modelGenValue = defineModel({ default: '' })

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
  itemType_: string,
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
    const { data } = await genProductInstructionContentRequest(itemValue)
    if (data.code === 0) {
      infoValue.value = data.data
    }
  } else {
    infoValue.value = itemValue
  }
}

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

// 生成数据人视频
const getDigitalHumanVideo = async () => {
  if (salesDoc.value === '') {
    ElMessage.error('需要先生成文案')
    return
  }

  isGenerating.value = true
  ElMessage.success('正在生成，请稍候')
  const { data } = await genDigitalHuamnVideoRequest(salesDoc.value)
  console.log(data)
  if (data.code === 0) {
    infoValue.value = data.data
    updateGenValue(infoValue.value)
    ElMessage.success('生成数字人视频成功')
  }
  isGenerating.value = false
}

// 是否正在生成文案标识
const isGenerating = ref(false)
// 生成解说文案
const handleGenSalesDocClick = async () => {
  isGenerating.value = true
  ElMessage.success('正在生成，请稍候')
  const { data } = await genSalesDocRequest(Number(productId.value), Number(streamerId.value))
  console.log(data)
  if (data.code === 0) {
    infoValue.value = data.data
    updateGenValue(infoValue.value) // 更新与父组件双向绑定的值
    ElMessage.success('生成文案成功')
  }
  isGenerating.value = false
}

// 跳转编辑页面
const handelEditClick = () => {
  dialogFormVisible.value = false
  console.log(productId.value)
  router.push({ name: 'ProductEdit', params: { productId: productId.value } })
}

defineExpose({ showItemInfoDialog })
</script>

<template>
  <div>
    <!-- 显示说明书 or 文案 or 数字人视频-->
    <teleport to="body">
      <el-dialog v-model="dialogFormVisible" :title="titleName + title" width="1000" top="5vh">
        <!-- 主播文案  -->
        <template v-if="itemType === 'SalesDoc'">
          <div>
            <el-input
              type="textarea"
              v-model="infoValue"
              maxlength="2000"
              :autosize="{ minRows: 20 }"
              show-word-limit
            />
            <div class="bottom-gen-btn">
              <el-button @click="handleGenSalesDocClick" :loading="isGenerating" type="primary">
                AI 生成
              </el-button>
            </div>
          </div>
        </template>

        <!-- 说明书 -->
        <template v-else-if="itemType === 'Instruction'">
          <div style="text-align: left">
            <MdPreview editorId="preview-SalesDoc" :modelValue="infoValue" />
          </div>
        </template>

        <!-- 数字人视频 -->
        <template v-else-if="itemType === 'DigitalHuman'">
          <div>
            <VideoComponent :src="infoValue" :key="infoValue" />

            <div class="bottom-gen-btn">
              <el-button @click="getDigitalHumanVideo" :loading="isGenerating" type="primary">
                AI 生成数字人视频
              </el-button>
            </div>
          </div>
        </template>
        <template #footer>
          <div class="dialog-footer bottom-gen-btn">
            <!-- <el-button type="primary" @click="handelEditClick"> 编辑 </el-button> -->

            <el-button
              v-show="itemType !== 'Instruction'"
              @click="dialogFormVisible = false"
              type="success"
            >
              保存
            </el-button>
            <el-button @click="dialogFormVisible = false">关闭</el-button>
          </div>
        </template>
      </el-dialog>
    </teleport>
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
</style>
