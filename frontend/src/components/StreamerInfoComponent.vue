<script lang="ts" setup>
import { nextTick, ref } from 'vue'
import { ElInput } from 'element-plus'
import type { InputInstance } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

import VideoComponent from '@/components/VideoComponent.vue'
import { type StreamerInfo } from '@/api/streamerInfo'
import FileUpload from '@/components/FileUpload.vue'

// 定义 和父组件通信的双向绑定 model
const modelSteamerInfo = defineModel({ default: {} as StreamerInfo })

// 定义组件入参
const props = defineProps({
  disableChange: {
    type: Boolean,
    default: false
  },
  optionList: {
    type: Array,
    default: () => [] as StreamerInfo[]
  }
})

// 性格操作
const inputCharacterValue = ref('')
const inputCharacterVisible = ref(false)
const InputCharacterRef = ref<InputInstance>()

const handleCharacterClose = (tag: string) => {
  // 删除性格操作
  modelSteamerInfo.value.character.splice(modelSteamerInfo.value.character.indexOf(tag), 1)
}

const showCharacterInput = () => {
  inputCharacterVisible.value = true
  nextTick(() => {
    InputCharacterRef.value!.input!.focus()
  })
}

const handleCharacterInputConfirm = () => {
  if (inputCharacterValue.value) {
    modelSteamerInfo.value.character.push(inputCharacterValue.value)
  }
  inputCharacterVisible.value = false
  inputCharacterValue.value = ''
}

const formLabelWidth = ref(120)
const labelPosition = ref('top')
</script>

<template>
  <div>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card shadow="never" v-if="optionList.length >= 1">
          <h2>选择主播</h2>
          <el-divider />
          <el-select
            v-model="modelSteamerInfo"
            placeholder="选择主播"
            size="large"
            style="width: 240px"
          >
            <el-option v-for="item in optionList" :key="item.id" :label="item.name" :value="item" />
          </el-select>
        </el-card>

        <el-card shadow="never">
          <h2>基本信息</h2>
          <el-divider />
          <el-form :label-position="labelPosition" :label-width="formLabelWidth">
            <el-form-item label="姓名">
              <el-input
                v-model="modelSteamerInfo.name"
                size="large"
                :disabled="props.disableChange"
              />
            </el-form-item>
            <el-form-item label="主播性格">
              <el-tag
                v-for="(characterItem, index) in modelSteamerInfo.character"
                :key="index"
                :closable="!props.disableChange"
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
              <el-button
                v-else
                @click="showCharacterInput"
                circle
                :icon="Plus"
                v-show="!props.disableChange"
              >
              </el-button>
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
                  v-if="modelSteamerInfo.tts_reference_audio"
                  :src="modelSteamerInfo.tts_reference_audio"
                  controls
                  style="margin-right: 20px"
                ></audio>
                <el-tag v-else size="large" type="danger"> 未找到音频 </el-tag>
                <FileUpload
                  v-show="!props.disableChange"
                  v-model="modelSteamerInfo.tts_reference_audio"
                  file-type="audio"
                />
              </div>
            </el-form-item>

            <el-form-item label="音频对应文字">
              <el-input
                v-model="modelSteamerInfo.tts_reference_sentence"
                size="large"
                :disabled="props.disableChange"
              />
            </el-form-item>

            <!-- TODO 支持用户上传自己的权重 -->
            <!-- <el-form-item label="TTS 权重" :label-width="formLabelWidth">
              <el-input
                v-model="modelSteamerInfo.tts_weight_tag"
                size="large"
                :disabled="props.disableChange"
              />
            </el-form-item> -->
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never">
          <div class="make-center">
            <!-- 数字人视频 -->
            <VideoComponent
              :src="modelSteamerInfo.base_mp4_path"
              :key="modelSteamerInfo.base_mp4_path"
              :height="600"
              :autoplay="true"
              :loop="true"
            />
          </div>
          <div class="make-center" style="margin-top: 10px">
            <FileUpload
              v-show="!props.disableChange"
              v-model="modelSteamerInfo.base_mp4_path"
              file-type="video"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style lang="scss" scoped>
.make-center {
  display: flex;
  justify-content: center;
  align-items: center;
}

.el-form-item {
  align-items: center;
}

::v-deep(.el-input__wrapper) {
  border-radius: 14px;
}

.el-card {
  margin-top: 10px;
  border-radius: 10px;
}

::v-deep(.el-form-item__label) {
  font-weight: 600;
  font-size: 15px;
}
</style>
