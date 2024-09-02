<script setup lang="ts">
const tableData = [
  {
    id: 1,
    date: '2024-05-03',
    name: '电动牙刷',
    amount: 1,
    address: '广东省广州市********',
    status: '备货中'
  },
  {
    id: 2,
    date: '2024-05-02',
    name: '平板电脑',
    amount: 1,
    address: '北京市朝阳区********',
    status: '备货中'
  },
  {
    id: 3,
    date: '2024-05-01',
    name: '唇膏',
    amount: 1,
    address: '浙江省杭州市********',
    status: '已发货'
  },
  {
    id: 4,
    date: '2024-05-02',
    name: '洗发露',
    amount: 2,
    address: '上海市黄浦区********',
    status: '已完成'
  }
]
</script>

<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <!-- 头部 -->
        <div class="card-header">
          <div>
            <el-form :inline="true">
              <el-form-item label="搜索">
                <el-input style="width: 240px" placeholder="商品名称" clearable />
              </el-form-item>
              <el-form-item>
                <el-button type="primary"> 查询 </el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </template>

      <el-table :data="tableData" style="width: 100%">
        <el-table-column prop="id" label="ID" width="50" />
        <el-table-column prop="name" label="商品名称" />
        <el-table-column prop="amount" label="数量" />
        <el-table-column prop="date" label="下单时间" />
        <el-table-column prop="address" label="地址" />
        <el-table-column label="订单状态" v-slot="{ row }" align="center" width="250px">
          <el-tag :type="row.status === '已完成' ? 'success' : 'warning'">{{ row.status }}</el-tag>
        </el-table-column>
      </el-table>
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
</style>
