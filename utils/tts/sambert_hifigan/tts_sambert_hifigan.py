import streamlit as st
from modelscope.outputs import OutputKeys
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

# pip install kantts -f https://modelscope.oss-cn-beijing.aliyuncs.com/releases/repo.html
# pip install pytorch_wavelets tensorboardX scipy==1.12.0


@st.cache_resource
def get_tts_model():
    model_id = "damo/speech_sambert-hifigan_tts_zhisha_zh-cn_16k"
    sambert_hifigan_tts = pipeline(task=Tasks.text_to_speech, model=model_id)
    return sambert_hifigan_tts


def gen_tts_wav(sambert_hifigan_tts, text, wav_path):
    # wav_path = 'output.wav'
    # text = '哈喽哈喽，家人们好啊！今天呀，咱们这儿可是有大大的福利等着大家哦你们猜猜看是什么呢？没错啦，就是这款超级棒哒【声波电动牙刷】啦！哎呀，我知道你们肯定都用过电动牙刷的，但是这款真的是太不一样了哦让我来给你们一一揭秘吧首先呢，它的【高效清洁】功能绝对是业界领先的哦，无论是顽固牙渍还是口腔死角，都能轻松搞定，让你们的牙齿每天都亮晶晶滴而且啊，它还有【减少手动压力】的设计，再也不用担心手酸手疼啦，轻轻松松就能拥有健康洁白的好笑容哦对了，还有【定时提醒】这个功能，再也不用担心刷牙时间不够啦，让你随时随地保持口腔卫生哦最厉害的是，它还有【智能模式调节】和【无线充电】的功能呢，简直是科技感爆棚哦而且，它的【噪音低】设计，就算是深夜刷牙也不会打扰到家人啦家人们，这样的电动牙刷是不是超级心动呢？快来把它带回家吧，让你的每一天都充满活力和好心情哦'
    print(f"gerning tts for {wav_path} ....")
    output = sambert_hifigan_tts(input=text)
    wav = output[OutputKeys.OUTPUT_WAV]
    with open(wav_path, "wb") as f:
        f.write(wav)
    print(f"gen tts for {wav_path} done!....")
