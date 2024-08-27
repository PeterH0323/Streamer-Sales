<script setup lang="ts">
import { ref } from 'vue'
import VideoComponent from '@/components/VideoComponent.vue'

import { streamerDetailInfoRequest, type StreamerInfo } from '@/api/streamerInfo'

const dialogInfoVisible = ref(false)

// 定义标题
const steamerInfo = ref({} as StreamerInfo)
const showItemInfoDialog = async (streamerId: number) => {
  console.log(streamerId)
  dialogInfoVisible.value = true

  // 请求接口获取说明书数据
  const { data } = await streamerDetailInfoRequest(streamerId)
  if (data.code === 0) {
    steamerInfo.value = data.data[0]
  } else {
    // ElMessage.error()
  }
}

const formLabelWidth = ref(120)

const handelSaveClick = () => {}

defineExpose({ showItemInfoDialog })
</script>

<template>
  <div class="dialog-container">
    <el-dialog
      v-model="dialogInfoVisible"
      title="主播详情"
      width="80%"
      destroy-on-close
      class="my-custom-dialog"
    >
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card shadow="never">
            <h2>基本信息</h2>
            <el-form-item label="姓名" :label-width="formLabelWidth">
              <el-input v-model="steamerInfo.name" disabled size="large" />
            </el-form-item>
            <el-form-item label="主播性格" :label-width="formLabelWidth">
              <el-input v-model="steamerInfo.character" disabled size="large" />
            </el-form-item>
          </el-card>

          <el-card shadow="never">
            <h2>TTS 配置</h2>
            <el-form-item label="音频文件" :label-width="formLabelWidth">
              <!-- TODO 支持新增？ -->
              <audio
                v-if="steamerInfo.tts_reference_audio"
                :src="steamerInfo.tts_reference_audio"
                controls
              ></audio>
              <div v-else>未找到音频</div>
            </el-form-item>

            <el-form-item label="情感" :label-width="formLabelWidth">
              <el-tag type="primary"> {{ steamerInfo.tts_tag }} </el-tag>
            </el-form-item>

            <el-form-item label="声音参考文字" :label-width="formLabelWidth">
              <el-input v-model="steamerInfo.tts_reference_sentence" size="large" />
            </el-form-item>
            <el-form-item label="TTS 权重" :label-width="formLabelWidth">
              <el-input v-model="steamerInfo.tts_weight_tag" size="large" />
            </el-form-item>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card shadow="never">
            <div class="video-container">
              <!-- 数字人视频 -->
              <VideoComponent
                :src="steamerInfo.base_mp4_path"
                :key="steamerInfo.id"
                :height="600"
                :autoplay="true"
                :loop="true"
              />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="handelSaveClick"> 保存 </el-button>
          <el-button @click="dialogInfoVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.video-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

::v-deep(.el-input__wrapper) {
  border-radius: 14px;
}

.el-card {
  margin-top: 10px;
  border-radius: 10px;
}

// 使用 ::v-deep 选择器来覆盖 el-dialog 的默认样式。
::v-deep(.el-dialog) {
  border-radius: 10px;
  padding: 20px;

  --el-dialog-bg-color: #f7f8fa;
  --el-dialog-title-font-size: 24px;
}

.el-form-item {
  align-items: center;
}
::v-deep(.el-form-item__label) {
  font-weight: 600;
  font-size: 15px;
}
</style>
