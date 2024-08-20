from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from ..utils import ResultCode, make_return_data

router = APIRouter(
    prefix="/digital-human",
    tags=["digital-human"],
    responses={404: {"description": "Not found"}},
)


class GenDigitalHumanVideoItem(BaseModel):
    salesDoc: str


@router.post("/gen")
async def get_digital_human_according_doc_api(gen_item: GenDigitalHumanVideoItem):
    """根据口播文案生成数字人介绍视频

    Args:
        gen_item (GenDigitalHumanVideoItem): _description_

    """
    logger.info(gen_item.salesDoc)

    video_path = "https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-360p.mp4"

    # 生成 TTS wav

    # 生成 数字人视频

    return make_return_data(True, ResultCode.SUCCESS, "成功", video_path)
