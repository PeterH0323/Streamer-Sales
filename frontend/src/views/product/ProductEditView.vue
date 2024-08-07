<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Picture, UploadFilled } from '@element-plus/icons-vue'
import { ref } from 'vue'

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
const productInfo = ref({})
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
          <el-button type="primary" class="ml-2">保存</el-button>
        </div>
      </template>
    </el-page-header>

    <el-card>
      <template #header>
        <!-- 步骤条 -->
        <!-- TODO 完善图标 -->
        <el-steps class="mb-4" :space="200" :active="currentStep" simple>
          <el-step title="商品图片" :icon="Picture" @click="currentStep = 0" />
          <el-step title="说明书" :icon="UploadFilled" @click="currentStep = 1" />
          <el-step title="商品信息" :icon="Picture" @click="currentStep = 2" />
          <el-step title="解说文案" :icon="Picture" @click="currentStep = 3" />
          <el-step title="数字人视频" :icon="Picture" @click="currentStep = 4" />
          <el-step title="更多配置" :icon="Picture" @click="currentStep = 5" />
        </el-steps>
      </template>
      <!-- 表单 -->
      <el-form :model="productInfo">
        <div v-show="currentStep === 0"><h1>商品图片</h1></div>
        <div v-show="currentStep === 1"><h1>说明书</h1></div>
        <div v-show="currentStep === 2"><h1>商品信息</h1></div>
        <div v-show="currentStep === 3"><h1>解说文案</h1></div>
        <div v-show="currentStep === 4"><h1>数字人视频</h1></div>
        <div v-show="currentStep === 5"><h1>更多配置</h1></div>
      </el-form>
      <template #footer>
        <div class="form-bottom-btn">
          <el-button v-show="currentStep > 0" @click="currentStep--">上一步</el-button>
          <el-button v-show="currentStep < 5" @click="currentStep++">下一步</el-button>
          <el-button v-show="currentStep === 5" type="primary">保存</el-button>
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
</style>
