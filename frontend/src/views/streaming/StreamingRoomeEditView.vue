<script setup lang="ts">
import { useRouter } from 'vue-router'
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  roomDetailRequest,
  roomPorductAddListRequest,
  type RoomProductData,
  type RoomDetailItem
} from '@/api/streamingRoom'
import type { StreamerInfo } from '@/api/streamerInfo'
import VideoComponent from '@/components/VideoComponent.vue'

const router = useRouter()

// 定义 URL ID 传参
const props = defineProps({
  roomId: {
    type: String,
    default: '0'
  }
})

const onSubmit = () => {}

// 侧边栏
const DrawerProductList = ref({} as RoomProductData)
DrawerProductList.value.product = [] // 设置默认值
DrawerProductList.value.totalSize = 0

const currentPage = ref(1)
const pageSize = ref(-1)

const getProductInfo = async () => {
  // 调用接口获取商品
  const { data } = await roomPorductAddListRequest(
    Number(props.roomId),
    currentPage.value,
    pageSize.value
  )
  if (data.code === 0) {
    if (DrawerProductList.value.product.length === 0) {
      DrawerProductList.value = data.data
    } else {
      for (let i of data.data.product) {
        // 根据返回数据继续添加商品
        DrawerProductList.value.product.push(i)
      }
      DrawerProductList.value.currentPage = data.data.currentPage
      DrawerProductList.value.pageSize = data.data.pageSize
      DrawerProductList.value.totalSize = data.data.totalSize
    }
    console.info(DrawerProductList.value)
    ElMessage.success('获取商品成功')
  }
}

// 获取商品表格信息
const RoomProductList = ref({} as RoomDetailItem)
RoomProductList.value.streamerInfo = {} as StreamerInfo

const getProductListInfo = async (currentPage: number, pageSize: number) => {
  const { data } = await roomDetailRequest(props.roomId, currentPage, pageSize)
  if (data.code === 0) {
    console.info(data.data)
    RoomProductList.value = data.data
  }
}

onMounted(() => {
  // 获取商品信息
  getProductListInfo(1, 10)
})

// 新增商品
const handelAddProductClick = async () => {
  drawerShow.value = true
  getProductInfo()
}

const drawerShow = ref(false)
function cancelClick() {
  drawerShow.value = false
}
function confirmClick() {}
</script>

<template>
  <div>
    <!-- 返回栏 -->
    <el-page-header @back="router.push({ name: 'StreamingOverview' })" title="返回">
      <template #content>
        <div class="flex items-center">
          <span class="text-large font-600 mr-3">
            {{ props.roomId ? '编辑' : '新建' }} 直播间
          </span>
        </div>
      </template>
    </el-page-header>

    <!-- 新增窗口右边抽屉弹窗 -->
    <el-drawer v-model="drawerShow" direction="rtl">
      <template #header>
        <h1>添加商品</h1>
      </template>
      <template #default>
        <div>
          <ul>
            <li v-for="item in DrawerProductList.product" :key="item.id" class="list-item">
              <el-image style="width: 100px; height: 100px" :src="item.image" fit="contain" />
              <el-checkbox v-model="item.selected" :label="item.name" size="large" border />
            </li>
          </ul>
        </div>
      </template>
      <template #footer>
        <div style="flex: auto">
          <el-button @click="cancelClick">cancel</el-button>
          <el-button type="primary" @click="confirmClick">confirm</el-button>
        </div>
      </template>
    </el-drawer>

    <el-card>
      <!-- TODO 后续主播信息做成 component -->
      <el-row :gutter="20">
        <el-col :span="12">
          <h2>主播基本信息</h2>
          <el-form-item label="姓名">
            <el-input v-model="RoomProductList.streamerInfo.name" disabled />
          </el-form-item>
          <el-form-item label="主播性格">
            <el-input v-model="RoomProductList.streamerInfo.character" disabled />
          </el-form-item>
          <el-divider />

          <h2>TTS 配置</h2>
          <el-form-item label="音频文件">
            <!-- TODO 支持新增？ -->
            <audio
              v-if="RoomProductList.streamerInfo.tts_reference_audio"
              :src="RoomProductList.streamerInfo.tts_reference_audio"
              controls
            ></audio>
            <div v-else>未找到音频</div>
          </el-form-item>

          <el-form-item label="情感">
            <el-tag type="primary"> {{ RoomProductList.streamerInfo.tts_tag }} </el-tag>
          </el-form-item>

          <el-form-item label="声音参考文字">
            <el-input v-model="RoomProductList.streamerInfo.tts_reference_sentence" />
          </el-form-item>
          <el-form-item label="TTS 权重">
            <el-input v-model="RoomProductList.streamerInfo.tts_weight_path" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <div>
            <!-- 数字人视频 -->
            <VideoComponent
              :src="RoomProductList.streamerInfo.base_mp4_path"
              :key="RoomProductList.streamerInfo.id"
            />
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card>
      <el-button type="primary" class="ml-2" @click="handelAddProductClick">新增商品</el-button>
      <el-table :data="RoomProductList.product" max-height="1000" border>
        <el-table-column prop="product_id" label="ID" align="center" width="50px" />

        <el-table-column prop="image_path" label="图片" align="center">
          <template #default="scope">
            <div style="display: flex; align-items: center">
              <!-- TODO 加上  :preview-src-list="[scope.row.image_path]"  -->
              <el-image :src="scope.row.image_path" />
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="product_name" label="名称" align="center" />
        <el-table-column prop="product_class" label="分类" align="center" />
        <el-table-column prop="heighlights" label="亮点" align="center" />
        <el-table-column prop="selling_price" label="价格" align="center" />
        <el-table-column prop="amount" label="库存" align="center" />
        <el-table-column prop="departure_place" label="发货地" align="center" />
        <el-table-column prop="delivery_company" label="快递公司" align="center" />
        <el-table-column prop="upload_date" label="上传时间" align="center" />
      </el-table>
      <template #footer>
        <el-pagination
          v-model:current-page="RoomProductList.currentPage"
          v-model:page-size="RoomProductList.pageSize"
          :page-sizes="[5, 10, 15, 20]"
          :background="true"
          layout="total, sizes, prev, pager, next, jumper"
          :total="RoomProductList.totalSize || 0"
          @size-change="(pageSize: number) => getProductListInfo(1, pageSize)"
          @current-change="
            (currentPage: number) => getProductListInfo(currentPage, RoomProductList.pageSize)
          "
        />
        <div class="form-bottom-btn">
          <el-button type="primary" class="ml-2" @click="onSubmit">开始直播</el-button>
          <el-button type="primary" class="ml-2" @click="onSubmit">保存</el-button>
        </div>
      </template>
    </el-card>
  </div>
</template>

<style lang="scss" scoped></style>
