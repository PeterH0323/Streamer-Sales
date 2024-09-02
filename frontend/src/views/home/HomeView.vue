<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useTransition } from '@vueuse/core'
import { getDashboardInfoRequest, type DashboardItem } from '@/api/dashboard'
import BarChartComponent from '@/components/BarChartComponent.vue'
import LineChartComponent from '@/components/LineChartComponent.vue'

import {
  OfficeBuilding,
  Present,
  View,
  DataAnalysis,
  CreditCard,
  ShoppingCartFull
} from '@element-plus/icons-vue'
const systemInfo = ref({} as DashboardItem)

const registeredBrandNum = ref(0) //入驻品牌方
const productNum = ref(0) //商品数
const dailyActivity = ref(0) //日活
const todayOrder = ref(0) //订单量
const totalSales = ref(0) //销售额
const conversionRate = ref(0) //转化率

// 配置动画
const registeredBrandNumTrans = useTransition(registeredBrandNum, {
  duration: 1500
})
const productNumTrans = useTransition(productNum, {
  duration: 1500
})
const dailyActivityTrans = useTransition(dailyActivity, {
  duration: 1500
})
const todayOrderTrans = useTransition(todayOrder, {
  duration: 1500
})
const totalSalesTrans = useTransition(totalSales, {
  duration: 1500
})
const conversionRateTrans = useTransition(conversionRate, {
  duration: 1500
})

const iconSize = ref(50)

onMounted(async () => {
  const { data } = await getDashboardInfoRequest()
  if (data.code === 0) {
    systemInfo.value = data.data

    registeredBrandNum.value = systemInfo.value.registeredBrandNum
    productNum.value = systemInfo.value.productNum
    dailyActivity.value = systemInfo.value.dailyActivity
    todayOrder.value = systemInfo.value.todayOrder
    totalSales.value = systemInfo.value.totalSales
    conversionRate.value = systemInfo.value.conversionRate
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
          <el-icon :size="iconSize" color="#006382"><OfficeBuilding /></el-icon>
          <el-statistic title="入驻品牌方数量" :value="registeredBrandNumTrans" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <el-icon :size="iconSize" color="#f0bb1f"><Present /></el-icon>
          <el-statistic title="商品数" :value="productNumTrans" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <el-icon :size="iconSize" color="#f25a2b"><View /></el-icon>
          <el-statistic title="日活" :value="dailyActivityTrans" />
        </el-card>
      </el-col>
    </el-row>

    <el-row>
      <el-col :span="8">
        <el-card shadow="never">
          <el-icon :size="iconSize" color="#97d1c8"><ShoppingCartFull /></el-icon>
          <el-statistic title="今日订单数" :value="todayOrderTrans" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <el-icon :size="iconSize" color="#756bf2"><CreditCard /></el-icon>
          <el-statistic title="销售额" :value="totalSalesTrans" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <el-icon :size="iconSize" color="#22c45d"><DataAnalysis /></el-icon>
          <el-statistic title="转化率(%)" :value="conversionRateTrans" />
        </el-card>
      </el-col>
    </el-row>

    <el-row>
      <el-col :span="16">
        <el-card shadow="never">
          <LineChartComponent
            :orderNumList="systemInfo.orderNumList"
            :totalSalesList="systemInfo.totalSalesList"
            :newUserList="systemInfo.newUserList"
            :activityUserList="systemInfo.activityUserList"
            :key="systemInfo.registeredBrandNum"
          />
        </el-card>
      </el-col>
      <el-col :span="8">
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
.el-col {
  text-align: center;
}

.el-statistic {
  --el-statistic-title-font-size: 16px;
  --el-statistic-title-font-weight: 400;

  --el-statistic-content-font-size: 28px;
  --el-statistic-content-font-weight: 800;
}

.el-card {
  margin: 12px 12px 12px 12px;
  border-radius: 22px;

  .info-item {
    margin: 12px 12px 12px 12px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
}
</style>
