<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

// 创建一个引用来存储图表的 DOM 容器
const chartRef = ref(null)

const props = defineProps({
  orderNumList: {
    type: Array
  },
  totalSalesList: {
    type: Array
  },
  newUserList: {
    type: Array
  },
  activityUserList: {
    type: Array
  }
})

// 初始化图表的函数
const initChart = () => {
  const chart = echarts.init(chartRef.value)

  // 配置图表的选项
  const option = {
    title: {
      text: '订单和用户数量'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      }
    },
    legend: {
      data: ['订单量', '销售额', '新增用户', '活跃用户']
    },
    toolbox: {
      feature: {
        saveAsImage: {}
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: [
      {
        type: 'category',
        boundaryGap: false,
        data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
      }
    ],
    yAxis: [
      {
        type: 'value'
      }
    ],
    series: [
      {
        name: '订单量',
        type: 'line',
        stack: 'Total',
        areaStyle: {},
        emphasis: {
          focus: 'series'
        },
        data: props.orderNumList
      },
      {
        name: '销售额',
        type: 'line',
        stack: 'Total',
        areaStyle: {},
        emphasis: {
          focus: 'series'
        },
        data: props.totalSalesList
      },
      {
        name: '新增用户',
        type: 'line',
        stack: 'Total',
        areaStyle: {},
        emphasis: {
          focus: 'series'
        },
        data: props.newUserList
      },
      {
        name: '活跃用户',
        type: 'line',
        stack: 'Total',
        areaStyle: {},
        emphasis: {
          focus: 'series'
        },
        data: props.activityUserList
      }
    ]
  }

  // 使用设置的配置项渲染图表
  chart.setOption(option)
}

// 在组件挂载后初始化图表
onMounted(() => {
  initChart()
})
</script>

<template>
  <div ref="chartRef" style="width: auto; height: 400px"></div>
</template>

<style scoped>
/* 可以根据需要调整图表容器的样式 */
</style>
