<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Picture } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus/es'

import FileUpload from '@/components/FileUpload.vue'

import {
  type ProductListItem,
  getProductByIdRequest,
  productCreadeOrEditRequest
} from '@/api/product'

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
    ElMessage.success(`${statusInof}成功!`)
    router.push({ name: 'Product' })
  } else {
    ElMessage.error(`${statusInof}失败, ${data.message}`)
    throw new Error(`${statusInof}失败, ${data.message}`)
  }
}

onMounted(async () => {
  // 获取商品信息
  if (props.productId) {
    const { data } = await getProductByIdRequest(props.productId)
    if (data.code === 0) {
      productInfo.value = data.data
      ElMessage.infor('获取商品信息成功')
    } else {
      ElMessage.error(data.message)
    }
  }
})
</script>

<template>
  <div>
    <!-- 返回栏 -->
    <el-page-header @back="router.push({ name: 'ProductList' })" title="返回">
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
      </el-form>

      <template #footer>
        <div class="form-bottom-btn">
          <el-button v-show="currentStep > 0" @click="currentStep--">上一步</el-button>
          <el-button v-show="currentStep < 1" @click="currentStep++">下一步</el-button>
          <el-button v-show="currentStep === 1" type="primary" @click="onSubmit">保存</el-button>
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
