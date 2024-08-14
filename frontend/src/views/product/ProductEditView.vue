<script setup lang="ts">
import { useRouter } from 'vue-router'
import { onMounted, ref } from 'vue'

import { Picture } from '@element-plus/icons-vue'

import FileUpload from '@/components/FileUpload.vue'
import VideoComponent from '@/components/VideoComponent.vue'

import { streamerInfoListRequest } from '@/api/streamerInfo'
import { genSalesDocRequest } from '@/api/llm'

import {
  type ProductListItem,
  type StreamerInfo,
  productCreadeOrEditRequest,
  getProductByIdRequest
} from '@/api/product'
import { ElMessage } from 'element-plus/es'

const router = useRouter()

// 定义 URL ID 传参
const props = defineProps({
  productId: {
    type: String,
    default: ''
  }
})

// 步骤条ID
const currentStep = ref(0)

// 商品信息
const productInfo = ref({} as ProductListItem)

// 表单提交
const onSubmit = async () => {
  const statusInof = props.productId ? '编辑商品' : '新建商品'

  const { data } = await productCreadeOrEditRequest(productInfo.value)
  if (data.code === 0) {
    ElMessage.info(`${statusInof}成功!`)
    router.push({ name: 'Product' })
  } else {
    ElMessage.error(`${statusInof}失败, ${data.message}`)
    throw new Error(`${statusInof}失败, ${data.message}`)
  }
}

// 生成数据人视频
const getDigitalHumanVideo = async () => {
  // const res = await productGenDigitalHuamnVideoRequest(productInfo.value.sales_doc)
  productInfo.value.digital_human_video =
    'https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-360p.mp4'
}

// 是否正在生成文案标识
const isGeneratingDoc = ref(false)
// 生成解说文案
const handleGenSalesDocClick = async () => {
  isGeneratingDoc.value = true
  ElMessage.success('正在生成，请稍候')
  const { data } = await genSalesDocRequest(productInfo.value, streamInfoSelected.value)
  console.log(data)
  if (data.code === 0) {
    productInfo.value.sales_doc = data.data
    ElMessage.success('生成文案成功')
  }
  isGeneratingDoc.value = false
}

// 获取主播信息
const streamerNameOptions = ref([] as StreamerInfo[])

const streamInfoSelected = ref({} as StreamerInfo)

onMounted(async () => {
  // 获取主播信息
  const { data } = await streamerInfoListRequest()
  if (data.code === 0) {
    streamerNameOptions.value = data.data
    ElMessage.success('获取主播信息成功')
  }

  if (props.productId) {
    //编辑情况下调取接口获取对应商品信息
    const { data } = await getProductByIdRequest(props.productId)
    console.log(data)
    if (data.state === 0) {
      productInfo.value = data.product
      streamInfoSelected.value.id = productInfo.value.streamer_id
      ElMessage.success('获取数据成功')
    }
  }
})
</script>

<template>
  <div>
    <!-- 返回栏 -->
    <el-page-header @back="router.go(-1)" title="返回">
      <template #content>
        <div class="flex items-center">
          <span class="text-large font-600 mr-3">
            {{ props.productId ? '编辑' : '新建' }}商品
          </span>
        </div>
      </template>
      <template #extra>
        <div class="flex items-center">
          <el-button type="primary" class="ml-2" @click="onSubmit">保存</el-button>
        </div>
      </template>
    </el-page-header>

    <el-card>
      <template #header>
        <!-- 步骤条 -->
        <!-- TODO 完善图标 -->
        <el-steps class="mb-4" :space="200" :active="currentStep" simple>
          <el-step title="头图 & 说明书" :icon="Picture" @click="currentStep = 0" />
          <el-step title="商品信息" :icon="Picture" @click="currentStep = 1" />
          <el-step title="主播 & 文案" :icon="Picture" @click="currentStep = 2" />
          <el-step title="数字人视频" :icon="Picture" @click="currentStep = 3" />
        </el-steps>
      </template>
      <!-- 表单 -->
      <!-- label-width 用于对其 el-form-item 标签 -->
      <el-form :model="productInfo" label-width="120" size="large">
        <div v-show="currentStep === 0">
          <!-- 商品头图 & 说明书-->
          <el-form-item label="商品图片">
            <FileUpload v-model="productInfo.image_path" file-type="image" />
          </el-form-item>

          <el-form-item label="商品说明书">
            <FileUpload v-model="productInfo.instruction" file-type="doc" />
          </el-form-item>
        </div>

        <div v-show="currentStep === 1">
          <!-- 商品信息 -->

          <el-form-item label="商品名称">
            <el-input v-model="productInfo.product_name" maxlength="50" show-word-limit />
          </el-form-item>
          <el-form-item label="商品分类">
            <!-- TODO 改为下拉框 -->
            <el-input v-model="productInfo.product_class" />
          </el-form-item>
          <el-form-item label="商品亮点">
            <el-input v-model="productInfo.heighlights" maxlength="200" show-word-limit />
          </el-form-item>
          <el-form-item label="价格">
            <el-input-number
              v-model="productInfo.selling_price"
              :min="0.01"
              :precision="2"
              :step="0.1"
              :max="99999"
              size="large"
            />
          </el-form-item>
          <el-form-item label="库存数量">
            <el-input-number
              v-model="productInfo.amount"
              :min="0"
              :step="50"
              :max="99999"
              size="large"
            />
          </el-form-item>
          <el-form-item label="发货地">
            <!-- TODO 改为下拉框选择 ? -->
            <el-input v-model="productInfo.departure_place" maxlength="100" show-word-limit />
          </el-form-item>
          <el-form-item label="快递公司">
            <!-- TODO 改为下拉框 -->
            <el-input v-model="productInfo.delivery_company" maxlength="50" show-word-limit />
          </el-form-item>
          <div class="bottom-gen-btn">
            <el-button type="success"> AI 生成 </el-button>
          </div>
        </div>

        <div v-show="currentStep === 2">
          <!-- 解说文案 -->
          <el-form-item label="选择主播">
            <el-select
              v-model="streamInfoSelected"
              placeholder="选择主播"
              size="large"
              style="width: 240px"
              @change="productInfo.streamer_id = streamInfoSelected.id"
            >
              <el-option
                v-for="item in streamerNameOptions"
                :key="item.id"
                :label="item.name"
                :value="item"
              />
              <!-- TODO hover 的时候显示头图？使用一个概览筐 or 弹窗加载缩略图然后让客户选择？ -->
            </el-select>
          </el-form-item>
          <el-form-item label="主播形象">
            <el-image
              style="width: 100px; height: 100px"
              :src="streamInfoSelected.imageUrl"
              :zoom-rate="1.2"
              :max-scale="7"
              :min-scale="0.2"
              :preview-src-list="[streamInfoSelected.imageUrl]"
              fit="scale-down"
            />
          </el-form-item>
          <el-form-item label="主播性格">
            <el-input v-model="streamInfoSelected.character" />
          </el-form-item>

          <el-form-item label="解说文案">
            <el-input
              type="textarea"
              v-model="productInfo.sales_doc"
              maxlength="2000"
              :autosize="{ minRows: 20 }"
              show-word-limit
            />
          </el-form-item>
          <div class="bottom-gen-btn">
            <el-button @click="handleGenSalesDocClick" :loading="isGeneratingDoc" type="success">
              AI 生成
            </el-button>
          </div>
        </div>
        <div v-show="currentStep === 3">
          <!-- 数字人视频 -->
          <div clas="video-container">
            <VideoComponent
              :src="productInfo.digital_human_video"
              :key="productInfo.digital_human_video"
            />
          </div>
          <div class="bottom-gen-btn">
            <el-button @click="getDigitalHumanVideo" type="success"> AI 生成数字人视频 </el-button>
          </div>
        </div>
      </el-form>

      <template #footer>
        <div class="form-bottom-btn">
          <el-button v-show="currentStep > 0" @click="currentStep--">上一步</el-button>
          <el-button v-show="currentStep < 3" @click="currentStep++">下一步</el-button>
          <el-button v-show="currentStep === 3" type="primary" @click="onSubmit">保存</el-button>
        </div>
      </template>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.el-card {
  width: auto;
  margin-top: 20px;
}

// 步骤条
.el-step {
  cursor: pointer; // 鼠标移动过去显示鼠标变成 pointer 手指
}

// 底部按钮
.form-bottom-btn {
  display: flex;
  justify-content: center;
  align-items: center;
}

// 中间表单控件
.el-form {
  padding: 0px 180px 0px 100px; // 从上开始顺时针四个放心
}

// 视频控件
.video-container {
  // margin-left: 1000px;
}

// 每个表单底部 AI 生成按钮
.bottom-gen-btn {
  margin-top: 15px;
  margin-left: 70px;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
