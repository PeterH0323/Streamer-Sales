from pathlib import Path
from .realtime_inference import DIGITAL_HUMAN_HANDLER, gen_digital_human_preprocess, gen_digital_human_video
from ...web_configs import WEB_CONFIGS


async def gen_digital_human_video_app(stream_id, audio_path, save_tag):
    if DIGITAL_HUMAN_HANDLER is None:
        return None

    save_path = gen_digital_human_video(
        DIGITAL_HUMAN_HANDLER,
        stream_id,
        audio_path,
        work_dir=str(Path(WEB_CONFIGS.DIGITAL_HUMAN_VIDEO_OUTPUT_PATH).absolute()),
        video_path=save_tag,
        fps=DIGITAL_HUMAN_HANDLER.fps,
    )

    return save_path


async def preprocess_digital_human_app(stream_id, video_path):
    if DIGITAL_HUMAN_HANDLER is None:
        return None

    res = gen_digital_human_preprocess(
        DIGITAL_HUMAN_HANDLER,
        stream_id,
        work_dir=str(Path(WEB_CONFIGS.DIGITAL_HUMAN_VIDEO_OUTPUT_PATH).absolute()),
        video_path=video_path,
    )

    return res
