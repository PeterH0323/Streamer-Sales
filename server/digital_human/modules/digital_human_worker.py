from pathlib import Path
from .realtime_inference import DIGITAL_HUMAN_HANDLER, gen_digital_human_video
from ...web_configs import WEB_CONFIGS


async def gen_digital_human_video_app(audio_path, save_tag):
    if DIGITAL_HUMAN_HANDLER is None:
        return None

    save_path = gen_digital_human_video(
        DIGITAL_HUMAN_HANDLER,
        audio_path,
        work_dir=str(Path(WEB_CONFIGS.DIGITAL_HUMAN_VIDEO_OUTPUT_PATH).absolute()),
        video_path=save_tag,
        fps=DIGITAL_HUMAN_HANDLER.model_handler.fps,
    )

    return save_path
