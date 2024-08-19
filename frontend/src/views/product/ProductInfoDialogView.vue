<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import VideoComponent from '@/components/VideoComponent.vue'
import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/preview.css'
import { genProductInstructionContentRequest } from '@/api/product'

const dialogFormVisible = ref(false)
const router = useRouter()

// 定义标题
const titleMap = { SalesDoc: '主播文案', Instruction: '说明书', DigitalHuman: '数字人视频' }
const title = ref('')
const productId = ref('')
const infoValue = ref('')
const itemType = ref('')
const showItemInfoDialog = async (itemType_: string, itemValue: string, productId_: string) => {
  title.value = titleMap[itemType_]
  itemType.value = itemType_
  productId.value = productId_
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
      <el-dialog v-model="dialogFormVisible" :title="title" width="1000" top="5vh">
        <!-- 主播文案 or 说明书 -->
        <div
          v-show="itemType === 'SalesDoc' || itemType === 'Instruction'"
          style="text-align: left"
        >
          <MdPreview editorId="preview-SalesDoc" :modelValue="infoValue" />
        </div>
        <div v-show="itemType === 'DigitalHuman'">
          <!-- 数字人视频 -->
          <VideoComponent :src="infoValue" :key="infoValue" />
        </div>

        <template #footer>
          <div class="dialog-footer">
            <el-button type="primary" @click="handelEditClick"> 编辑 </el-button>
            <el-button @click="dialogFormVisible = false">关闭</el-button>
          </div>
        </template>
      </el-dialog>
    </teleport>
  </div>
</template>

<style lang="scss" scoped></style>
