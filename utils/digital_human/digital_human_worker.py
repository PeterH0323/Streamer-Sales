from pathlib import Path
import streamlit as st
from utils.digital_human.realtime_inference import gen_digital_human_video


def show_video(video_path, autoplay=True, loop=False, muted=False):
    # 需要 fp25 才能显示
    with open(video_path, "rb") as f_wav:
        video_bytes = f_wav.read()

    print(f"Show video: {video_path}")
    st.video(video_bytes, format="video/mp4", autoplay=autoplay, loop=loop, muted=muted)


def gen_digital_human_video_in_spinner(audio_path):
    save_path = None
    if st.session_state.gen_digital_human_checkbox and st.session_state.digital_human_handler is not None:
        with st.spinner(
            "正在生成数字人，请稍等... 如果觉得生成时间太久，可以将侧边栏的【生成数字人】按钮取消选中，下次则不会生成"
        ):
            # save_tag = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".wav"

            # st.session_state.digital_human_video_path = gen_digital_human_video(
            #     video_path=st.session_state.digital_human_video_path,
            #     audio_path=audio_path,
            #     bbox_shift=st.session_state.digital_human_handler.bbox_shift,
            #     fps=st.session_state.digital_human_handler.fps,
            #     batch_size=8,
            #     use_float16=st.session_state.digital_human_handler.use_float16,
            #     infer_handler=st.session_state.digital_human_handler,
            # )

            st.session_state.digital_human_video_path = gen_digital_human_video(
                st.session_state.digital_human_handler,
                audio_path,
                work_dir=str(Path(st.session_state.digital_human_root).absolute()),
                video_path=st.session_state.digital_human_video_path,
                fps=st.session_state.digital_human_handler.model_handler.fps,
            )

            st.session_state.video_placeholder.empty()  # 清空
            with st.session_state.video_placeholder.container():
                show_video(st.session_state.digital_human_video_path)
            st.toast("生成数字人视频成功!")
    return save_path
