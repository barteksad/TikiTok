# !pip install av
# ! wget https://raw.githubusercontent.com/pytorch/vision/6de158c473b83cf43344a0651d7c01128c7850e6/references/video_classification/transforms.py
# ! pip install git+https://github.com/Atze00/MoViNet-pytorch.git
#
from typing import Dict

import tempfile
import numpy as np
import torchvision
from torch.nn.functional import log_softmax
import torchvision.transforms as transforms
import torch
from movinets import transforms as T
from movinets.models import MoViNet
from movinets.config import _C

MAX_FPS = 5  # MoViNet-A0 should be given inputs with 5 frames per second (FPS).
TOP_K = 3

MODEL = MoViNet(_C.MODEL.MoViNetA0, pretrained=True)
MODEL.eval()

MODEL_PREPROCESS = transforms.Compose([
    T.ToFloatTensorInZeroOne(),
    T.Resize((200, 200)),
    T.CenterCrop((172, 172))])


def read_class_labels() -> np.array:
    """Returns array of names associated with 600 Kinetics600 classes."""
    labels_file = open("kinetics_600.txt", "r")
    # Numpy array for easy masking.
    return np.array(labels_file.read().split('\n'))


LABELS = read_class_labels()


def reduce_fps(video: torch.Tensor, metadata: Dict) -> torch.Tensor:
    """
        Selects frames to reduce video's FPS to at most MAX_FPS.
        Returns selected frames of the video.
    """
    fps = int(metadata['video_fps'])
    frames_cnt = video.size()[0]

    selected_frames_cnt = min(frames_cnt, frames_cnt * MAX_FPS // fps)
    selected_frames = torch.linspace(start=0,
                                     end=frames_cnt - 1,
                                     steps=selected_frames_cnt,
                                     dtype=torch.long)
    return video[selected_frames]


def process_video(video_id: str, raw_video_content: bytes) -> np.array:
    # Save the video to a temp file
    # to easily read it with torchvision.
    # TODO: check how to do it without saving to file.
    with tempfile.NamedTemporaryFile() as fp, torch.no_grad():
        fp.write(raw_video_content)

        video, _, metadata = torchvision.io.read_video(fp.name)
        # video has shape (frames, height, width, colors)

        video = reduce_fps(video, metadata)
        video = MODEL_PREPROCESS(video)

        video_batch = torch.unsqueeze(video, 0)
        output = log_softmax(MODEL(video_batch), dim=1)
        _, predicted_classes = torch.topk(output, dim=1, k=TOP_K)

        print(f"Video {video_id} predictions: {LABELS[predicted_classes]}")
        return predicted_classes[0]

