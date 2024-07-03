import copy
from datetime import datetime
import glob
import json
import os
import pickle
import queue
import shutil
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
import streamlit as st
import torch
import wget
from tqdm import tqdm

from utils.digital_human.musetalk.models.unet import PositionalEncoding, UNet
from utils.digital_human.musetalk.models.vae import VAE
from utils.digital_human.musetalk.utils.blending import get_image_blending, get_image_prepare_material, init_face_parsing_model
from utils.digital_human.musetalk.utils.face_parsing import FaceParsing
from utils.digital_human.musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs
from utils.digital_human.musetalk.utils.utils import datagen, load_all_model
from utils.digital_human.musetalk.whisper.audio2feature import Audio2Feature


def setup_ffmpeg_env(model_dir):
    # wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
    # xz -d ffmpeg-release-amd64-static.tar.xz
    # tar -xvf ffmpeg-release-amd64-static.tar

    ffmpeg_file_name = "ffmpeg-release-amd64-static"
    ffmpeg_root = Path(model_dir).joinpath(f"drivers").absolute()
    Path(ffmpeg_root).mkdir(exist_ok=True, parents=True)

    ffmpeg_dir = None
    for ffmpeg_dir_path in Path(ffmpeg_root).iterdir():
        if not ffmpeg_dir_path.is_dir():
            continue
        ffmpeg_dir = str(ffmpeg_dir_path)

    if ffmpeg_dir is None:
        os.system(
            f"cd {str(ffmpeg_root)} && wget https://johnvansickle.com/ffmpeg/releases/{ffmpeg_file_name}.tar.xz && xz -d {ffmpeg_file_name}.tar.xz && tar -xvf {ffmpeg_file_name}.tar"
        )

    for ffmpeg_dir_path in Path(ffmpeg_root).iterdir():
        if not ffmpeg_dir_path.is_dir():
            continue
        ffmpeg_dir = str(ffmpeg_dir_path)
        break
    print(f"setting ffmpeg dir: {ffmpeg_dir}")
    if str(ffmpeg_dir) not in os.getenv("PATH"):
        print(f"add ffmpeg to path : {str(ffmpeg_dir)}")
        os.environ["PATH"] = f"{str(ffmpeg_dir)}:{os.environ['PATH']}"


def init_digital_model(model_dir, use_float16=False):

    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    from huggingface_hub import snapshot_download

    # 直接下载单个文件
    muse_talk_model_path = snapshot_download(repo_id="TMElyralab/MuseTalk", local_dir=model_dir)
    sd_model_path = snapshot_download(repo_id="stabilityai/sd-vae-ft-mse", local_dir=Path(model_dir).joinpath("sd-vae-ft-mse"))

    whisper_pth_path = Path(model_dir).joinpath(r"whisper/tiny.pt")
    whisper_pth_path.parent.mkdir(parents=True, exist_ok=True)
    if not whisper_pth_path.exists():

        wget.download(
            url="https://openaipublic.azureedge.net/main/whisper/models/65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9/tiny.pt",
            out=str(whisper_pth_path),
        )

    # load model weights
    print("Loading models...")
    audio_processor, vae, unet, pe = load_all_model(
        audio2feature_model_path=str(whisper_pth_path),
        vae_model_path=sd_model_path,
        unet_model_dict={
            "unet_config": str(Path(muse_talk_model_path).joinpath("musetalk", "musetalk.json")),
            "model_path": str(Path(muse_talk_model_path).joinpath("musetalk", "pytorch_model.bin")),
        },
    )

    if use_float16 is True:
        pe = pe.half()
        vae.vae = vae.vae.half()
        unet.model = unet.model.half()
    print("Loaded models done !...")
    return audio_processor, vae, unet, pe


def load_pose_model(model_dir):

    from mmpose.apis import init_model

    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    from huggingface_hub import hf_hub_download

    # 直接下载单个文件
    dw_pose_path = hf_hub_download(
        repo_id="yzd-v/DWPose",
        filename="dw-ll_ucoco_384.pth",
        local_dir=Path(model_dir).joinpath("dwpose"),
    )

    config_file = r"./utils/digital_human/musetalk/utils/dwpose/rtmpose-l_8xb32-270e_coco-ubody-wholebody-384x288.py"
    pose_model = init_model(config_file, dw_pose_path, device="cuda")

    return pose_model


def load_face_parsing_model(model_dir):

    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    from huggingface_hub import hf_hub_download

    model_dir = Path(model_dir).joinpath("face-parse-bisent")
    model_dir.mkdir(parents=True, exist_ok=True)

    resnet_path = Path(model_dir).joinpath("resnet18-5c106cde.pth")
    if not resnet_path.exists():

        wget.download(
            url="https://download.pytorch.org/models/resnet18-5c106cde.pth",
            out=str(resnet_path),
        )

    # 79999_iter.pth 地址: https://drive.google.com/open?id=154JgKpzCPW82qINcVieuPH3fZ2e0P812
    # 非官方
    _ = hf_hub_download(
        repo_id="ManyOtherFunctions/face-parse-bisent",
        filename="79999_iter.pth",
        local_dir=str(model_dir),
    )

    face_parsing_model = init_face_parsing_model(
        resnet_path=str(resnet_path),
        face_model_pth=Path(model_dir).joinpath("79999_iter.pth"),
    )
    return face_parsing_model


def video2imgs(vid_path, save_path, ext=".png", cut_frame=10000000):
    cap = cv2.VideoCapture(vid_path)
    count = 0
    while True:
        if count > cut_frame:
            break
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(f"{save_path}/{count:08d}.png", frame)
            count += 1
        else:
            break


def osmakedirs(path_list):
    for path in path_list:
        os.makedirs(path) if not os.path.exists(path) else None


@dataclass
class HandlerDigitalHuman:
    audio_processor: Optional[Audio2Feature] = None
    vae: Optional[VAE] = None
    unet: Optional[UNet] = None
    pe: Optional[PositionalEncoding] = None
    face_parsing_model: Optional[FaceParsing] = None
    frame_list_cycle: Optional[List] = None
    coord_list_cycle: Optional[List] = None
    input_latent_list_cycle: Optional[List] = None
    mask_coords_list_cycle: Optional[List] = None
    mask_list_cycle: Optional[List] = None
    fps: int = 25
    bbox_shift: int = 0
    use_float16: bool = False


@torch.no_grad()
class Avatar:
    def __init__(self, avatar_id, work_dir, model_dir, video_path, bbox_shift, batch_size, fps, preparation_force):
        self.avatar_id = avatar_id
        self.video_path = video_path
        self.bbox_shift = bbox_shift
        self.avatar_path = work_dir
        self.model_dir = model_dir
        self.full_imgs_path = f"{self.avatar_path}/full_imgs"
        self.coords_path = f"{self.avatar_path}/coords.pkl"
        self.latents_out_path = f"{self.avatar_path}/latents.pt"
        self.video_out_path = f"{self.avatar_path}/vid_output/"
        self.mask_out_path = f"{self.avatar_path}/mask"
        self.mask_coords_path = f"{self.avatar_path}/mask_coords.pkl"
        self.avatar_info_path = f"{self.avatar_path}/avator_info.json"
        self.avatar_info = {"avatar_id": avatar_id, "video_path": video_path, "bbox_shift": bbox_shift}
        self.preparation_force = preparation_force
        self.batch_size = batch_size
        self.idx = 0

        # 模型初始化，防止 pose 导致 OOM，放到最后加载
        face_parsing_model = load_face_parsing_model(self.model_dir)
        audio_processor, vae, unet, pe = init_digital_model(self.model_dir, use_float16=False)
        pe = pe.half()
        vae.vae = vae.vae.half()
        unet.model = unet.model.half()

        self.init(vae_model=vae, face_parsing_model=face_parsing_model)

        self.model_handler = HandlerDigitalHuman(
            audio_processor=audio_processor,
            vae=vae,
            unet=unet,
            pe=pe,
            face_parsing_model=face_parsing_model,
            frame_list_cycle=self.frame_list_cycle,
            coord_list_cycle=self.coord_list_cycle,
            input_latent_list_cycle=self.input_latent_list_cycle,
            mask_coords_list_cycle=self.mask_coords_list_cycle,
            mask_list_cycle=self.mask_list_cycle,
            fps=fps,
            bbox_shift=bbox_shift,
        )

    def init(self, vae_model, face_parsing_model):
        need_to_prepare = False

        if self.preparation_force and os.path.exists(self.avatar_path):
            shutil.rmtree(self.avatar_path)
            need_to_prepare = True
        elif not os.path.exists(self.avatar_path):
            # 预处理文件不存在，需要进行预处理
            need_to_prepare = True
        elif os.path.exists(self.avatar_path):
            # 预处理文件存在，判断 bbox_shift 是否匹配，不匹配需要重新进行预处理
            with open(self.avatar_info_path, "r") as f:
                avatar_info = json.load(f)
            if avatar_info["bbox_shift"] != self.avatar_info["bbox_shift"]:
                need_to_prepare = True
                shutil.rmtree(self.avatar_path)

        if need_to_prepare is False:
            # 对文件再进行一个判断，避免中途出错导致文件没生成全
            for prepare_file in [
                self.full_imgs_path,
                self.coords_path,
                self.latents_out_path,
                self.video_out_path,
                self.mask_out_path,
                self.mask_coords_path,
                self.avatar_info_path,
            ]:
                if not os.path.exists(prepare_file):
                    # 如有文件不存在，则需要重新生成
                    print(f"Missing file {prepare_file}, will process prerpare...")
                    need_to_prepare = True
                    shutil.rmtree(self.avatar_path)
                    break

        if need_to_prepare:
            print("*********************************")
            print(f"  creating avator: {self.avatar_id}")
            print("*********************************")
            osmakedirs([self.avatar_path, self.full_imgs_path, self.video_out_path, self.mask_out_path])
            self.prepare_material(vae_model=vae_model, face_parsing_model=face_parsing_model)

        self.input_latent_list_cycle = torch.load(self.latents_out_path)
        with open(self.coords_path, "rb") as f:
            self.coord_list_cycle = pickle.load(f)
        input_img_list = glob.glob(os.path.join(self.full_imgs_path, "*.[jpJP][pnPN]*[gG]"))
        input_img_list = sorted(input_img_list, key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
        self.frame_list_cycle = read_imgs(input_img_list)
        with open(self.mask_coords_path, "rb") as f:
            self.mask_coords_list_cycle = pickle.load(f)
        input_mask_list = glob.glob(os.path.join(self.mask_out_path, "*.[jpJP][pnPN]*[gG]"))
        input_mask_list = sorted(input_mask_list, key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
        self.mask_list_cycle = read_imgs(input_mask_list)

    def prepare_material(self, vae_model, face_parsing_model):
        print("preparing data materials ... ...")
        with open(self.avatar_info_path, "w") as f:
            json.dump(self.avatar_info, f)

        if os.path.isfile(self.video_path):
            video2imgs(self.video_path, self.full_imgs_path, ext="png")
        else:
            print(f"copy files in {self.video_path}")
            files = os.listdir(self.video_path)
            files.sort()
            files = [file for file in files if file.split(".")[-1] == "png"]
            for filename in files:
                shutil.copyfile(f"{self.video_path}/{filename}", f"{self.full_imgs_path}/{filename}")
        input_img_list = sorted(glob.glob(os.path.join(self.full_imgs_path, "*.[jpJP][pnPN]*[gG]")))

        print("extracting landmarks...")
        pose_model = load_pose_model(self.model_dir)
        coord_list, frame_list = get_landmark_and_bbox(input_img_list, pose_model, self.bbox_shift)
        del pose_model

        input_latent_list = []
        idx = -1
        # maker if the bbox is not sufficient
        coord_placeholder = (0.0, 0.0, 0.0, 0.0)
        for bbox, frame in zip(coord_list, frame_list):
            idx = idx + 1
            if bbox == coord_placeholder:
                continue
            x1, y1, x2, y2 = bbox
            crop_frame = frame[y1:y2, x1:x2]
            resized_crop_frame = cv2.resize(crop_frame, (256, 256), interpolation=cv2.INTER_LANCZOS4)
            latents = vae_model.get_latents_for_unet(resized_crop_frame)
            input_latent_list.append(latents)

        self.frame_list_cycle = frame_list + frame_list[::-1]
        self.coord_list_cycle = coord_list + coord_list[::-1]
        self.input_latent_list_cycle = input_latent_list + input_latent_list[::-1]
        self.mask_coords_list_cycle = []
        self.mask_list_cycle = []

        for i, frame in enumerate(tqdm(self.frame_list_cycle)):
            cv2.imwrite(f"{self.full_imgs_path}/{str(i).zfill(8)}.png", frame)

            face_box = self.coord_list_cycle[i]
            mask, crop_box = get_image_prepare_material(frame, face_box, face_parsing_model)
            cv2.imwrite(f"{self.mask_out_path}/{str(i).zfill(8)}.png", mask)
            self.mask_coords_list_cycle += [crop_box]
            self.mask_list_cycle.append(mask)

        with open(self.mask_coords_path, "wb") as f:
            pickle.dump(self.mask_coords_list_cycle, f)

        with open(self.coords_path, "wb") as f:
            pickle.dump(self.coord_list_cycle, f)

        torch.save(self.input_latent_list_cycle, os.path.join(self.latents_out_path))

    def process_frames(self, res_frame_queue, video_len, skip_save_images, save_dir_name):
        print(video_len)
        while True:
            if self.idx >= video_len - 1:
                break
            try:
                res_frame = res_frame_queue.get(block=True, timeout=1)
            except queue.Empty:
                continue

            bbox = self.coord_list_cycle[self.idx % (len(self.coord_list_cycle))]
            ori_frame = copy.deepcopy(self.frame_list_cycle[self.idx % (len(self.frame_list_cycle))])
            x1, y1, x2, y2 = bbox
            try:
                res_frame = cv2.resize(res_frame.astype(np.uint8), (x2 - x1, y2 - y1))
            except:
                continue
            mask = self.mask_list_cycle[self.idx % (len(self.mask_list_cycle))]
            mask_crop_box = self.mask_coords_list_cycle[self.idx % (len(self.mask_coords_list_cycle))]
            # combine_frame = get_image(ori_frame,res_frame,bbox)
            combine_frame = get_image_blending(ori_frame, res_frame, bbox, mask, mask_crop_box)

            if skip_save_images is False:
                cv2.imwrite(f"{self.avatar_path}/{save_dir_name}/{str(self.idx).zfill(8)}.png", combine_frame)
            self.idx = self.idx + 1

    def inference(self, audio_path, output_vid, fps, skip_save_images=False):

        tmp_tag = "tmp_" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

        os.makedirs(self.avatar_path + f"/{tmp_tag}", exist_ok=True)
        print("start inference")
        ############################################## extract audio feature ##############################################
        start_time = time.time()
        whisper_feature = self.model_handler.audio_processor.audio2feat(audio_path)
        whisper_chunks = self.model_handler.audio_processor.feature2chunks(feature_array=whisper_feature, fps=fps)
        print(f"processing audio:{audio_path} costs {(time.time() - start_time) * 1000}ms")
        ############################################## inference batch by batch ##############################################
        video_num = len(whisper_chunks)
        res_frame_queue = queue.Queue()
        self.idx = 0
        # # Create a sub-thread and start it
        process_thread = threading.Thread(
            target=self.process_frames, args=(res_frame_queue, video_num, skip_save_images, tmp_tag)
        )
        process_thread.start()

        gen = datagen(whisper_chunks, self.input_latent_list_cycle, self.batch_size)
        start_time = time.time()

        for i, (whisper_batch, latent_batch) in enumerate(tqdm(gen, total=int(np.ceil(float(video_num) / self.batch_size)))):
            audio_feature_batch = torch.from_numpy(whisper_batch)
            audio_feature_batch = audio_feature_batch.to(
                device=self.model_handler.unet.device, dtype=self.model_handler.unet.model.dtype
            )
            audio_feature_batch = self.model_handler.pe(audio_feature_batch)
            latent_batch = latent_batch.to(dtype=self.model_handler.unet.model.dtype)

            timesteps = torch.tensor([0], device="cuda")
            pred_latents = self.model_handler.unet.model(
                latent_batch, timesteps, encoder_hidden_states=audio_feature_batch
            ).sample
            recon = self.model_handler.vae.decode_latents(pred_latents)
            for res_frame in recon:
                res_frame_queue.put(res_frame)
        # Close the queue and sub-thread after all tasks are completed
        process_thread.join()

        print("Total process time of {} frames including saving images = {}s".format(video_num, time.time() - start_time))

        cmd_img2video = f"ffmpeg -y -v warning -r {fps} -f image2 -i {self.avatar_path}/{tmp_tag}/%08d.png -vcodec libx264 -vf format=rgb24,scale=out_color_matrix=bt709,format=yuv420p -crf 18 {self.avatar_path}/{tmp_tag}.mp4"
        print(cmd_img2video)
        os.system(cmd_img2video)

        # output_vid = os.path.join(self.video_out_path, out_vid_name + ".mp4")  # on
        cmd_combine_audio = f"ffmpeg -y -v warning -i {audio_path} -i {self.avatar_path}/{tmp_tag}.mp4 {output_vid}"
        print(cmd_combine_audio)
        os.system(cmd_combine_audio)

        os.remove(f"{self.avatar_path}/{tmp_tag}.mp4")
        shutil.rmtree(f"{self.avatar_path}/{tmp_tag}")
        print(f"result is save to {output_vid}")

        return str(output_vid)


@st.cache_resource
def digital_human_preprocess(model_dir, use_float16, video_path, work_dir, fps, bbox_shift):

    avatar = Avatar(
        avatar_id="lelemiao",
        work_dir=work_dir,
        model_dir=model_dir,
        video_path=video_path,
        bbox_shift=bbox_shift,
        batch_size=8,
        fps=fps,
        preparation_force=False,
    )

    setup_ffmpeg_env(model_dir)

    return avatar


@torch.no_grad()
def gen_digital_human_video(
    avatar_handler: Avatar,
    audio_path,
    work_dir,
    video_path,
    fps,
):
    output_vid_image_dir = Path(avatar_handler.video_out_path).joinpath(f"{Path(video_path).stem}+{Path(audio_path).stem}")
    output_vid_file_path = output_vid_image_dir.with_suffix(".mp4")
    output_vid = avatar_handler.inference(
        audio_path=audio_path,  # wav file
        output_vid=str(output_vid_file_path),
        fps=fps,
        skip_save_images=False,
    )

    return output_vid


if __name__ == "__main__":

    data_preparation = False
    video_path = "./work_dirs/tts_wavs/2024-06-05-20-48-53.wav"
    bbox_shift = 5
    avatar = Avatar(
        avatar_id="lelemiao", video_path=video_path, bbox_shift=bbox_shift, batch_size=4, preparation=data_preparation
    )

    avatar.inference(
        audio_path=r"./work_dirs/tts_wavs/2024-06-05-20-48-53.wav",
        out_vid_name="avatar_1",
        fps=25,
        skip_save_images=False,
    )
