<script setup lang="ts">
import { queryCondition, queriedResult, getProductList } from '@/api/product'

// 获取商品信息
getProductList()
</script>

<template>
  <el-card>
    <template #header>
      <!-- 头部查询 -->
      <!-- <el-form :inline="true" :model="formInline" class="demo-form-inline">
        <el-form-item label="Approved by">
          <el-input v-model="formInline.user" placeholder="Approved by" clearable />
        </el-form-item>
        <el-form-item label="Activity zone">
          <el-select v-model="formInline.region" placeholder="Activity zone" clearable>
            <el-option label="Zone one" value="shanghai" />
            <el-option label="Zone two" value="beijing" />
          </el-select>
        </el-form-item>
        <el-form-item label="Activity time">
          <el-date-picker
            v-model="formInline.date"
            type="date"
            placeholder="Pick a date"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSubmit">Query</el-button>
        </el-form-item>
      </el-form> -->
    </template>
    <el-table :data="queriedResult.product" border style="width: 100%">
      <el-table-column prop="product_id" label="ID" align="center" />
      <el-table-column prop="image_path" label="图片" align="center" />
      <el-table-column prop="product_name" label="名称" align="center" />
      <el-table-column prop="class" label="分类" align="center" />
      <el-table-column prop="heightlight" label="亮点" align="center" />
      <el-table-column prop="selling_price" label="价格" align="center" />
      <el-table-column prop="amount" label="库存" align="center" />
      <el-table-column prop="sales_doc" label="解说文案" align="center" />
      <el-table-column prop="instruction_path" label="说明书" align="center" />
      <el-table-column prop="digital_human_video" label="数字人视频" align="center" />
      <el-table-column prop="departure_place" label="发货地" align="center" />
      <el-table-column prop="delivery_company" label="快递公司" align="center" />
      <el-table-column prop="upload_date" label="上传时间" align="center" />
      <el-table-column label="操作" align="center">
        <el-button>修改</el-button>
        <el-button>归档</el-button>
        <el-button>分配直播间</el-button>
      </el-table-column>
    </el-table>
    <template #footer>
      <!-- 分页栏 -->
      <!-- <el-pagination
        v-model:current-page="currentPage4"
        v-model:page-size="pageSize4"
        :page-sizes="[100, 200, 300, 400]"
        :size="size"
        :disabled="disabled"
        :background="background"
        layout="total, sizes, prev, pager, next, jumper"
        :total="400"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      /> -->
    </template>
  </el-card>
</template>

<style lang="scss" scoped>
.box-card {
  width: auto; // 卡片宽度
}
</style>
