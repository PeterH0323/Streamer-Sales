<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Delete, Edit } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import InfoDialogComponents from '@/components/InfoDialogComponents.vue'

import {
  productListRequest,
  deleteProductByIdRequest,
  type ProductListType,
  type ProductData
} from '@/api/product'
import { AxiosError } from 'axios'

const router = useRouter()

// 信息弹窗显示标识
const ShowItemInfo = ref()

// 加载框
const tableLoading = ref(true)

// 查询 - 条件
const queryCondition = ref<ProductListType>({
  currentPage: 1,
  pageSize: 10
} as ProductListType)

// 查询 - 结果
const queriedResult = ref<ProductData>({} as ProductData)

// 查询 - 方法
const getProductList = async (params: ProductListType = {}) => {
  tableLoading.value = true

  Object.assign(queryCondition.value, params) // 用于外部灵活使用，传参的字典更新

  try {
    const { data } = await productListRequest(queryCondition.value)
    tableLoading.value = false

    if (data.code === 0) {
      queriedResult.value = data.data
    } else {
      ElMessage.error('商品接口错误')
      throw new Error('商品接口错误')
    }
  } catch (error: unknown) {
    if (error instanceof AxiosError) {
      ElMessage.error('商品接口失败: ' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
  }
}

onMounted(() => {
  // 获取商品信息
  getProductList()
})

const isDelecting = ref(false)
const DeleteProduct = async (id: number, productName: string) => {
  ElMessageBox.confirm(`确定要删除 "${productName}" 吗？`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
    showClose: false
  })
    .then(async () => {
      ElMessage.success(`正在删除 ${productName}，请稍候`)
      isDelecting.value = true
      const { data } = await deleteProductByIdRequest(id)
      if (data.code === 0) {
        ElMessage.success('删除成功')
        getProductList()
      } else {
        ElMessage.error('删除失败')
      }
      isDelecting.value = false
    })
    .catch(() => {
      // ElMessage({
      //   type: 'info',
      //   message: 'Input canceled'
      // })
    })
}
</script>

<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <!-- 头部 -->
        <div class="card-header">
          <div>
            <el-form :inline="true" :model="queriedResult.product_list">
              <el-form-item label="搜索">
                <el-input
                  style="width: 240px"
                  v-model="queryCondition.productName"
                  placeholder="商品名称"
                  clearable
                />
              </el-form-item>
              <!-- <el-form-item label="分类">
                <el-select v-model="queriedResult.class" placeholder="">
                  <el-option label="全部" value="" />
                  <el-option label="电子" value="电子" />
                </el-select>
              </el-form-item> -->
              <el-form-item>
                <el-button type="primary" @click="() => getProductList({ currentPage: 1 })">
                  查询
                </el-button>
              </el-form-item>
            </el-form>
          </div>
          <div>
            <!-- 添加商品 -->
            <el-button type="primary" @click="router.push({ name: 'ProductCreate' })">
              <el-icon style="margin-right: 5px">
                <Plus />
              </el-icon>
              添加商品
            </el-button>
          </div>
        </div>
      </template>

      <!-- 中部表格信息-->
      <el-table :data="queriedResult.product_list" max-height="1000" v-loading="tableLoading">
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
        <el-table-column label="操作" v-slot="{ row }" align="center" width="250px">
          <div class="control-item">
            <el-button
              :type="row.instruction !== '' ? 'success' : 'warning'"
              :disabled="row.instruction === ''"
              @click="
                ShowItemInfo.showItemInfoDialog(
                  row.product_name,
                  'Instruction',
                  row.instruction,
                  row.product_id
                )
              "
            >
              说明书
            </el-button>

            <!-- 编辑按钮 -->
            <el-button
              type="primary"
              :icon="Edit"
              @click="router.push({ name: 'ProductEdit', params: { productId: row.product_id } })"
            />

            <!-- 删除按钮 -->
            <el-button
              type="danger"
              @click="DeleteProduct(row.product_id, row.product_name)"
              :icon="Delete"
              :id="row.product_id"
              :disabled="isDelecting"
            />
          </div>
        </el-table-column>
      </el-table>

      <!-- 信息弹窗 -->
      <InfoDialogComponents ref="ShowItemInfo" />

      <!-- 分页栏 -->
      <template #footer>
        <!-- TODO 保持在页面最低位置 -->
        <el-pagination
          v-model:current-page="queriedResult.currentPage"
          v-model:page-size="queriedResult.pageSize"
          :page-sizes="[5, 10, 15, 20]"
          :background="true"
          layout="total, sizes, prev, pager, next, jumper"
          :total="queriedResult.totalSize || 0"
          @size-change="(pageSize: number) => getProductList({ pageSize, currentPage: 1 })"
          @current-change="(currentPage: number) => getProductList({ currentPage })"
        />
      </template>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.el-card {
  border-radius: 12px;
}

.box-card {
  width: auto; // 卡片宽度
}

// 查询栏
.card-header {
  display: flex;
  justify-content: space-between; // 将两个 div 放置在页面的两侧
  align-items: center;

  .el-form-item {
    margin-bottom: 0px; // 查询框和下面的组件间隔大小
  }
}

// 分页框
.el-pagination {
  margin-top: 10px; // 距离上面的控件有一定的距离
  display: flex;
  justify-content: center;
  align-items: center;
}

// 操作栏
.control-item {
  display: flex;
  align-items: center;
}

// 去掉表格下边框线
:deep(.el-table__inner-wrapper::before) {
  height: 0;
}
</style>
