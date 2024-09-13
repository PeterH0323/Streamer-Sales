<script setup lang="ts">
import { useRouter } from 'vue-router'
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { Check, Warning, Edit } from '@element-plus/icons-vue'
import {
  roomDetailRequest,
  roomPorductAddListRequest,
  RoomCreadeOrEditRequest,
  type RoomProductData,
  type RoomDetailItem,
  type StreamingRoomStatusItem,
  type StreamingRoomProductList,
  onAirRoomStartRequest
} from '@/api/streamingRoom'
import type { StreamerInfo } from '@/api/streamerInfo'
import InfoDialogComponents from '@/components/InfoDialogComponents.vue'
import { streamerInfoListRequest } from '@/api/streamerInfo'
import StreamerInfoComponent from '@/components/StreamerInfoComponent.vue'
import { AxiosError } from 'axios'

const router = useRouter()

// 定义 URL ID 传参
const props = defineProps({
  roomId: {
    type: String,
    default: '0'
  }
})

// 信息弹窗显示标识
const ShowItemInfo = ref()

// 侧边栏
const DrawerProductList = ref({} as RoomProductData)
DrawerProductList.value.product_list = [] // 设置默认值
DrawerProductList.value.totalSize = 0

const currentPage = ref(1)
const pageSize = ref(-1)

const getProductInfo = async () => {
  try {
    // 调用接口获取商品缩略图用于抽屉
    const { data } = await roomPorductAddListRequest(
      RoomDetailInfo.value.room_id,
      currentPage.value,
      pageSize.value
    )
    if (data.code === 0) {
      DrawerProductList.value = data.data

      // 分页获取
      // if (DrawerProductList.value.product.length === 0) {
      //   DrawerProductList.value = data.data
      // } else {
      //   for (let i of data.data.product) {
      //     // 根据返回数据继续添加商品
      //     DrawerProductList.value.product.push(i)
      //   }
      //   DrawerProductList.value.currentPage = data.data.currentPage
      //   DrawerProductList.value.pageSize = data.data.pageSize
      //   DrawerProductList.value.totalSize = data.data.totalSize
      // }
      console.info(DrawerProductList.value)
      ElMessage.success('获取商品成功')
    } else {
      ElMessage.error('获取商品失败：' + data.message)
    }
  } catch (error: unknown) {
    if (error instanceof AxiosError) {
      ElMessage.error('获取商品失败：' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
  }
}

// 获取商品表格信息
const RoomDetailInfo = ref({} as RoomDetailItem)
RoomDetailInfo.value.streamer_info = {} as StreamerInfo
RoomDetailInfo.value.streamer_info.streamer_id = 0
RoomDetailInfo.value.pageSize = 10
RoomDetailInfo.value.room_id = Number(props.roomId)
RoomDetailInfo.value.product_list = [] as StreamingRoomProductList[]
RoomDetailInfo.value.status = {} as StreamingRoomStatusItem
const EditProductList = ref({} as RoomDetailItem)

const getProductListInfo = async (currentPage: number, pageSize: number) => {
  if (RoomDetailInfo.value.room_id === 0) {
    return
  }

  try {
    const { data } = await roomDetailRequest(
      String(RoomDetailInfo.value.room_id),
      currentPage,
      pageSize
    )
    if (data.code === 0) {
      console.info(data.data)
      RoomDetailInfo.value = data.data
    } else {
      ElMessage.error('获取直播间详情失败' + data.message)
    }
  } catch (error: unknown) {
    if (error instanceof AxiosError) {
      ElMessage.error('获取直播间详情失败' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
  }
}

// 获取主播信息
const streamerNameOptions = ref([] as StreamerInfo[])

const getSteramerInfo = async () => {
  try {
    // 获取主播信息
    const { data } = await streamerInfoListRequest()
    if (data.code === 0) {
      streamerNameOptions.value = data.data
      ElMessage.success('获取主播信息成功')
    } else {
      ElMessage.error('获取主播信息失败' + data.message)
    }
  } catch (error: unknown) {
    if (error instanceof AxiosError) {
      ElMessage.error('获取主播信息失败' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
  }
}

onMounted(() => {
  // 获取商品表格信息
  getProductListInfo(1, 10)

  // 获取主播信息
  getSteramerInfo()
})

// 新增商品
const handelAddProductClick = async () => {
  // 先保存商品，防止文案 or 数字人视频丢失
  // onSubmit()

  drawerShow.value = true
  getProductInfo()
}

const drawerShow = ref(false)
function cancelClick() {
  drawerShow.value = false
}

async function confirmClick() {
  EditProductList.value = RoomDetailInfo.value
  EditProductList.value.product_list = DrawerProductList.value.product_list
  EditProductList.value.streamer_id = RoomDetailInfo.value.streamer_info.streamer_id

  console.log(EditProductList.value)
  try {
    // 调用接口更新选择的商品
    const { data } = await RoomCreadeOrEditRequest(EditProductList.value)
    if (data.code === 0) {
      // 新建会返回直播间后台保存 ID
      RoomDetailInfo.value.room_id = data.data
      ElMessage.success('操作成功')
    } else {
      ElMessage.error('操作失败' + data.message)
    }
  } catch (error: unknown) {
    if (error instanceof AxiosError) {
      ElMessage.error('操作失败' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
  }

  drawerShow.value = false

  // 重新获取
  getProductListInfo(1, 10)
}

// 保存
const onSubmit = async () => {
  try {
    // 调用接口保存商品
    await RoomCreadeOrEditRequest(RoomDetailInfo.value)
    ElMessage.success('保存成功')
  } catch (error: unknown) {
    if (error instanceof AxiosError) {
      ElMessage.error('保存失败' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
  }
}

const handelOnAirClick = async () => {
  for (const entry of RoomDetailInfo.value.product_list) {
    if (entry.start_video === '') {
      ElMessage.error('必须将所有的商品都生成数字人视频才可以进行开播')
      return false
    }
  }

  // 保存商品信息
  await onSubmit()

  if (RoomDetailInfo.value.status.live_status !== 1) {
    try {
      // 调用接口执行开播
      await onAirRoomStartRequest(RoomDetailInfo.value.room_id)
      ElMessage.success('开播成功')
    } catch (error: unknown) {
      if (error instanceof AxiosError) {
        ElMessage.error('开播成功' + error.message)
      } else {
        ElMessage.error('未知错误：' + error)
      }
    }
  }

  router.push({ name: 'StreamingOnAir', params: { roomId: String(RoomDetailInfo.value.room_id) } })
}

// 每个物品的点击按钮
const handelControlClick = (
  titleName: string,
  itemType: string,
  itemValue: string,
  productId: number,
  streamerId: number,
  salesDoc: string
) => {
  console.info(itemType)
  console.info(itemValue)
  ShowItemInfo.value.showItemInfoDialog(
    titleName,
    itemType,
    itemValue,
    productId,
    streamerId,
    salesDoc
  )
}
</script>

<template>
  <div>
    <!-- 返回栏 -->
    <el-page-header @back="router.push({ name: 'StreamingOverview' })" title="返回">
      <template #content>
        <div class="flex items-center">
          <span class="text-large font-600 mr-3">
            {{ RoomDetailInfo.room_id !== 0 ? '编辑' : '新建' }} 直播间
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
          <ul class="product-list">
            <li
              v-for="item in DrawerProductList.product_list"
              :key="item.product_id"
              style="margin-bottom: 10px"
            >
              <el-checkbox-button
                v-model="item.selected"
                size="large"
                border
                class="item-checkbox-button"
              >
                <el-card shadow="never">
                  <el-row :gutter="0">
                    <el-col :span="6">
                      <el-image
                        style="width: 80px; height: 80px"
                        :src="item.product_info.image_path"
                        fit="contain"
                      />
                    </el-col>
                    <el-col :span="18">
                      <div class="product-info">
                        <p class="title">{{ item.product_info.product_name }}</p>
                        <p class="content">{{ item.product_info.heighlights }}</p>
                        <p class="price">￥{{ item.product_info.selling_price }}</p>
                      </div>
                    </el-col>
                  </el-row>
                </el-card>
              </el-checkbox-button>
            </li>
          </ul>
        </div>
      </template>
      <template #footer>
        <div style="flex: auto">
          <el-button @click="cancelClick">取消</el-button>
          <el-button type="primary" @click="confirmClick">确认</el-button>
        </div>
      </template>
    </el-drawer>

    <el-card shadow="never" style="margin-top: 10px">
      <h2>直播间名称</h2>
      <el-divider />

      <el-input v-model="RoomDetailInfo.name" size="large" />
    </el-card>

    <el-card shadow="never">
      <StreamerInfoComponent
        :disable-change="true"
        v-model="RoomDetailInfo.streamer_info"
        :optionList="streamerNameOptions"
      />
    </el-card>

    <el-card shadow="never">
      <el-button
        type="primary"
        style="margin-bottom: 15px"
        @click="handelAddProductClick"
        size="large"
        round
      >
        <el-icon style="margin-right: 5px">
          <Edit />
        </el-icon>
        增删商品
      </el-button>

      <!-- TODO 商品表格可以做成 component 组件 -->
      <el-table :data="RoomDetailInfo.product_list" max-height="1000" border>
        <el-table-column prop="product_info.product_id" label="ID" align="center" width="50px" />

        <el-table-column prop="product_info.image_path" label="图片" align="center">
          <template #default="scope">
            <div style="display: flex; align-items: center">
              <!-- TODO 加上  :preview-src-list="[scope.row.image_path]"  -->
              <el-image :src="scope.row.product_info.image_path" />
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="product_info.product_name" label="名称" align="center" />
        <el-table-column prop="product_info.product_class" label="分类" align="center" />
        <el-table-column prop="product_info.heighlights" label="亮点" align="center" />
        <el-table-column prop="product_info.selling_price" label="价格" align="center" />
        <el-table-column prop="product_info.amount" label="库存" align="center" />
        <el-table-column prop="product_info.departure_place" label="发货地" align="center" />
        <el-table-column prop="product_info.delivery_company" label="快递公司" align="center" />
        <el-table-column prop="product_info.upload_date" label="上传时间" align="center" />
        <el-table-column label="操作" v-slot="{ row }" align="center" width="400px">
          <div class="control-item">
            <el-button
              size="small"
              :type="row.product_info.instruction !== '' ? 'success' : 'warning'"
              :icon="row.product_info.instruction !== '' ? Check : Warning"
              @click="
                handelControlClick(
                  row.product_info.product_name,
                  'Instruction',
                  row.product_info.instruction,
                  row.product_id,
                  RoomDetailInfo.streamer_info.streamer_id,
                  row.sales_doc
                )
              "
            >
              说明书
            </el-button>

            <el-button
              size="small"
              v-model="row.sales_doc"
              :type="row.sales_doc !== '' ? 'success' : 'warning'"
              :icon="row.sales_doc !== '' ? Check : Warning"
              @click="
                handelControlClick(
                  row.product_info.product_name,
                  'SalesDoc',
                  row.sales_doc,
                  row.product_id,
                  RoomDetailInfo.streamer_info.streamer_id,
                  row.sales_doc
                )
              "
            >
              解说文案
            </el-button>

            <el-button
              size="small"
              v-model="row.start_video"
              :type="row.start_video !== '' ? 'success' : 'warning'"
              :icon="row.start_video !== '' ? Check : Warning"
              @click="
                handelControlClick(
                  row.product_info.product_name,
                  'DigitalHuman',
                  row.start_video,
                  row.product_id,
                  RoomDetailInfo.streamer_info.streamer_id,
                  row.sales_doc
                )
              "
            >
              数字人视频
            </el-button>

            <el-button
              size="small"
              @click="router.push({ name: 'ProductEdit', params: { productId: row.product_id } })"
            >
              编辑
            </el-button>
          </div>
        </el-table-column>
      </el-table>

      <!-- 信息弹窗 -->
      <InfoDialogComponents ref="ShowItemInfo" v-model="RoomDetailInfo.product_list" />

      <template #footer>
        <div class="bottom-item">
          <el-pagination
            v-model:current-page="RoomDetailInfo.currentPage"
            v-model:page-size="RoomDetailInfo.pageSize"
            :page-sizes="[5, 10, 15, 20]"
            :background="true"
            layout="total, sizes, prev, pager, next, jumper"
            :total="RoomDetailInfo.totalSize || 0"
            @size-change="(pageSize: number) => getProductListInfo(1, pageSize)"
            @current-change="
              (currentPage: number) => getProductListInfo(currentPage, RoomDetailInfo.pageSize)
            "
          />
          <div>
            <el-button
              type="success"
              @click="handelOnAirClick"
              :disable="RoomDetailInfo.room_id === 0"
            >
              {{ RoomDetailInfo.status.live_status === 1 ? '进入' : '开始' }}直播</el-button
            >
            <el-button
              type="primary"
              @click="onSubmit"
              :disabled="RoomDetailInfo.product_list.length === 0"
              >保存</el-button
            >
          </div>
        </div>
      </template>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.bottom-item {
  margin-top: 10px; // 距离上面的控件有一定的距离
  display: flex;
  justify-content: space-between; // 将两个 div 放置在页面的两侧
  align-items: center;
}

.product-list {
  padding-left: 0; /* 去掉默认的缩进 */
  margin: 0; /* 去掉默认的外边距 */
  list-style-type: none; /* 去掉列表项前的默认圆点 */

  .ul {
    list-style-type: none;
    padding-left: 0; /* 去掉默认的缩进 */
  }
}

.el-card {
  margin-bottom: 20px;
  padding: 20px;
  border-radius: 20px;
}

::v-deep(.el-input__wrapper) {
  border-radius: 14px;
}

.item-checkbox-button {
  ::v-deep(.el-checkbox-button__inner) {
    border-radius: 20px; /* 设置 checkbox button 圆角大小 */
    line-height: 0;
    text-align: left;
    padding: 5px 5px;
  }

  .el-card__body {
    padding: 0px !important;
  }

  .el-card {
    margin: 0px;
    width: 450px;
    height: 120px;
    padding: 0px;

    .product-info {
      display: flex;
      flex-direction: column; /* 将子元素垂直排列 */
      margin-left: 10px;

      .title {
        font-size: 14px;
        font-weight: 600;
      }

      .content {
        font-size: 12px;
        color: #b1b3b8;
      }

      .price {
        font-size: 12px;
        color: #fda100;
      }
    }
  }
}
</style>
