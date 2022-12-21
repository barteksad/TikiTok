# !pip install av
# ! wget https://raw.githubusercontent.com/pytorch/vision/6de158c473b83cf43344a0651d7c01128c7850e6/references/video_classification/transforms.py
# ! pip install git+https://github.com/Atze00/MoViNet-pytorch.git
#
from typing import Dict

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import requests
import tempfile
import numpy as np
import torchvision
import torch.nn.functional as F
import torchvision.transforms as transforms
import torch
import transforms as T
from movinets import MoViNet
from movinets.config import _C

MAX_FPS = 5  # MoViNet-A0 should be given inputs with 5 frames per second (FPS).
TOP_K = 3

MODEL = MoViNet(_C.MODEL.MoViNetA0, pretrained=True)
MODEL.eval()

BUNNY_CND_PULL_ZONE = "vz-80e5d374-0a6"
VIDEO_ID = "6f37c274-4742-4953-b401-57b4ded16ebd"

MODEL_PREPROCESS = transforms.Compose([
    T.ToFloatTensorInZeroOne(),
    T.Resize((200, 200)),
    T.CenterCrop((172, 172))])


def download_video(video_id: int) -> requests.Response:
    url = f"https://{BUNNY_CND_PULL_ZONE}.b-cdn.net/{video_id}/original"
    return requests.get(url)


def read_class_labels() -> np.array:
    """Returns array of names associated with 600 Kinetics600 classes."""
    labels_file = open("kinetics_600.txt", "r")
    # Numpy array for easy masking.
    return np.array(labels_file.read().split('\n'))


def reduce_fps(vid: torch.Tensor, vid_metadata: Dict) -> torch.Tensor:
    """
        Selects frames to reduce video's FPS to at most MAX_FPS.
        Returns selected frames of the video.
    """
    fps = int(vid_metadata['video_fps'])
    frames_cnt = vid.size()[0]

    selected_frames_cnt = min(frames_cnt, frames_cnt * MAX_FPS // fps)
    selected_frames = torch.linspace(start=0,
                                     end=frames_cnt - 1,
                                     steps=selected_frames_cnt,
                                     dtype=torch.long)
    return vid[selected_frames]



try:
    labels = read_class_labels()

    # Download the video from CDN.
    x = download_video(VIDEO_ID)
    print(x)

    # Save the downloaded video to a temp file
    # to easily read it with torchvision.
    with tempfile.NamedTemporaryFile() as fp, torch.no_grad():
        fp.write(x.content)

        video, _, metadata = torchvision.io.read_video(fp.name)
        # video has shape (frames, height, width, colors)

        video = reduce_fps(video, metadata)
        video = MODEL_PREPROCESS(video)

        #
        # fig, ax = plt.subplots()
        # frames = [[ax.imshow(video[0][i])] for i in range(video.size()[1])]
        #
        # ani = animation.ArtistAnimation(fig, frames, interval=200, blit=True, repeat_delay=1000)
        #
        # plt.show()

        video_batch = torch.unsqueeze(video, 0)
        output = F.log_softmax(MODEL(video_batch), dim=1)
        _, predicted_classes = torch.topk(output, dim=1, k=TOP_K)
        print(f"Video {VIDEO_ID} predictions: {labels[predicted_classes]}")
except Exception as e:
    print(e)
