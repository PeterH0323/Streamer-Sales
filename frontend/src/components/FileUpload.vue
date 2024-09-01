<script setup lang="ts">
import { ref, watchEffect } from 'vue'
import { ElMessage, type UploadProps, type UploadProgressEvent } from 'element-plus'
import { Plus, Document } from '@element-plus/icons-vue'

import { header_authorization } from '@/api/user'

// 定义组件入参
const props = defineProps({
  fileType: {
    type: String,
    default: 'image'
  }
})

// 定义 和父组件通信的双向绑定 model
const modelFilePath = defineModel({ default: '' })

// 上传文件，上传后为本机内存地址，方便加载
const fileUrl = ref('')
watchEffect(() => {
  // 用于在编辑模式下显示图片
  fileUrl.value = modelFilePath.value
})

// 是否显示进度条
const isShowProgress = ref(false)

// 文件上传成功后的 callback
const handleFileUploadSuccess: UploadProps['onSuccess'] = (response, uploadFile) => {
  // fileUrl.value = URL.createObjectURL(uploadFile.raw!) // 生成内存地址，方便加载
  fileUrl.value = response.data
  console.info(fileUrl.value)

  modelFilePath.value = response.data // 更新父组件双向绑定的值
  isShowProgress.value = false
}

// 文件上传前的校验 callback
const beforeFileUploadUpload: UploadProps['beforeUpload'] = (rawFile) => {
  console.log(rawFile)

  if (props.fileType === 'image' && rawFile.type !== 'image/png' && rawFile.type !== 'image/jpeg') {
    ElMessage.error('商品图片必须是 PNG / JPG 格式!')
    return false
  } else if (props.fileType === 'doc' && !rawFile.name.endsWith('.md')) {
    ElMessage.error('商品说明书必须是 markdown 格式!')
    return false
  } else if (props.fileType === 'video' && rawFile.type !== 'video/mp4') {
    ElMessage.error('主播视频必须是 mp4 格式!')
    return false
  } else if (props.fileType === 'audio' && rawFile.type !== 'audio/wav') {
    ElMessage.error('主播音频必须是 wav 格式!')
    return false
  }

  if (props.fileType === 'video' && rawFile.size / 1024 / 1024 > 20) {
    ElMessage.error('主播视频文件大小不能超过 20MB!')
    return false
  } else if (props.fileType !== 'video' && rawFile.size / 1024 / 1024 > 2) {
    ElMessage.error('文件大小不能超过 2MB!')
    return false
  }

  isShowProgress.value = true
  return true
}

// 文件上传成功后的 callback
const handleFileUploadFail: UploadProps['onError'] = (error: Error) => {
  ElMessage.error('上传文件失败')
  console.error(error)
  isShowProgress.value = false
}

// 文件上传进度条
const uploadPercentage = ref(0)

// 文件上传进度回调
const handleUploadProgress = (evt: UploadProgressEvent) => {
  uploadPercentage.value = Math.floor(evt.percent)
}
</script>

<template>
  <div>
    <el-progress v-show="isShowProgress" type="circle" :percentage="uploadPercentage" />
    <!-- TODO 长时间上传后端会断开？ -->
    <el-upload
      v-show="!isShowProgress"
      class="avatar-uploader"
      action="/upload/file"
      :headers="{
        Authorization: header_authorization
      }"
      method="post"
      :drag="props.fileType !== 'video' && props.fileType !== 'audio'"
      :multiple="false"
      :show-file-list="false"
      :on-success="handleFileUploadSuccess"
      :before-upload="beforeFileUploadUpload"
      :on-progress="handleUploadProgress"
      :on-error="handleFileUploadFail"
    >
      <!-- 图片 -->
      <img
        v-if="fileUrl && props.fileType === 'image'"
        :src="fileUrl"
        class="avatar"
        @load="isShowProgress = false"
      />

      <!-- markdown 文档 -->
      <el-icon
        v-else-if="fileUrl && props.fileType === 'doc'"
        :size="50"
        class="avatar-uploader-icon"
      >
        <Document />
      </el-icon>

      <!-- 视频上传 -->
      <el-button v-else-if="props.fileType === 'video' || props.fileType === 'audio'" type="danger">
        {{ fileUrl === '' ? '上传' : '更换' }}{{ props.fileType === 'video' ? '视频' : '音频' }}
      </el-button>

      <!-- 拖动上传框 -->
      <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
    </el-upload>
  </div>
</template>

<style lang="scss" scoped>
// 上传图片
.avatar-uploader .avatar {
  width: 178px;
  height: 178px;
  display: block;
}
</style>

<style lang="scss">
// 上传图片全局 css
.avatar-uploader .el-upload {
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: var(--el-transition-duration-fast);
}

.avatar-uploader .el-upload:hover {
  border-color: var(--el-color-primary);
}

.el-icon.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 178px;
  height: 178px;
  text-align: center;
}

// 进度条
.el-progress--circle {
  margin-right: 15px;
}
</style>
