# 前端文档

## 安装 npm

参考[官网说明](https://nodejs.org/zh-cn/download/package-manager)，执行下面的命令就可以完成安装：

```bash
# layouts.download.codeBox.installsFnm
curl -fsSL https://fnm.vercel.app/install | bash

# layouts.download.codeBox.activateFNM
source ~/.bashrc

# layouts.download.codeBox.downloadAndInstallNodejs
fnm use --install-if-missing 20

# layouts.download.codeBox.verifiesRightNodejsVersion
node -v # layouts.download.codeBox.shouldPrint

# layouts.download.codeBox.verifiesRightNpmVersion
npm -v # layouts.download.codeBox.shouldPrint
```

## 启动项目

1. 进入前端项目：

```bash
cd frontend
```

2. 安装依赖库

```sh
npm install
```

3. 开发环境启动

> Compile and Hot-Reload for Development

```sh
npm run dev
```

4. 生产环境打包

> Type-Check, Compile and Minify for Production

```sh
npm run build
```
