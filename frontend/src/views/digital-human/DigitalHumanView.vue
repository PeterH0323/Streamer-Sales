<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { ElMessage } from 'element-plus/es'

import { streamerInfoListRequest, type StreamerInfo } from '@/api/streamerInfo'

import showItemInfoDialog from '@/views/digital-human/DigitalHumanEditDialogView.vue'

// 获取主播信息
const streamerNameOptions = ref([] as StreamerInfo[])

onMounted(async () => {
  // 获取主播信息
  const { data } = await streamerInfoListRequest()
  if (data.code === 0) {
    streamerNameOptions.value = data.data
    ElMessage.success('获取主播信息成功')
  }
})

const chunkArray = (array: StreamerInfo[], chunkSize: number) => {
  // 切割每 n 个为一行（即一个数组），方便后续进行 v-for 遍历
  const result = []
  for (let i = 0; i < array.length; i += chunkSize) {
    result.push(array.slice(i, i + chunkSize))
  }
  return result
}

const chunkedArray = computed(() => chunkArray(streamerNameOptions.value, 2))

// 信息弹窗显示标识
const ShowItemInfo = ref()
</script>

<template>
  <div>
    <div v-for="(row, rowIndex) in chunkedArray" :key="rowIndex" class="row">
      <el-row :gutter="20">
        <el-col v-for="(item, index) in row" :key="index" :span="8">
          <el-card style="max-width: 480px">
            <img :src="item.poster_image" style="width: 100%" />
            <div>名称：{{ item.name }}</div>
            <div>性格：{{ item.character }}</div>
            <div class="bottom-button">
              <el-button type="primary" plain @click="ShowItemInfo.showItemInfoDialog(item.id)">
                详情
              </el-button>
              <el-button type="danger" plain> 删除 </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <showItemInfoDialog ref="ShowItemInfo" />
  </div>
</template>

<style lang="scss" scoped>
.row {
  margin-bottom: 20px;
}

.bottom-button {
  margin-top: 10px; // 距离上面的控件有一定的距离
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
