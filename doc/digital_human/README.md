# ComfyUI 使用文档

## 工作流

如果您已经有 ComfyUI 的环境，可以直接使用我的工作流：

<p align="center">
  <img src="./streamer-sales-lelemiao-workflow-v1.0.png" alt="Demo gif" >
</p>


## 功能点

我的 Workflow 具有以下功能点：

- 生成人像
- dwpose 生成骨骼图
- AnimateDiff生成视频
- 提升分辨率
- 插帧提升帧率

## 环境搭建

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
pip install -r requirements.txt
```

测试安装

```bash
cd ComfyUI
python main.py
```

## 模型下载

执行脚本 `python download_models.py` 即可下载本项目需要用到的全部权重

## 插件安装

1. 首先需要手动拉取下【插件管理器】

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/ltdrdata/ComfyUI-Manager.git
```

2. 重启 ComfyUI

3. 刷新页面，点击右下角 【管理器】->【安装缺失节点】即可。

以下是我用到的插件：

|            插件名             |            用途            |
| :---------------------------: | :------------------------: |
| AIGODLIKE-COMFYUI-TRANSLATION |          中文翻译          |
|  ComfyUI-Advanced-ControlNet  |  ContralNet 工具包升级版   |
|  ComfyUI-AnimateDiff-Evolved  |    AnimateDiff 动画生成    |
|       ComfyUI-Crystools       |        机器资源监控        |
|    ComfyUI-Custom-Scripts     |          模型管理          |
|  ComfyUI-Frame-Interpolation  |            插帧            |
|      ComfyUI-Impact-Pack      |                            |
|        ComfyUI-Manager        |     插件管理器（必备）     |
|   ComfyUI-VideoHelperSuite    |         视频加载器         |
|       ComfyUI_FizzNodes       |                            |
|    ComfyUI_IPAdapter_plus     |     IPAdapter 风格迁移     |
| comfyui-portrait-master-zh-cn | 人物生成中文提示词辅助工具 |
|   comfyui-workspace-manager   |        工作流管理器        |
|    comfyui_controlnet_aux     |     ContralNet 工具包      |
|   comfyui_segment_anything    |         SAM 工具包         |
|      sdxl_prompt_styler       |        SDXL 工具包         |

## 开发参考网站

- 模型下载网站：C站：https://civitai.com
- 提示词网站：https://promlib.com/
- 工作流：https://openart.ai/workflows/home
- 插件排行：https://www.nodecafe.org/
