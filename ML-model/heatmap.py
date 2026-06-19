import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import torchvision.transforms as T
import matplotlib.pyplot as plt
import numpy as np

# =========================
# CONFIG
# =========================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMG_SIZE = 224
MODEL_PATH = "saved_models/model_pruned_0pct.pth"

# =========================
# DATASET
# =========================
class MMSDataset(Dataset):
    def __init__(self, root, split="test"):
        self.samples = []
        base = os.path.join(root, split)

        self.tfm = T.Compose([
            T.Resize((IMG_SIZE, IMG_SIZE)),
            T.ToTensor(),
            T.Normalize([0.485,0.456,0.406],
                        [0.229,0.224,0.225])
        ])

        for cls in os.listdir(base):
            cpath = os.path.join(base, cls)
            if not os.path.isdir(cpath):
                continue
            label = 0 if cls == "good" else 1
            for f in os.listdir(cpath):
                self.samples.append((os.path.join(cpath,f), label))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, i):
        p,y = self.samples[i]
        img = Image.open(p).convert("RGB")
        return self.tfm(img), y, p

# =========================
# MODEL
# =========================
class StudentCNN(nn.Module):
    def __init__(self, ch=[16,32,64,128,128]):
        super().__init__()
        c1,c2,c3,c4,c5 = ch
        self.net = nn.Sequential(
            nn.Conv2d(3,c1,3,padding=1), nn.ReLU(),
            nn.Conv2d(c1,c2,3,2,1), nn.ReLU(),
            nn.Conv2d(c2,c3,3,2,1), nn.ReLU(),
            nn.Conv2d(c3,c4,3,2,1), nn.ReLU(),
            nn.Conv2d(c4,c5,3,padding=1)
        )

    def forward(self, x):
        return self.net(x)

    def extract(self, x):
        return self.forward(x)

# =========================
# MEMORY (FIXED)
# =========================
@torch.no_grad()
def build_memory(model, loader, K=64):
    model.eval()
    feats = []

    for x, y, _ in loader:
        mask = (y == 0)
        if mask.sum() == 0:
            continue

        x = x[mask].to(DEVICE)
        f = model.extract(x)              # [B,128,H,W]
        B,C,H,W = f.shape

        # IMPORTANT FIX: use raw spatial features
        f = f.permute(0,2,3,1).reshape(-1, C)  # [N,128]
        feats.append(F.normalize(f, dim=1).cpu())

    feats = torch.cat(feats)
    feats = F.normalize(feats, dim=1)

    idx = torch.randperm(len(feats))[:K]
    proto = feats[idx].to(DEVICE)

    return proto

# =========================
# HEATMAP
# =========================
def anomaly_heatmap(f, memory):
    B,C,H,W = f.shape

    f = f.permute(0,2,3,1).contiguous()   # B,H,W,C
    f_flat = F.normalize(f.view(B, H*W, C), dim=-1)

    memory = F.normalize(memory, dim=1)

    dist = torch.cdist(f_flat, memory)    # B,N,K
    heatmap = dist.min(dim=-1).values      # B,N
    return heatmap.view(B,H,W)

def upscale_heatmap(hm, size=224):
    return F.interpolate(
        hm.unsqueeze(1),
        size=(size,size),
        mode="bilinear",
        align_corners=False
    ).squeeze(1)

# =========================
# VISUALIZATION
# =========================
def show(img, hm):
    img = img.permute(1,2,0).cpu().numpy()
    img = (img - img.min()) / (img.max() - img.min())

    hm = hm.cpu().numpy()

    plt.imshow(img)
    plt.imshow(hm, cmap="jet", alpha=0.5)
    plt.axis("off")
    plt.show()

# =========================
# LOAD MODEL
# =========================
model = StudentCNN().to(DEVICE)
ckpt = torch.load(MODEL_PATH, map_location=DEVICE)
model.load_state_dict(ckpt["model_state"])
model.eval()

# =========================
# DATA
# =========================
DATA_ROOT = "tinyglass_mmdataset/tinyglass_mmdataset/mms_rpi"

train_ds = MMSDataset(DATA_ROOT, "train")
test_ds  = MMSDataset(DATA_ROOT, "test")

train_loader = DataLoader(train_ds, batch_size=16, shuffle=True)
test_loader  = DataLoader(test_ds, batch_size=1, shuffle=False)

# =========================
# BUILD MEMORY (FIXED)
# =========================
memory = build_memory(model, train_loader, K=64)

# =========================
# RUN HEATMAPS
# =========================
with torch.no_grad():
    for x, y, path in test_loader:
        x = x.to(DEVICE)

        f = model.extract(x)
        hm = anomaly_heatmap(f, memory)
        hm = upscale_heatmap(hm, IMG_SIZE)

        print(f"{path[0]} | label={y.item()}")
        show(x[0], hm[0])