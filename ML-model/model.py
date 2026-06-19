import os
import copy
import random
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as T
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import numpy as np
from sklearn.metrics import roc_auc_score, f1_score, roc_curve

# =========================
# CONFIG
# =========================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMG_SIZE = 224

# =========================
# OUTPUT DIR (NEW)
# =========================
OUTPUT_DIR = "saved_models"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================
# SEED
# =========================
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

set_seed()

# =========================
# DATASET
# =========================
class MMSDataset(Dataset):
    def __init__(self, root, split="train"):
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
        return self.tfm(img), y

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
# FEATURES
# =========================
def pool_features(f):
    p1 = F.adaptive_avg_pool2d(f,1)
    p2 = F.adaptive_avg_pool2d(f,2)
    v = torch.cat([p1.flatten(1), p2.flatten(1)],1)
    return F.normalize(v, dim=1)

# =========================
# MEMORY
# =========================
@torch.no_grad()
def build_memory(model, loader, K=64):
    model.eval()
    feats = []

    for x, y in loader:

        mask = (y == 0)

        if mask.sum() == 0:
            continue

        x = x[mask].to(DEVICE)
        f = model.extract(x)
        feats.append(pool_features(f).cpu())

    feats = torch.cat(feats)
    feats = F.normalize(feats, dim=1)

    idx = torch.randperm(len(feats))[:K]
    proto = feats[idx]

    for _ in range(5):
        sim = feats @ proto.T
        assign = sim.argmax(1)

        new = []
        for k in range(K):
            m = assign == k
            new.append(feats[m].mean(0) if m.sum() > 0 else proto[k])

        proto = F.normalize(torch.stack(new), dim=1)

    return proto.to(DEVICE)

# =========================
# ANOMALY SCORE
# =========================
def anomaly_score(f, memory):

    v = pool_features(f)

    memory = F.normalize(memory, dim=1)

    dist = ((v.unsqueeze(1) - memory.unsqueeze(0)) ** 2).sum(dim=2)
    score = dist.min(dim=1).values

    return score

# =========================
# THRESHOLD
# =========================
def compute_threshold(model, train_loader, memory):

    scores = []

    model.eval()

    with torch.no_grad():

        for x, y in train_loader:

            # only GOOD samples
            mask = (y == 0)

            if mask.sum() == 0:
                continue

            x = x[mask].to(DEVICE)

            f = model.extract(x)

            s = anomaly_score(f, memory)

            scores.append(s.cpu())

    scores = torch.cat(scores).numpy()

    mu = scores.mean()
    sigma = scores.std()

    threshold = mu + 4 * sigma

    print(f"\nThreshold stats:")
    print(f"mu    = {mu:.6f}")
    print(f"sigma = {sigma:.6f}")

    return threshold

# =========================
# METRICS
# =========================
def compute_metrics(scores, labels, threshold):
    scores = np.array(scores)
    labels = np.array(labels)

    auc = roc_auc_score(labels, scores)
    pred = (scores > threshold).astype(int)

    acc = (pred == labels).mean()
    f1 = f1_score(labels, pred)

    return auc, acc, f1

# =========================
# TRAIN
# =========================
def train(model, loader, epochs=25):
    opt = torch.optim.Adam(model.parameters(), 2e-4)

    for ep in range(epochs):
        model.train()
        s = 0

        for x,_ in loader:
            x = x.to(DEVICE)
            f = model.extract(x)
            loss = f.var(1).mean()

            opt.zero_grad()
            loss.backward()
            opt.step()

            s += loss.item()

        print(f"Epoch {ep+1}: {s/len(loader):.8f}")

# =========================
# EVAL
# =========================
def evaluate(model, test_loader, memory, threshold):
    scores, labels = [], []

    model.eval()
    with torch.no_grad():
        for x,y in test_loader:
            x = x.to(DEVICE)
            f = model.extract(x)
            s = anomaly_score(f, memory)

            scores.append(s.item())
            labels.append(y.item())

    return compute_metrics(scores, labels, threshold)

# =========================
# PRUNING
# =========================
def structured_prune(model, ratio=0.2):
    old_layers = list(model.net)
    new_layers = []

    keep_prev = None  # tracks kept input channels for next conv

    for layer in old_layers:

        if isinstance(layer, nn.Conv2d):

            # importance per output channel
            importance = layer.weight.data.abs().mean(dim=(1,2,3))

            k = max(1, int(len(importance) * (1 - ratio)))
            keep_out = torch.topk(importance, k).indices

            # build new conv with correct shape
            new_conv = nn.Conv2d(
                in_channels=layer.in_channels if keep_prev is None else len(keep_prev),
                out_channels=len(keep_out),
                kernel_size=layer.kernel_size,
                stride=layer.stride,
                padding=layer.padding,
                bias=(layer.bias is not None)
            )

            with torch.no_grad():
                w = layer.weight.data[keep_out]

                # IMPORTANT: prune input channels too if needed
                if keep_prev is not None:
                    w = w[:, keep_prev]

                new_conv.weight.copy_(w)

                if layer.bias is not None:
                    new_conv.bias.copy_(layer.bias.data[keep_out])

            new_layers.append(new_conv)
            keep_prev = keep_out

        else:
            new_layers.append(copy.deepcopy(layer))

    model.net = nn.Sequential(*new_layers)
    return model

# =========================
# PARAM COUNT
# =========================
def count_params(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

# =========================
# SIZE
# =========================
def model_size(model):
    path = "tmp.pt"
    torch.save(model.state_dict(), path)
    size = os.path.getsize(path) / (1024**2)
    os.remove(path)
    return size

# =========================
# SAVE CHECKPOINT (UPDATED)
# =========================
def save_checkpoint(model, memory, prune_ratio, pct):

    model_path = os.path.join(OUTPUT_DIR, f"model_pruned_{pct}pct.pth")
    mem_path = os.path.join(OUTPUT_DIR, f"memory_{pct}pct.pt")

    channels = [
        model.net[0].out_channels,
        model.net[2].out_channels,
        model.net[4].out_channels,
        model.net[6].out_channels,
        model.net[8].out_channels,
    ]

    torch.save({
        "model_state": model.state_dict(),
        "memory": memory.detach().cpu(),
        "prune_ratio": prune_ratio,
        "channels": channels
    }, model_path)

    torch.save(memory.detach().cpu(), mem_path)

# =========================
# EXPORT MCU
# =========================
def export_for_mcu(model):
    print("\n=== MCU EXPORT ===")

    model = model.cpu().eval()
    example = torch.randn(1,3,224,224)

    traced = torch.jit.trace(model, example)
    traced.save(os.path.join(OUTPUT_DIR, "model.pt"))

# =========================
# MAIN
# =========================
def main():

    DATA_ROOT = "tinyglass_mmdataset/tinyglass_mmdataset/mms_rpi"
    TEST_ROOT = "tinyglass_mmdataset/tinyglass_mmdataset/mms_stretch"

    train_ds = MMSDataset(DATA_ROOT,"train")
    test1 = MMSDataset(DATA_ROOT,"test")
    test2 = MMSDataset(TEST_ROOT,"test")

    train_loader = DataLoader(train_ds,16,True)
    test_loader_1 = DataLoader(test1,1,False)
    test_loader_2 = DataLoader(test2,1,False)

    # =========================
    # BASE
    # =========================
    print("\n=== BASE MODEL ===")

    base = StudentCNN().to(DEVICE)
    train(base, train_loader, epochs=25)

    memory = build_memory(base, train_loader, K=64)
    threshold = compute_threshold(base, train_loader, memory)

    print(f"\n🔧 Threshold: {threshold:.12f}")

    print("\n=== TEST 1 ===")
    auc1, acc1, f11 = evaluate(base, test_loader_1, memory, threshold)
    print(f"[TEST1] AUC {auc1:.4f} ACC {acc1:.4f} F1 {f11:.4f}")

    print("\n=== TEST 2 ===")
    auc2, acc2, f12 = evaluate(base, test_loader_2, memory, threshold)
    print(f"[TEST2] AUC {auc2:.4f} ACC {acc2:.4f} F1 {f12:.4f}")

    print(f"\n[BASE PARAMS] {count_params(base):,}")

    # =========================
    # PRUNING
    # =========================
    print("\n=== PRUNING SWEEP ===")

    results = []

    for pct in range(0, 100, 10):

        print(f"\n🔥 {pct}% PRUNING")

        model = copy.deepcopy(base)

        if pct > 0:
            model = structured_prune(model, pct/100.0).to(DEVICE)
            train(model, train_loader, 3)

        memory = build_memory(model, train_loader, K=64)

        print("\n--- TEST 1 ---")
        auc1, acc1, f11 = evaluate(model, test_loader_1, memory, threshold)
        print(f"[TEST1] AUC {auc1:.4f} ACC {acc1:.4f} F1 {f11:.4f}")

        print("\n--- TEST 2 ---")
        auc2, acc2, f12 = evaluate(model, test_loader_2, memory, threshold)
        print(f"[TEST2] AUC {auc2:.4f} ACC {acc2:.4f} F1 {f12:.4f}")

        size = model_size(model)

        print(f"[{pct}% PARAMS] {count_params(model):,}")
        print(f"[{pct}% SIZE] {size:.6f} MB")

        save_checkpoint(model, memory, pct/100.0, pct)

        results.append((pct, auc2, acc2, f12, size))

    best = max(results, key=lambda x: x[1])

    print("\n=== BEST ===")
    print(best)

    export_for_mcu(base)

if __name__ == "__main__":
    main()