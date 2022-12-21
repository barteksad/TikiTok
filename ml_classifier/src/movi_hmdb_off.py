# !pip install av
# ! wget https://raw.githubusercontent.com/pytorch/vision/6de158c473b83cf43344a0651d7c01128c7850e6/references/video_classification/transforms.py
# ! pip install git+https://github.com/Atze00/MoViNet-pytorch.git
#

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import requests
import tempfile
import numpy
import torchvision
import torch.nn.functional as F
import torchvision.transforms as transforms
import torch
import transforms as T
from movinets import MoViNet
from movinets.config import _C

MAX_FPS = 5  # MoViNet-A0 should be given inputs with 5 frames per second (FPS).
TOP_K = 3  # TODO: choose k

BUNNY_CND_PULL_ZONE = "vz-80e5d374-0a6"
VIDEO_ID = "6f37c274-4742-4953-b401-57b4ded16ebd"
URL = f"https://{BUNNY_CND_PULL_ZONE}.b-cdn.net/{VIDEO_ID}/original"

preprocess = transforms.Compose([
    T.ToFloatTensorInZeroOne(),
    T.Resize((200, 200)),
    T.CenterCrop((172, 172))])

try:
    labels_file = open("kinetics_600.txt", "r")
    labels = numpy.array(labels_file.read().split('\n'))

    print(URL)
    # Download the video from CDN.
    x = requests.get(URL)

    # Save the downloaded video to a temp file
    # to easily read it with torchvision.
    with tempfile.NamedTemporaryFile() as fp:
        fp.write(x.content)

        video, _, metadata = torchvision.io.read_video(fp.name)
        # video.size() == (frames, height, width, colors)

        fps = int(metadata['video_fps'])
        frames_cnt = video.size()[0]

        selected_frames_cnt = min(frames_cnt, frames_cnt * MAX_FPS // fps)
        selected_frames = torch.linspace(start=0, end=frames_cnt - 1, steps=selected_frames_cnt, dtype=torch.long)

        video = video[selected_frames]

        video = preprocess(video)

        fig, ax = plt.subplots()
        frames = [[ax.imshow(video[0][i])] for i in range(video.size()[1])]

        ani = animation.ArtistAnimation(fig, frames, interval=200, blit=True, repeat_delay=1000)

        plt.show()

        with torch.no_grad():
            model = MoViNet(_C.MODEL.MoViNetA0, pretrained=True)
            model.eval()

            video_batch = torch.unsqueeze(video, 0)
            output = F.log_softmax(model(video_batch), dim=1)
            _, predictions = torch.topk(output, dim=1, k=TOP_K)
            print(f"Video {VIDEO_ID} predictions: {labels[predictions]}")
except Exception as e:
    print(e)
    exit(1)
