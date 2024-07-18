# 模型文件夹

本文件夹是本项目所有的模型存放路径，如果各位在下载的过程出现问题，可以自行下载，模型一览表

| 模块 | 名称 | 下载地址 | 存放路径 |
| ---| --- | --- | --- |
| ASR | paraformer-zh | [modelscope](https://modelscope.cn/models/iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch/files) | asr_weights/iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch |
| ASR | fsmn-vad | [modelscope](https://modelscope.cn/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/files) | asr_weights/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch |
| ASR | ct-punc | [modelscope](https://modelscope.cn/models/iic/punc_ct-transformer_cn-en-common-vocab471067-large/files) | asr_weights/iic/punc_ct-transformer_cn-en-common-vocab471067-large |
| 数字人 | dwpose | [hf](https://hf-mirror.com/yzd-v/DWPose/blob/main/dw-ll_ucoco_384.pth) | digital_human_weights/dwpose/dw-ll_ucoco_384.pth |
| 数字人 | face-alignment | [adrianbulat](https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth) | digital_human_weights/face-alignment/s3fd-619a316812.pth |
| 数字人 | face-parse-bisent | [hf](https://hf-mirror.com/ManyOtherFunctions/face-parse-bisent/blob/main/79999_iter.pth) </br></br> [hf](https://hf-mirror.com/ManyOtherFunctions/face-parse-bisent/blob/main/resnet18-5c106cde.pth) | digital_human_weights/face-parse-bisent/79999_iter.pth </br></br> digital_human_weights/face-parse-bisent/resnet18-5c106cde.pth|
| 数字人 | musetalk | [hf](https://hf-mirror.com/TMElyralab/MuseTalk/tree/main) | digital_human_weights/musetalk/ |
| 数字人 | sd-vae-ft-mse | [hf](https://hf-mirror.com/stabilityai/sd-vae-ft-mse/tree/main) | digital_human_weights/sd-vae-ft-mse/ |
| 数字人 | whisper | [azure edge](https://openaipublic.azureedge.net/main/whisper/models/65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9/tiny.pt) | digital_human_weights/whisper/tiny.pt |
| TTS | pretrain | [hf](https://huggingface.co/lj1995/GPT-SoVITS/tree/main) | gpt_sovits_weights/pretrain |
| TTS | star | [hf](https://huggingface.co/baicai1145/GPT-SoVITS-STAR/blob/main/%E8%89%BE%E4%B8%9D%E5%A6%B2.zip) | gpt_sovits_weights/star |
| LLM | streamer-sales-lelemiao-7b | [modelscope](https://modelscope.cn/models/HinGwenWoong/streamer-sales-lelemiao-7b) | llm_weights/HinGwenWoong/streamer-sales-lelemiao-7b |
| RAG | BCE | [modelscope](https://modelscope.cn/models/maidalun/bce-embedding-base_v1/files) <br/><br/> [modelscope](https://modelscope.cn/models/maidalun/bce-reranker-base_v1/files)| rag_weights/maidalun/bce-embedding-base_v1 <br/><br/> rag_weights/maidalun/bce-reranker-base_v1 |


磁盘占用情况:

| 模型文件夹 | 占用大小 |
| :-: | :-: |
| asr_weights | 2.1G    |
| digital_human_weights | 4.8G    |
| gpt_sovits_weights | 1.6G    |
| llm_weights | 15G     |
| rag_weights | 2.2G    |


最终文件结构如下：

```bash
./weights
|-- asr_weights
|   |-- iic
|   |   |-- punc_ct-transformer_cn-en-common-vocab471067-large
|   |   |   |-- README.md
|   |   |   |-- config.yaml
|   |   |   |-- configuration.json
|   |   |   |-- example
|   |   |   |   `-- punc_example.txt
|   |   |   |-- fig
|   |   |   |   `-- struct.png
|   |   |   |-- jieba.c.dict
|   |   |   |-- jieba_usr_dict
|   |   |   |-- model.pt
|   |   |   `-- tokens.json
|   |   |-- speech_fsmn_vad_zh-cn-16k-common-pytorch
|   |   |   |-- README.md
|   |   |   |-- am.mvn
|   |   |   |-- config.yaml
|   |   |   |-- configuration.json
|   |   |   |-- example
|   |   |   |   `-- vad_example.wav
|   |   |   |-- fig
|   |   |   |   `-- struct.png
|   |   |   `-- model.pt
|   |   `-- speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch
|   |       |-- README.md
|   |       |-- am.mvn
|   |       |-- asr_example_hotword.wav
|   |       |-- config.yaml
|   |       |-- configuration.json
|   |       |-- example
|   |       |   |-- asr_example.wav
|   |       |   `-- hotword.txt
|   |       |-- fig
|   |       |   |-- res.png
|   |       |   `-- seaco.png
|   |       |-- model.pt
|   |       |-- seg_dict
|   |       `-- tokens.json
|   `-- temp
|-- digital_human_weights
|   |-- README.md
|   |-- dwpose
|   |   `-- dw-ll_ucoco_384.pth
|   |-- face-alignment
|   |   |-- checkpoints
|   |   |   `-- s3fd-619a316812.pth
|   |-- face-parse-bisent
|   |   |-- 79999_iter.pth
|   |   `-- resnet18-5c106cde.pth
|   |-- musetalk
|   |   |-- musetalk.json
|   |   `-- pytorch_model.bin
|   |-- sd-vae-ft-mse
|   |   |-- README.md
|   |   |-- config.json
|   |   |-- diffusion_pytorch_model.bin
|   |   `-- diffusion_pytorch_model.safetensors
|   `-- whisper
|       `-- tiny.pt
|-- gpt_sovits_weights
|   |-- pretrain
|   |   |-- README.md
|   |   |-- chinese-hubert-base
|   |   |   |-- config.json
|   |   |   |-- preprocessor_config.json
|   |   |   `-- pytorch_model.bin
|   |   |-- chinese-roberta-wwm-ext-large
|   |   |   |-- config.json
|   |   |   |-- pytorch_model.bin
|   |   |   `-- tokenizer.json
|   |   |-- s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt
|   |   |-- s2D488k.pth
|   |   `-- s2G488k.pth
|   `-- star
|       |-- 参考音频
|       |   |-- 平静说话-你们经过的收容舱段收藏着诸多「奇物」和「遗器」，是最核心的研究场所。.wav
|       |   |-- 激动说话-列车巡游银河，我不一定都能帮上忙，但只要是花钱能解决的事，尽管和我说吧。.wav
|       |   |-- 疑惑-已经到这个点了么？工作的时间总是过得那么快。.wav
|       |   `-- 迟疑-虽然现在一个字都还没写，但写起来肯定很快。.wav
|       |-- 艾丝妲-e10.ckpt
|       |-- 艾丝妲.zip
|       |-- 艾丝妲_e25_s925.pth
|       `-- 训练日志.log
|-- llm_weights
|   |-- HinGwenWoong
|   |   `-- streamer-sales-lelemiao-7b
|   |       |-- LICENSE
|   |       |-- README.md
|   |       |-- config.json
|   |       |-- configuration.json
|   |       |-- configuration_internlm2.py
|   |       |-- generation_config.json
|   |       |-- modeling_internlm2.py
|   |       |-- pytorch_model-00001-of-00008.bin
|   |       |-- pytorch_model-00002-of-00008.bin
|   |       |-- pytorch_model-00003-of-00008.bin
|   |       |-- pytorch_model-00004-of-00008.bin
|   |       |-- pytorch_model-00005-of-00008.bin
|   |       |-- pytorch_model-00006-of-00008.bin
|   |       |-- pytorch_model-00007-of-00008.bin
|   |       |-- pytorch_model-00008-of-00008.bin
|   |       |-- pytorch_model.bin.index.json
|   |       |-- special_tokens_map.json
|   |       |-- tokenization_internlm2.py
|   |       |-- tokenization_internlm2_fast.py
|   |       |-- tokenizer.json
|   |       |-- tokenizer.model
|   |       `-- tokenizer_config.json
|   `-- temp
`-- rag_weights
    |-- maidalun
    |   |-- bce-embedding-base_v1
    |   |   |-- 1_Pooling
    |   |   |   `-- config.json
    |   |   |-- README.md
    |   |   |-- config.json
    |   |   |-- config_sentence_transformers.json
    |   |   |-- configuration.json
    |   |   |-- modules.json
    |   |   |-- pytorch_model.bin
    |   |   |-- sentence_bert_config.json
    |   |   |-- sentencepiece.bpe.model
    |   |   |-- special_tokens_map.json
    |   |   |-- tokenizer.json
    |   |   `-- tokenizer_config.json
    |   `-- bce-reranker-base_v1
    |       |-- README.md
    |       |-- config.json
    |       |-- configuration.json
    |       |-- pytorch_model.bin
    |       |-- sentencepiece.bpe.model
    |       |-- special_tokens_map.json
    |       |-- tokenizer.json
    |       `-- tokenizer_config.json
    `-- temp
```
