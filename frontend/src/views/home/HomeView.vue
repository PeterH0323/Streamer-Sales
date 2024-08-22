<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { getDashboardInfoRequest, type DashboardItem } from '@/api/dashboard'
import BarChartComponent from '@/components/BarChartComponent.vue'
import LineChartComponent from '@/components/LineChartComponent.vue'

const systemInfo = ref({} as DashboardItem)

onMounted(async () => {
  const { data } = await getDashboardInfoRequest()
  if (data.code === 0) {
    systemInfo.value = data.data
  } else {
    ElMessage.error('获取总览数据失败')
  }
})
</script>

<template>
  <div>
    <el-row>
      <el-col :span="8">
        <el-card shadow="never">
          <div class="info-item title">入驻品牌方数量</div>
          <div class="info-item number">{{ systemInfo.registeredBrandNum }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <div class="info-item title">商品数</div>
          <div class="info-item number">{{ systemInfo.productNum }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <div class="info-item title">日活</div>
          <div class="info-item number">{{ systemInfo.dailyActivity }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row>
      <el-col :span="8">
        <el-card shadow="never">
          <div class="info-item title">今日订单数</div>
          <div class="info-item number">{{ systemInfo.todayOrder }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <div class="info-item title">销售额</div>
          <div class="info-item number">{{ systemInfo.totalSales }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <div class="info-item title">转化率</div>
          <div class="info-item number">{{ systemInfo.conversionRate }} %</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row>
      <el-col :span="14">
        <el-card shadow="never">
          <LineChartComponent
            :orderNumList="systemInfo.orderNumList"
            :totalSalesList="systemInfo.totalSalesList"
            :newUserList="systemInfo.newUserList"
            :activityUserList="systemInfo.activityUserList"
            :key="systemInfo.orderNumList"
          />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never">
          <BarChartComponent
            :knowledgeBasesNum="systemInfo.knowledgeBasesNum"
            :digitalHumanNum="systemInfo.digitalHumanNum"
            :LiveRoomNum="systemInfo.LiveRoomNum"
            :key="systemInfo.knowledgeBasesNum"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style lang="scss" scoped>
.el-card {
  margin: 12px 12px 12px 12px;
  border-radius: 15px;

  .info-item {
    margin: 12px 12px 12px 12px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .title {
    font-weight: 600;
    font-size: 25px;
  }

  .number {
    font-size: 18px;
  }
}
</style>
