<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { ElInput, ElMessage } from 'element-plus'
import type { InputInstance } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

import VideoComponent from '@/components/VideoComponent.vue'
import {
  streamerDetailInfoRequest,
  streamerEditDetailRequest,
  type StreamerInfo
} from '@/api/streamerInfo'
import FileUpload from '@/components/FileUpload.vue'

const dialogInfoVisible = ref(false)

// 定义标题
const steamerInfo = ref({} as StreamerInfo)
const showItemInfoDialog = async (streamerId: number) => {
  console.log(streamerId)
  dialogInfoVisible.value = true

  // 请求接口获取主播数据
  const { data } = await streamerDetailInfoRequest(streamerId)
  if (data.code === 0) {
    steamerInfo.value = data.data[0]
    characterList.value = steamerInfo.value.character.split('、')
  } else {
    // ElMessage.error()
  }
}

// 性格操作
const characterList = ref<string[]>([])
const inputCharacterValue = ref('')
const inputCharacterVisible = ref(false)
const InputCharacterRef = ref<InputInstance>()

const updateCharacterToStraing = () => {
  steamerInfo.value.character = ''
  for (var charString of characterList.value) {
    steamerInfo.value.character += charString + '、'
  }
  steamerInfo.value.character = steamerInfo.value.character.slice(0, -1) // 去掉最后一个 、
  console.log(steamerInfo.value.character)
}

const handleCharacterClose = (tag: string) => {
  // 删除性格操作
  characterList.value.splice(characterList.value.indexOf(tag), 1)
  updateCharacterToStraing()
}

const showCharacterInput = () => {
  inputCharacterVisible.value = true
  nextTick(() => {
    InputCharacterRef.value!.input!.focus()
  })
}

const handleCharacterInputConfirm = () => {
  if (inputCharacterValue.value) {
    characterList.value.push(inputCharacterValue.value)
    updateCharacterToStraing()
  }
  inputCharacterVisible.value = false
  inputCharacterValue.value = ''
}

const formLabelWidth = ref(120)
const labelPosition = ref('top')

const handelSaveClick = async () => {
  const { data } = await streamerEditDetailRequest(steamerInfo.value)

  if (data.code === 0) {
    steamerInfo.value.id = data.data
    ElMessage.success('保存成功')
  }
  else {
    ElMessage.error(data.message)
  }
}

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
            <el-divider />
            <el-form :label-position="labelPosition" :label-width="formLabelWidth">
              <el-form-item label="姓名">
                <el-input v-model="steamerInfo.name" size="large" />
              </el-form-item>
              <el-form-item label="主播性格">
                <el-tag
                  v-for="(characterItem, index) in characterList"
                  :key="index"
                  closable
                  :disable-transitions="false"
                  @close="handleCharacterClose(characterItem)"
                  round
                  size="large"
                  style="margin: 3px"
                >
                  {{ characterItem }}
                </el-tag>

                <el-input
                  v-if="inputCharacterVisible"
                  ref="InputCharacterRef"
                  v-model="inputCharacterValue"
                  class="w-20"
                  @keyup.enter="handleCharacterInputConfirm"
                  @blur="handleCharacterInputConfirm"
                  size="large"
                />
                <el-button v-else @click="showCharacterInput" circle :icon="Plus"> </el-button>
              </el-form-item>
            </el-form>
          </el-card>

          <el-card shadow="never">
            <h2>TTS 配置</h2>
            <el-divider />
            <el-form :label-position="labelPosition" :label-width="formLabelWidth">
              <el-form-item label="音频文件">
                <div class="make-center">
                  <audio
                    v-if="steamerInfo.tts_reference_audio"
                    :src="steamerInfo.tts_reference_audio"
                    controls
                    style="margin-right: 20px"
                  ></audio>
                  <el-tag v-else size="large" type="danger"> 未找到音频 </el-tag>
                  <FileUpload v-model="steamerInfo.tts_reference_audio" file-type="audio" />
                </div>
              </el-form-item>

              <el-form-item label="情感">
                <el-tag type="primary"> {{ steamerInfo.tts_tag }} </el-tag>
              </el-form-item>

              <el-form-item label="音频对应文字">
                <el-input v-model="steamerInfo.tts_reference_sentence" size="large" />
              </el-form-item>
              <el-form-item label="TTS 权重" :label-width="formLabelWidth">
                <el-input v-model="steamerInfo.tts_weight_tag" size="large" />
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card shadow="never">
            <div class="make-center">
              <!-- 数字人视频 -->
              <VideoComponent
                :src="steamerInfo.base_mp4_path"
                :key="steamerInfo.base_mp4_path"
                :height="600"
                :autoplay="true"
                :loop="true"
              />
            </div>
            <div class="make-center" style="margin-top: 10px">
              <FileUpload v-model="steamerInfo.base_mp4_path" file-type="video" />
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
.make-center {
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
