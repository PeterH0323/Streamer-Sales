<template>
  <div class="login">
    <el-form
      :model="loginForm"
      :rules="rules"
      label-width="120px"
      label-position="top"
      size="large"
      ref="formRef"
    >
      <h2>销冠 —— 卖货主播大模型</h2>

      <!-- prop -> 校验规则的名称 -->
      <el-form-item label="用户名" prop="name">
        <el-input v-model="loginForm.name" />
      </el-form-item>

      <el-form-item label="密码" prop="password">
        <el-input v-model="loginForm.password" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="onSubmit">确认</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script lang="ts" setup>
import { reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { login_request } from '@/api/user'

// 表格信息保存对象
const formRef = ref<FormInstance>()

// 声明每个字段的类型
interface FormType {
  name: string
  password: string
  // vertify_code: string
}

// 双向绑定对象
const loginForm = reactive<FormType>({
  name: '',
  password: ''
  // vertify_code: ''
})

// 定义表单规则，在 el-form 中注册
const rules = reactive<FormRules<FormType>>({
  name: [
    { required: true, message: '请输入登录名', trigger: 'blur' },
    { pattern: /^1\d{10}$/, message: '请输入正确的电话号码', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 18, message: '密码长度必须 6~18 位', trigger: 'blur' }
  ]
})

const onSubmit = async () => {
  // 表单校验
  await formRef.value?.validate().catch((err) => {
    ElMessage.error('表单校验失败')
    throw err // 抛出异常
    // return new Promise(() => ()) // 返回一个空的状态
  })

  // 校验成功，执行登录
  const log_res = await login_request(loginForm).then((res) => {
    if (!res.data.success) {
      // 登录失败
      ElMessage.error('账号名或密码错误')
      throw new Error('账号名或密码错误') // 抛出异常
    }
    return res.data
  })

  console.log(log_res)
}
</script>

<style lang="scss">
.login {
  background-color: #dddddd;
  height: 100vh; // 满屏
  display: flex; // 居中显示
  justify-content: center;
  align-items: center;

  .el-form {
    width: 300px;
    background-color: #ffffff;
    padding: 30px; // 周围外加的 padding 像素
    border-radius: 10px; // 边框圆角
  }

  .el-form-item {
    margin-top: 20px; // 距离上方控件距离
  }

  .el-button {
    width: 100%;
    margin-top: 20px;
  }
}
</style>
