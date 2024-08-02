<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const handleLink = (item) => {
  const { redirect, name, path } = item
  if (redirect) {
    router.push(redirect as any)
  } else {
    if (name) {
      if (item.query) {
        router.push({
          name,
          query: item.query
        })
      } else if (item.params) {
        router.push({
          name,
          params: item.params
        })
      } else {
        router.push({ name })
      }
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
