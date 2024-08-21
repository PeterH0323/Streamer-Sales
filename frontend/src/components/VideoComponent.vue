<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Player from 'xgplayer'

// 定义组件入参
const props = defineProps({
  src: {
    type: String,
    default: 'player'
  },
  autoplay: {
    type: Boolean,
    default: false
  },
  width: {
    type: Number,
    default: 600
  },
  height: {
    type: Number,
    default: 337.5
  }
})

const player_id = ref(props.src)

const playerOpts = {
  id: player_id.value, //元素id
  url: props.src, //视频地址
  width: props.width, // 播放器宽度
  height: props.height, //播放器高度
  poster: '@/assets/logo.png', //封面图
  lang: 'zh-cn', //设置中文
  closeVideoClick: false, // true - 禁止pc端单击暂停，反之
  videoInit: true, // 是否默认初始化video，当autoplay为true时，该配置为false无效
  fluid: true, //填满屏幕
  autoplay: props.autoplay, //自动播放
  loop: false, //循环播放
  pip: false, //是否使用画中画插件
  volume: 1, //音量 0 -  1
  playbackRate: false, // [0.5, 0.75, 1, 1.5, 2], //传入倍速可选数组
  // 删除控件
  // ignores: ['time', 'definition', 'error', 'fullscreen', 'i18n', 'loading', 'mobile', 'pc', 'play', 'poster', 'progress', 'replay', 'volume'],
  ignores: ['volume']
}

//  播放器
let player = null

// 必须在onMounted 或 nextTick实例Xgplayer播放器
onMounted(() => {
  player = new Player(playerOpts)
})
</script>

<template>
  <div :id="player_id"></div>
</template>
