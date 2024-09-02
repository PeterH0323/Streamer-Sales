<script setup lang="ts">
import { useRoute, useRouter, type RouteRecordNormalized, type RouteLocationRaw } from 'vue-router'

const route = useRoute()
const router = useRouter()

const handleLink = (item: RouteRecordNormalized) => {
  const { redirect, name, path } = item
  if (redirect) {
    router.push(redirect as RouteLocationRaw)
  } else {
    if (name) {
      router.push({ name })
    } else {
      router.push({ path })
    }
  }
}
</script>

<template>
  <el-breadcrumb separator="/">
    <el-breadcrumb-item
      v-for="(item, index) in route.matched"
      :key="index"
      :to="{ path: item.path }"
    >
      <a @click.prevent="handleLink(item)">
        {{ item.meta.title }}
      </a>
    </el-breadcrumb-item>
  </el-breadcrumb>
</template>

<style lang="scss" scoped></style>
