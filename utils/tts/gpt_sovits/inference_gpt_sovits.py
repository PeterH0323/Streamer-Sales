"""
TTS 
https://github.com/RVC-Boss/GPT-SoVITS/blob/main/GPT_SoVITS/inference_webui.py
"""

import os
import re
import shutil
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import LangSegment
import librosa
import numpy as np
import soundfile as sf
import streamlit as st
import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer
from transformers.models.bert.modeling_bert import BertForMaskedLM
from transformers.models.bert.tokenization_bert_fast import BertTokenizerFast

from utils import HParams
from utils.tts.gpt_sovits.AR.models.t2s_lightning_module import Text2SemanticLightningModule
from utils.tts.gpt_sovits.module import cnhubert
from utils.tts.gpt_sovits.module.cnhubert import CNHubert
from utils.tts.gpt_sovits.module.mel_processing import spectrogram_torch
from utils.tts.gpt_sovits.module.models import SynthesizerTrn
from utils.tts.gpt_sovits.text import cleaned_text_to_sequence
from utils.tts.gpt_sovits.text.cleaner import clean_text
from utils.tts.gpt_sovits.utils import load_audio
from utils.web_configs import WEB_CONFIGS

symbol_splits = {
    "，",
    "。",
    "？",
    "！",
    ",",
    ".",
    "?",
    "!",
    "~",
    ":",
    "：",
    "—",
    "…",
}

DEVICE = "cuda"
HZ = 50


def get_bert_feature(text, bert_tokenizer, bert_model, word2ph):
    with torch.no_grad():
        inputs = bert_tokenizer(text, return_tensors="pt")
        for i in inputs:
            inputs[i] = inputs[i].to(DEVICE)
        res = bert_model(**inputs, output_hidden_states=True)
        res = torch.cat(res["hidden_states"][-3:-2], -1)[0].cpu()[1:-1]
    assert len(word2ph) == len(text)
    phone_level_feature = []
    for i in range(len(word2ph)):
        repeat_feature = res[i].repeat(word2ph[i], 1)
        phone_level_feature.append(repeat_feature)
    phone_level_feature = torch.cat(phone_level_feature, dim=0)
    return phone_level_feature.T


def change_sovits_weights(sovits_path, is_half):

    dict_s2 = torch.load(sovits_path, map_location="cpu")
    hps = dict_s2["config"]
    hps.model.semantic_frame_rate = "25hz"
    vq_model = SynthesizerTrn(
        hps.data.filter_length // 2 + 1,
        hps.train.segment_size // hps.data.hop_length,
        n_speakers=hps.data.n_speakers,
        **hps.model,
    )
    if "pretrained" not in sovits_path:
        del vq_model.enc_q
    if is_half:
        vq_model = vq_model.half()
    vq_model = vq_model.to(DEVICE)
    vq_model.eval()
    print(vq_model.load_state_dict(dict_s2["weight"], strict=False))

    return vq_model, hps


def change_gpt_weights(gpt_path, is_half):
    dict_s1 = torch.load(gpt_path, map_location="cpu")
    config = dict_s1["config"]
    max_sec = config["data"]["max_sec"]
    t2s_model = Text2SemanticLightningModule(config, "****", is_train=False)
    t2s_model.load_state_dict(dict_s1["weight"])
    if is_half:
        t2s_model = t2s_model.half()
    t2s_model = t2s_model.to(DEVICE)
    t2s_model.eval()
    total = sum([param.nelement() for param in t2s_model.parameters()])
    print("Number of parameter: %.2fM" % (total / 1e6))

    return max_sec, t2s_model


def get_spepc(hps, filename):
    audio = load_audio(filename, int(hps.data.sampling_rate))
    audio = torch.FloatTensor(audio)
    audio_norm = audio
    audio_norm = audio_norm.unsqueeze(0)
    spec = spectrogram_torch(
        audio_norm,
        hps.data.filter_length,
        hps.data.sampling_rate,
        hps.data.hop_length,
        hps.data.win_length,
        center=False,
    )
    return spec


def clean_text_inf(text, language):
    phones, word2ph, norm_text = clean_text(text, language)
    phones = cleaned_text_to_sequence(phones)
    return phones, word2ph, norm_text


def get_bert_inf(phones, word2ph, bert_tokenizer, bert_model, norm_text, language, is_half=True):
    language = language.replace("all_", "")
    if language == "zh":
        bert = get_bert_feature(norm_text, bert_tokenizer, bert_model, word2ph).to(DEVICE)  # .to(dtype)
    else:
        bert = torch.zeros((1024, len(phones)), dtype=torch.float16 if is_half else torch.float32).to(DEVICE)

    return bert


def get_first(text):
    pattern = "[" + "".join(re.escape(sep) for sep in symbol_splits) + "]"
    text = re.split(pattern, text)[0].strip()
    return text


def get_phones_and_bert(text, bert_tokenizer, bert_model, language, is_half=True):
    if language in {"en", "all_zh", "all_ja"}:
        language = language.replace("all_", "")
        if language == "en":
            LangSegment.setfilters(["en"])
            formattext = " ".join(tmp["text"] for tmp in LangSegment.getTexts(text))
        else:
            # 因无法区别中日文汉字,以用户输入为准
            formattext = text
        while "  " in formattext:
            formattext = formattext.replace("  ", " ")
        phones, word2ph, norm_text = clean_text_inf(formattext, language)
        if language == "zh":
            bert = get_bert_feature(norm_text, bert_tokenizer, bert_model, word2ph).to(DEVICE)
        else:
            bert = torch.zeros(
                (1024, len(phones)),
                dtype=torch.float16 if is_half else torch.float32,
            ).to(DEVICE)
    elif language in {"zh", "ja", "auto"}:
        textlist = []
        langlist = []
        LangSegment.setfilters(["zh", "ja", "en", "ko"])
        if language == "auto":
            for tmp in LangSegment.getTexts(text):
                if tmp["lang"] == "ko":
                    langlist.append("zh")
                    textlist.append(tmp["text"])
                else:
                    langlist.append(tmp["lang"])
                    textlist.append(tmp["text"])
        else:
            for tmp in LangSegment.getTexts(text):
                if tmp["lang"] == "en":
                    langlist.append(tmp["lang"])
                else:
                    # 因无法区别中日文汉字,以用户输入为准
                    langlist.append(language)
                textlist.append(tmp["text"])
        print(textlist)
        print(langlist)
        phones_list = []
        bert_list = []
        norm_text_list = []
        for i in range(len(textlist)):
            lang = langlist[i]
            phones, word2ph, norm_text = clean_text_inf(textlist[i], lang)
            bert = get_bert_inf(phones, word2ph, bert_tokenizer, bert_model, norm_text, lang, is_half)
            phones_list.append(phones)
            norm_text_list.append(norm_text)
            bert_list.append(bert)
        bert = torch.cat(bert_list, dim=1)
        phones = sum(phones_list, [])
        norm_text = "".join(norm_text_list)

    return phones, bert.to(torch.float16 if is_half else torch.float32), norm_text


def merge_short_text_in_array(texts, threshold):
    if (len(texts)) < 2:
        return texts
    result = []
    text = ""
    for ele in texts:
        text += ele
        if len(text) >= threshold:
            result.append(text)
            text = ""
    if len(text) > 0:
        if len(result) == 0:
            result.append(text)
        else:
            result[len(result) - 1] += text
    return result


def get_tts_wav(
    text,
    text_language,
    bert_tokenizer,
    bert_model,
    ssl_model,
    vq_model,
    hps,
    max_sec,
    t2s_model: Text2SemanticLightningModule,
    ref_wav_path,
    prompt,
    refer,
    bert1,
    phones1,
    zero_wav,
    prompt_text,
    prompt_language,
    how_to_cut="不切",
    top_k=20,
    top_p=0.6,
    temperature=0.6,
    ref_free=False,
    is_half=True,
    process_bar=None,
):

    dict_language = {
        "中文": "all_zh",  # 全部按中文识别
        "英文": "en",  # 全部按英文识别#######不变
        "日文": "all_ja",  # 全部按日文识别
        "中英混合": "zh",  # 按中英混合识别####不变
        "日英混合": "ja",  # 按日英混合识别####不变
        "多语种混合": "auto",  # 多语种启动切分识别语种
    }

    prompt_language = dict_language[prompt_language]
    text_language = dict_language[text_language]

    text = text.strip("\n")
    if text[0] not in symbol_splits and len(get_first(text)) < 4:
        text = "。" + text
    print("=" * 20, "\n实际输入的目标文本:", text)

    text = cut_sentences(text, how_to_cut)
    print("=" * 20, "\n实际输入的目标文本(切句后):", text)

    texts = text.split("\n")
    texts = merge_short_text_in_array(texts, 5)  # 小于 5 个字符的句子和上一句合并

    audio_opt = []
    # if not ref_free:
    #     phones1, bert1, _ = get_phones_and_bert(prompt_text, bert_tokenizer, bert_model, prompt_language, is_half)

    for text_idx, text in enumerate(texts):

        if process_bar is not None:
            percent_complete = (text_idx + 1) / len(texts)
            process_bar.progress(percent_complete, text=f"正在生成语音 {round(percent_complete * 100, 2)} % ...")

        # 解决输入目标文本的空行导致报错的问题
        if len(text.strip()) == 0:
            continue
        if text[-1] not in symbol_splits:
            text += "。" if text_language != "en" else "."
        print("=" * 20, "\n实际输入的目标文本(每句):", text)
        phones2, bert2, norm_text2 = get_phones_and_bert(text, bert_tokenizer, bert_model, text_language, is_half)
        print("=" * 20, "\n前端处理后的文本(每句):", norm_text2)

        if not ref_free:
            bert = torch.cat([bert1, bert2], 1)
            all_phoneme_ids = torch.LongTensor(phones1 + phones2).to(DEVICE).unsqueeze(0)
        else:
            pass
            # bert = bert2
            # all_phoneme_ids = torch.LongTensor(phones2).to(DEVICE).unsqueeze(0)

        bert = bert.to(DEVICE).unsqueeze(0)
        all_phoneme_len = torch.tensor([all_phoneme_ids.shape[-1]]).to(DEVICE)

        with torch.no_grad():
            pred_semantic, idx = t2s_model.model.infer_panel(
                all_phoneme_ids,
                all_phoneme_len,
                None if ref_free else prompt,
                bert,
                top_k=top_k,
                top_p=top_p,
                temperature=temperature,
                early_stop_num=HZ * max_sec,
            )
        pred_semantic = pred_semantic[:, -idx:].unsqueeze(0)  # .unsqueeze(0) # mq要多unsqueeze一次

        # audio = vq_model.decode(pred_semantic, all_phoneme_ids, refer).detach().cpu().numpy()[0, 0]
        audio = (
            vq_model.decode(pred_semantic, torch.LongTensor(phones2).to(DEVICE).unsqueeze(0), refer).detach().cpu().numpy()[0, 0]
        )  ###试试重建不带上prompt部分
        max_audio = np.abs(audio).max()  # 简单防止 16bit 爆音
        if max_audio > 1:
            audio /= max_audio
        audio_opt.append(audio)
        audio_opt.append(zero_wav)

    return hps.data.sampling_rate, (np.concatenate(audio_opt, 0) * 32768).astype(np.int16)


def split_txt(todo_text):
    """根据 symbol_splits 标点切分句子

    Args:
        todo_text (str): 原文本

    Returns:
        list: 切后的文本 list
    """

    todo_text = todo_text.replace("……", "。").replace("——", "，")

    if todo_text[-1] not in symbol_splits:
        todo_text += "。"  # 尾部加入 。

    i_split_head = i_split_tail = 0
    len_text = len(todo_text)
    todo_texts = []
    while 1:
        if i_split_head >= len_text:
            break  # 结尾一定有标点，所以直接跳出即可，最后一段在上次已加入
        if todo_text[i_split_head] in symbol_splits:
            i_split_head += 1
            todo_texts.append(todo_text[i_split_tail:i_split_head])
            i_split_tail = i_split_head
        else:
            i_split_head += 1
    return todo_texts


def cut_sentences(input_text, how_to_cut):

    inp = input_text.strip("\n")

    if how_to_cut == "凑四句一切":
        inps = split_txt(inp)  # 根据标点符号直接切
        split_idx = list(range(0, len(inps), 4))
        split_idx[-1] = None
        if len(split_idx) > 1:
            opts = []
            for idx in range(len(split_idx) - 1):
                opts.append("".join(inps[split_idx[idx] : split_idx[idx + 1]]))
        else:
            opts = [inp]
        cut_txt = "\n".join(opts)

    elif how_to_cut == "凑50字一切":
        inps = split_txt(inp)
        if len(inps) < 2:
            return inp
        opts = []
        summ = 0
        tmp_str = ""
        for i in range(len(inps)):
            summ += len(inps[i])
            tmp_str += inps[i]
            if summ > 50:
                summ = 0
                opts.append(tmp_str)
                tmp_str = ""
        if tmp_str != "":
            opts.append(tmp_str)
        # print(opts)
        if len(opts) > 1 and len(opts[-1]) < 50:  ##如果最后一个太短了，和前一个合一起
            opts[-2] = opts[-2] + opts[-1]
            opts = opts[:-1]
        cut_txt = "\n".join(opts)

    elif how_to_cut == "按中文句号。切":
        cut_txt = "\n".join(["%s" % item for item in inp.strip("。").split("。")])

    elif how_to_cut == "按英文句号.切":
        cut_txt = "\n".join(["%s" % item for item in inp.strip(".").split(".")])

    elif how_to_cut == "按标点符号切":
        punds = r"[,.;?!、，。？！;：…]"
        items = re.split(f"({punds})", inp)
        mergeitems = ["".join(group) for group in zip(items[::2], items[1::2])]
        # 在句子不存在符号或句尾无符号的时候保证文本完整
        if len(items) % 2 == 1:
            mergeitems.append(items[-1])
        cut_txt = "\n".join(mergeitems)

    else:
        cut_txt = inp

    cut_txt = cut_txt.replace("\n\n", "\n")
    return cut_txt


def get_gpt_and_sovits_model_path(voice_character_name: str, tts_model_root: Path):
    gpt_path_list = [i for i in tts_model_root.glob(f"{voice_character_name}*.ckpt")]
    sovits_path_list = [i for i in tts_model_root.glob(f"{voice_character_name}*.pth")]

    if len(gpt_path_list) > 0 and len(sovits_path_list) > 0:
        return str(gpt_path_list[0]), str(sovits_path_list[0])
    else:
        return None, None


@dataclass
class HandlerTTS:
    bert_tokenizer: BertTokenizerFast
    bert_model: BertForMaskedLM
    ssl_model: CNHubert
    max_sec: KeyboardInterrupt
    t2s_model: Text2SemanticLightningModule
    vq_model: SynthesizerTrn
    hps: HParams
    inp_ref: str
    prompt_text: str
    prompt: torch.Tensor
    refer: torch.Tensor
    bert1: torch.Tensor
    phones1: list
    zero_wav: np.ndarray


@st.cache_resource
def get_tts_model(voice_character_name="艾丝妲", is_half=True):

    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    from huggingface_hub import hf_hub_download, snapshot_download

    # https://huggingface.co/baicai1145/GPT-SoVITS-STAR/tree/main
    tts_star_model_root = Path(WEB_CONFIGS.TTS_MODEL_DIR).joinpath("star")

    gpt_path, sovits_path = get_gpt_and_sovits_model_path(voice_character_name, tts_star_model_root)

    if gpt_path is None:
        if tts_star_model_root.exists():
            # 有可能中断了下载，先删除文件夹
            shutil.rmtree(tts_star_model_root)

        # 直接下载单个文件
        tts_model_dir = hf_hub_download(
            repo_id="baicai1145/GPT-SoVITS-STAR",
            filename=f"{voice_character_name}.zip",
            local_dir=str(tts_star_model_root),
        )

        # 解压
        os.system(f"cd {str(tts_star_model_root)} && unzip {voice_character_name}.zip")

    gpt_path, sovits_path = get_gpt_and_sovits_model_path(voice_character_name, tts_star_model_root)
    print(f"gpt_path dir = {gpt_path}")
    print(f"sovits_path dir = {sovits_path}")

    inf_name = "激动说话-列车巡游银河，我不一定都能帮上忙，但只要是花钱能解决的事，尽管和我说吧。.wav"
    prompt_text = inf_name.split("-")[-1].replace(".wav", "")
    ref_wav_path = Path(tts_star_model_root).joinpath("参考音频", inf_name)

    # https://huggingface.co/lj1995/GPT-SoVITS/tree/main
    tts_model_dir = snapshot_download(repo_id="lj1995/GPT-SoVITS", local_dir=Path(WEB_CONFIGS.TTS_MODEL_DIR).joinpath("pretrain"))
    cnhubert_base_path = os.path.join(tts_model_dir, "chinese-hubert-base")
    bert_path = os.path.join(tts_model_dir, "chinese-roberta-wwm-ext-large")

    print(f"cnhubert_base_path dir = {cnhubert_base_path}")
    print(f"bert_path dir = {bert_path}")

    print("Loading tts bert model...")
    bert_tokenizer = AutoTokenizer.from_pretrained(bert_path)
    bert_model = AutoModelForMaskedLM.from_pretrained(bert_path)
    if is_half:
        bert_model = bert_model.half()
    bert_model = bert_model.to(DEVICE)
    print("load tts bert model done!")

    print("Loading tts ssl model...")
    ssl_model = cnhubert.get_model(cnhubert_base_path)
    if is_half:
        ssl_model = ssl_model.half()
    ssl_model = ssl_model.to(DEVICE)
    print("load tts ssl model done !")

    max_sec, t2s_model = change_gpt_weights(gpt_path, is_half)
    vq_model, hps = change_sovits_weights(sovits_path, is_half)

    zero_wav = np.zeros(
        int(hps.data.sampling_rate * 0.3),
        dtype=np.float16 if is_half else np.float32,
    )
    print("=" * 20, "\n加载参考音频 。。。")
    t1 = time.time()
    with torch.no_grad():
        wav16k, sr = librosa.load(ref_wav_path, sr=16000)
        if wav16k.shape[0] > 160000 or wav16k.shape[0] < 48000:
            raise OSError("参考音频在3~10秒范围外，请更换！")
        wav16k = torch.from_numpy(wav16k)
        zero_wav_torch = torch.from_numpy(zero_wav)

        wav16k = wav16k.half()
        zero_wav_torch = zero_wav_torch.half()

        wav16k = wav16k.to(DEVICE)
        zero_wav_torch = zero_wav_torch.to(DEVICE)

        wav16k = torch.cat([wav16k, zero_wav_torch])
        ssl_content = ssl_model.model(wav16k.unsqueeze(0))["last_hidden_state"].transpose(1, 2)  # .float()
        codes = vq_model.extract_latent(ssl_content)

        prompt_semantic = codes[0, 0]
        prompt = prompt_semantic.unsqueeze(0).to(DEVICE)
    print("加载 参考音频 用时: ", time.time() - t1)

    t3 = time.time()
    refer = get_spepc(hps, ref_wav_path)
    if is_half:
        refer = refer.half()
    refer = refer.to(DEVICE)
    print("get_spepc 用时: ", time.time() - t3)

    ref_free = False
    dict_language = {
        "中文": "all_zh",  # 全部按中文识别
        "英文": "en",  # 全部按英文识别#######不变
        "日文": "all_ja",  # 全部按日文识别
        "中英混合": "zh",  # 按中英混合识别####不变
        "日英混合": "ja",  # 按日英混合识别####不变
        "多语种混合": "auto",  # 多语种启动切分识别语种
    }

    prompt_text = prompt_text.strip("\n")
    if prompt_text[-1] not in symbol_splits:
        prompt_text += "。"
    print("=" * 20, "\n音频参考文本:", prompt_text)

    if not ref_free:
        phones1, bert1, _ = get_phones_and_bert(prompt_text, bert_tokenizer, bert_model, dict_language["中英混合"], is_half)

    tts_handler = HandlerTTS(
        bert_tokenizer=bert_tokenizer,
        bert_model=bert_model,
        ssl_model=ssl_model,
        max_sec=max_sec,
        t2s_model=t2s_model,
        vq_model=vq_model,
        hps=hps,
        inp_ref=str(ref_wav_path),
        prompt_text=prompt_text,
        prompt=prompt,
        refer=refer,
        bert1=bert1,
        phones1=phones1,
        zero_wav=zero_wav,
    )

    return tts_handler


def gen_tts_wav(
    text,
    text_language,
    bert_tokenizer,
    bert_model,
    ssl_model,
    vq_model,
    hps,
    max_sec,
    t2s_model,
    inp_ref,
    prompt_text,
    prompt,
    refer,
    bert1,
    phones1,
    zero_wav,
    wav_path_output,
    how_to_cut="凑四句一切",  # ["不切", "凑四句一切", "凑50字一切", "按中文句号。切", "按英文句号.切", "按标点符号切"]
):

    process_bar = st.progress(0, text="正在生成语音...")

    # 推理
    sampling_rate, audio_data = get_tts_wav(
        text,
        text_language,
        bert_tokenizer,
        bert_model,
        ssl_model,
        vq_model,
        hps,
        max_sec,
        t2s_model,
        inp_ref,
        prompt,
        refer,
        bert1,
        phones1,
        zero_wav,
        prompt_text,
        prompt_language="中英混合",
        how_to_cut=how_to_cut,
        top_k=5,  # 0 ~ 100
        top_p=1,  # 0. ~ 1.
        temperature=1,  # 0. ~ 1.
        ref_free=False,
        is_half=True,
        process_bar=process_bar,
    )

    process_bar.progress(1, text=f"正在生成语音 100.00 % ...")
    process_bar.empty()

    # 保存
    wav = BytesIO()
    sf.write(wav, audio_data, sampling_rate, format="wav")
    wav.seek(0)

    with open(wav_path_output, "wb") as f:
        f.write(wav.getvalue())
    print("output:", wav_path_output)


def demo():

    # https://huggingface.co/baicai1145/GPT-SoVITS-STAR/tree/main
    gpt_path = "./work_dirs/gpt_sovits/weights/GPT_weights/艾丝妲-e10.ckpt"
    sovits_path = "./work_dirs/gpt_sovits/weights/SoVITS_weights/艾丝妲_e25_s925.pth"

    # https://huggingface.co/lj1995/GPT-SoVITS/tree/main
    cnhubert_base_path = "./work_dirs/gpt_sovits/weights/pretrained_models/chinese-hubert-base"
    bert_path = "./work_dirs/utils/tts/gpt_sovits/weights/pretrained_models/chinese-roberta-wwm-ext-large"

    inp_ref = r"./work_dirs/ref_wav/【开心】处理完之前的事情，这几天甚至都有空闲来车上转转了。.wav"

    bert_tokenizer, bert_model, ssl_model, max_sec, t2s_model, vq_model, hps = get_tts_model(
        bert_path, cnhubert_base_path, gpt_path, sovits_path, is_half=True
    )

    text = """哈喽哈喽，家人们好啊！今天呀，咱们这儿可是有大大的福利等着大家哦你们猜猜看是什么呢？没错啦，就是这款超级棒的本草精华洗发露啦！哎呀，我知道你们一定都想知道它的神奇之处吧？那就让小甜心来给你们一一揭秘吧💖

首先呢，这款洗发露的配方真的是超级温和的哦，就算是敏感肌的小仙女们也能安心使用呢！而且它还能深层清洁我们的头皮，把那些烦人的油脂和污垢通通赶走，让我们的头发更加清爽健康呢！💦💦

再来就是它的滋养效果啦，富含多种草本精华，轻轻一抹就能给我们的头皮提供满满的养分，让秀发更加乌黑亮丽，顺滑如丝哦！💖💖💖

还有啊，这款洗发露的泡沫真的是超级丰富呢！轻轻一挤就能挤出好多好多细腻绵密的泡沫来，洗起来既舒服又干净，感觉就像是在给我们的头发做SPA一样呢！💖💖💖

最后啊，这款洗发露还特别容易冲洗哦！用完之后轻轻一冲就能把泡沫全部冲洗干净，不会残留任何黏腻感，让你随时随地保持清爽状态哦！💦💦💦

而且呀，这款洗发露不仅适用于各种发质，无论是油性、干性还是混合性，都能轻松应对呢！所以家人们，无论你是哪种发质，只要用了这款洗发露，保证让你的头发焕发出前所未有的光彩哦！💖💖💖

好啦，家人们，这么一款集温和、深层清洁、滋养、丰富泡沫、易冲洗于一身的神级洗发露，你们是不是已经心动了呢？快来把它带回家吧，让你的秀发从此告别烦恼，迎接美丽新世界吧！💖💖💖"""
    text_language = "中英混合"

    gen_tts_wav(
        text,
        text_language,
        bert_tokenizer,
        bert_model,
        ssl_model,
        vq_model,
        hps,
        max_sec,
        t2s_model,
        inp_ref,
        wav_path_output=r"./work_dirs/tts_wavs/gpt-sovits-test.wav",
    )


if __name__ == "__main__":
    demo()
