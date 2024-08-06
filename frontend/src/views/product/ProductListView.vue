<script setup lang="ts">
import { queryCondition, queriedResult, getProductList } from '@/api/product'

// 获取商品信息
getProductList()
</script>

<template>
  <el-card>
    <template #header>
      <!-- 头部查询 -->
      <el-form :inline="true" :model="queriedResult.product">
        <el-form-item label="商品名称">
          <el-input v-model="queryCondition.productName" placeholder="商品名称" clearable />
        </el-form-item>
        <!-- <el-form-item label="分类">
          <el-select v-model="queriedResult.class" placeholder="">
            <el-option label="全部" value="" />
            <el-option label="电子" value="电子" />
          </el-select>
        </el-form-item> -->
        <el-form-item>
          <el-button type="primary" @click="() => getProductList({ currentPage: 1 })"
            >查询</el-button
          >
        </el-form-item>
      </el-form>
    </template>

    <!-- 中部表格信息 -->
    <el-table :data="queriedResult.product" max-height="1000" border>
      <el-table-column prop="product_id" label="ID" align="center" />
      <el-table-column prop="image_path" label="图片" align="center" />
      <el-table-column prop="product_name" label="名称" align="center" />
      <el-table-column prop="class" label="分类" align="center" />
      <el-table-column prop="heighlights" label="亮点" align="center" />
      <el-table-column prop="selling_price" label="价格" align="center" />
      <el-table-column prop="amount" label="库存" align="center" />
      <el-table-column prop="sales_doc" label="解说文案" align="center" />
      <el-table-column prop="instruction" label="说明书" align="center" />
      <el-table-column prop="digital_human_video" label="数字人视频" align="center" />
      <el-table-column prop="departure_place" label="发货地" align="center" />
      <el-table-column prop="delivery_company" label="快递公司" align="center" />
      <el-table-column prop="upload_date" label="上传时间" align="center" />
      <el-table-column label="操作" align="center">
        <el-button size="small">修改</el-button>
        <el-button size="small" type="danger">归档</el-button>
        <el-button size="small">分配直播间</el-button>
      </el-table-column>
    </el-table>

    <!-- 分页栏 -->
    <template #footer>
      <el-pagination
        v-model:current-page="queriedResult.current"
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
</template>

<style lang="scss" scoped>
.box-card {
  width: auto; // 卡片宽度
}

// 查询栏
.el-form-item {
  margin-bottom: 0px; // 查询框和下面的组件间隔大小
}

// 分页框
.el-pagination {
  margin-top: 10px; // 距离上面的控件有一定的距离
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
