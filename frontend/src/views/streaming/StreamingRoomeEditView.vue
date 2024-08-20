<script setup lang="ts">
import { useRouter } from 'vue-router'
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  roomPorductAddListRequest,
  type ProductItem,
  type RoomProductData
} from '@/api/streamingRoom'

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
              <el-checkbox v-model="item.selected" :label="item.name" size="large" border />
              <el-image style="width: 100px; height: 100px" :src="item.image" fit="contain" />
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
      <el-button type="primary" class="ml-2" @click="handelAddProductClick">新增商品</el-button>
      <div>表格</div>
      <template #footer>
        <div class="form-bottom-btn">
          <el-button type="primary" class="ml-2" @click="onSubmit">开始直播</el-button>
          <el-button type="primary" class="ml-2" @click="onSubmit">保存</el-button>
        </div>
      </template>
    </el-card>
  </div>
</template>

<style lang="scss" scoped></style>
