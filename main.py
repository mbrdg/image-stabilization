# main.py
# Authors: Guilherme Franco and Miguel Rodrigues
import numpy as np
import torch
import matplotlib.pyplot as plt
import cv2
import torchvision.transforms.functional as F
import torchvision.transforms as T
from torchvision.io import read_video
from torchvision.models.optical_flow import raft_large
from torchvision.utils import flow_to_image


plt.rcParams["savefig.bbox"] = "tight"


def main():
    frames, _, _ = read_video("data/unstable/42.avi")
    frames = frames.permute(0, 3, 2, 1)

    img1_batch = torch.stack([frames[100], frames[150]])
    img2_batch = torch.stack([frames[101], frames[151]])

    device = "cuda" if torch.cuda.is_available() else "cpu"

    img1_batch = preprocess(img1_batch).to(device)
    img2_batch = preprocess(img2_batch).to(device)

    print(f"shape = {img1_batch.shape}, dtype = {img1_batch.dtype}")

    model = raft_large(pretrained=True, progress=False).to(device)
    model = model.eval()

    list_of_flows = model(img1_batch.to(device), img2_batch.to(device))
    print(f"type = {type(list_of_flows)}")
    print(f"lenght = {len(list_of_flows)} (number of iterations of the model)")

    predicted_flows = list_of_flows[-1]
    print(f"dtype = {predicted_flows.dtype}")
    print(f"shape = {predicted_flows.shape} (N, 2, H, W)")
    print(f"min = {predicted_flows.min()}, max = {predicted_flows.max()}")

    flow_imgs = flow_to_image(predicted_flows)

    img1_batch = [(img1 + 1) / 2 for img1 in img1_batch]

    grid = [[img1, flow_img] for (img1, flow_img) in zip(img1_batch, flow_imgs)]
    plot(grid)


def plot(imgs, **imshow_kwargs):
    if not isinstance(imgs[0], list):
        imgs = [imgs]

    rows, cols = len(imgs), len(imgs[0])
    _, axs = plt.subplots(nrows=rows, ncols=cols, squeeze=False)

    for row_idx, row in enumerate(imgs):
        for col_idx, img in enumerate(row):
            ax = axs[row_idx, col_idx]
            img = F.to_pil_image(img.to("cpu"))
            ax.imshow(np.asarray(img), **imshow_kwargs)
            ax.set(xticklabels=[], yticklabels=[], xticks=[], yticks=[])

    plt.tight_layout()
    plt.show()


def preprocess(batch):
    transforms = T.Compose(
        [
            T.ConvertImageDtype(torch.float32),
            T.Normalize(mean=0.5, std=0.5),
            T.Resize(size=(520, 960)),
        ],
    )

    batch = transforms(batch)
    return batch


# Images must come in grayscale
def get_matching_features(img1, img2):
    # Initiate SIFT detector

    sift = cv2.SIFT_create()

    # find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)
    #  FLANN parameters
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)  # or pass empty dictionary
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)
    # Need to draw only good matches, so create a mask
    matchesMask = [[0, 0] for _ in range(len(matches))]
    matching_coords = []
    # ratio test as per Lowe's paper
    for i, (m, n) in enumerate(matches):
        if m.distance < 0.7 * n.distance:
            matchesMask[i] = [1, 0]
            matching_coords.append(m)
    draw_params = dict(
        matchColor=(0, 255, 0),
        singlePointColor=(255, 0, 0),
        matchesMask=matchesMask,
        flags=cv2.DrawMatchesFlags_DEFAULT,
    )
    img3 = cv2.drawMatchesKnn(img1, kp1, img2, kp2, matches, None, **draw_params)
    plt.imshow(
        img3,
    ), plt.show()
    source_pt = [kp1[m.queryIdx].pt for m in matching_coords]
    dst_pt = [kp2[m.trainIdx].pt for m in matching_coords]


if __name__ == "__main__":
    main()
