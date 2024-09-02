<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import type PresetPlayer from 'xgplayer'
import Player, { type IPlayerOptions } from 'xgplayer'

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
  loop: {
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
  },
  videoAfterEnd: {
    type: String,
    default: ''
  }
})

const player_id = ref(props.src !== '' ? props.src : 'video_player')

const playerOpts: IPlayerOptions = {
  id: player_id.value, //元素id
  url: props.src, //视频地址
  width: props.width, // 播放器宽度
  height: props.height, //播放器高度
  poster: '@/assets/logo.png', //封面图
  lang: 'zh-cn', //设置中文
  closeVideoClick: false, // true - 禁止pc端单击暂停
  videoInit: true, // 是否默认初始化video，当autoplay为true时，该配置为false无效
  fluid: false, //是否启用流式布局，启用流式布局时根据width、height计算播放器宽高比，若width和height不是Number类型，默认使用16:9比例
  autoplay: props.autoplay, //自动播放
  loop: props.loop, //循环播放
  autoplayMuted: false, // 是否自动静音自动播放，如果autoplay为false，则该属性的作用为默认静音播放
  pip: false, //是否使用画中画插件,
  closeVideoDblclick: true, // 是否关闭双击播放器进入全屏的能力
  volume: 1, //音量 0 -  1
  // playbackRate: [0.5, 0.75, 1, 1.5, 2], //传入倍速可选数组
  // 删除插件，插件文档: https://h5player.bytedance.com/plugins/internalplugins/controls.html
  ignores: [
    'volume',
    'cssFullScreen',
    'fullscreen',
    'enter',
    'play',
    'replay',
    'start',
    'playbackrate'
  ]
}

//  播放器
let player: Player | null = null

// 必须在onMounted 或 nextTick实例Xgplayer播放器
onMounted(() => {
  player = new Player(playerOpts)

  player.on('ended', () => {
    // 播放结束后的切换为 videoAfterEnd 的视频
    console.log('视频播放结束')

    if (props.videoAfterEnd !== '') {
      playerOpts.autoplay = true // 自动播放
      playerOpts.loop = true // 循环播放
      playerOpts.autoplayMuted = true // 静音
      playerOpts.url = props.videoAfterEnd // 新的视频地址

      // player.playNext(playerOpts) // 使用 playnext 之后不能触发 loop ，需要重新实例化
      if (player) {
        player.destroy()
      }
      player = null
      player = new Player(playerOpts)
    }
  })
})

onBeforeUnmount(() => {
  if (player) {
    player.destroy()
    player = null
  }
})
</script>

<template>
  <div :id="player_id"></div>
</template>
