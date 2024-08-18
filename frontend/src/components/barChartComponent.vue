<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

// 创建一个引用来存储图表的 DOM 容器
const chartRef = ref(null)

const props = defineProps({
  knowledgeBasesNum: {
    type: Number,
    default: 0
  },

  digitalHumanNum: {
    type: Number,
    default: 0
  },

  LiveRoomNum: {
    type: Number,
    default: 0
  }
})

// 初始化图表的函数
const initChart = () => {
  const chart = echarts.init(chartRef.value)

  // 配置图表的选项
  const option = {
    title: {
      text: '系统配置'
    },
    tooltip: {},
    xAxis: {
      data: ['知识库数量', '数字人数量', '直播间数量']
    },
    yAxis: {},
    series: [
      {
        name: '数量',
        type: 'bar',
        data: [props.knowledgeBasesNum, props.digitalHumanNum, props.LiveRoomNum]
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
