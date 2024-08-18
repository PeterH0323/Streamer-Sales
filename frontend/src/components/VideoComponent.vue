<script setup lang="ts">
import { onMounted } from 'vue'
import Player from 'xgplayer'

// 定义组件入参
const props = defineProps({
  src: {
    type: String,
    default: ''
  }
})

const playerOpts = {
  id: 'player', //元素id
  url: props.src, //视频地址
  poster: '@/assets/logo.png', //封面图
  lang: 'zh-cn', //设置中文
  lastPlayTime: 0, //视频起播时间（单位：秒）
  lastPlayTimeHideDelay: 5, //提示文字展示时长（单位：秒）
  closeVideoClick: false, // true - 禁止pc端单击暂停，反之
  closeVideoTouch: true, // true - 禁止移动端单击暂停，反之
  videoInit: true,
  fluid: true, //填满屏幕
  autoplay: false, //自动播放
  loop: false, //循环播放
  pip: true,
  volume: 1, //音量 0 -  1
  playbackRate: [0.5, 0.75, 1, 1.5, 2], //传入倍速可选数组
  // 删除控件
  // ignores: ['time', 'definition', 'error', 'fullscreen', 'i18n', 'loading', 'mobile', 'pc', 'play', 'poster', 'progress', 'replay', 'volume'],
  ignores: ['volume'],
  rotateFullscreen: true
}

//  播放器
let player = null

// 必须在onMounted 或 nextTick实例Xgplayer播放器
onMounted(() => {
  player = new Player(playerOpts)
})
</script>

<template>
  <div id="player"></div>
</template>
