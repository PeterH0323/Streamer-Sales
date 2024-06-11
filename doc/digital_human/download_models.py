import os

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from huggingface_hub import hf_hub_download

COMFYUI_PATH = r"/path/to/ComfyUI"

# ==============================================
#                官方 SD 权重
# ==============================================
hf_hub_download(
    repo_id="stabilityai/stable-diffusion-xl-base-1.0",
    filename="sd_xl_base_1.0.safetensors",
    local_dir=rf"{COMFYUI_PATH}/models/checkpoints",
)

hf_hub_download(
    repo_id="runwayml/stable-diffusion-v1-5",
    filename="v1-5-pruned.safetensors",
    local_dir=rf"{COMFYUI_PATH}/models/checkpoints",
)

# ==============================================
#                AnimateDiff 权重
# ==============================================
for animatediff_model in ["mm_sd_v15_v2.ckpt", "mm_sdxl_v10_beta.ckpt", "v3_sd15_mm.ckpt"]:
    hf_hub_download(
        repo_id="guoyww/animatediff",
        filename=animatediff_model,
        local_dir=rf"{COMFYUI_PATH}/models/animatediff_models",
    )

for animatediff_model in ["temporaldiff-v1-animatediff.safetensors"]:
    hf_hub_download(
        repo_id="CiaraRowles/TemporalDiff",
        filename=animatediff_model,
        local_dir=rf"{COMFYUI_PATH}/models/animatediff_models",
    )

for lora_model in [
    "v2_lora_PanLeft.ckpt",
    "v2_lora_PanRight.ckpt",
    "v2_lora_RollingAnticlockwise.ckpt",
    "v2_lora_RollingClockwise.ckpt",
    "v2_lora_TiltDown.ckpt",
    "v2_lora_TiltUp.ckpt",
    "v2_lora_ZoomIn.ckpt",
    "v2_lora_ZoomOut.ckpt",
]:
    hf_hub_download(
        repo_id="guoyww/animatediff",
        filename=lora_model,
        local_dir=rf"{COMFYUI_PATH}/models/animatediff_motion_lora",
    )

# ==============================================
#                ControlNet 权重
# ==============================================
for controlnet_model in ["control_v11p_sd15_openpose.pth", "control_v11f1p_sd15_depth.pth", "control_v11p_sd15_seg.pth"]:
    hf_hub_download(
        repo_id="lllyasviel/ControlNet-v1-1",
        filename=controlnet_model,
        local_dir=rf"{COMFYUI_PATH}/models/controlnet",
    )

# ==============================================
#                   SAM 权重
# ==============================================
for sam_model in ["groundingdino_swinb_cogcoor.pth", "GroundingDINO_SwinB.cfg.py"]:
    hf_hub_download(
        repo_id="ShilongLiu/GroundingDINO",
        filename=sam_model,
        local_dir=rf"{COMFYUI_PATH}/models/grounding-dino/",
    )

# ==============================================
#                   IP-Adapter 权重
# ==============================================
for ip_adapter_model in ["models/ip-adapter-plus_sd15.safetensors"]:
    hf_hub_download(
        repo_id="h94/IP-Adapter",
        filename=ip_adapter_model,
        local_dir=rf"{COMFYUI_PATH}/models/ipadapter",
    )

for ip_adapter_clip_model in ["models/image_encoder/model.safetensors"]:
    hf_hub_download(
        repo_id="h94/IP-Adapter",
        filename=ip_adapter_clip_model,
        local_dir=rf"{COMFYUI_PATH}/models/clip_vision/",
    )
