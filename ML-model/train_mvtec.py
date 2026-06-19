
import os
import copy
import random
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F

from torch.utils.data import DataLoader
from sklearn.metrics import roc_auc_score, f1_score

from mvtec import MVTecDataset, DatasetSplit

# ============================================================
# CONFIG
# ============================================================

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

MVTEC_ROOT = r"D:\ETH\mvtec_ad_2"

OUTPUT_DIR = "saved_models"
os.makedirs(OUTPUT_DIR, exist_ok=True)

IMG_SIZE = 224

MVTEC_CLASSES = [
    "can",
    "fabric",
    "fruit_jelly",
    "rice",
    "sheet_metal",
    "vial",
    "wallplugs",
    "walnuts"
]


# ============================================================
# SEED
# ============================================================

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


set_seed()


# ============================================================
# MODEL
# ============================================================

class StudentCNN(nn.Module):
    def __init__(self, ch=[16, 32, 64, 128, 128]):
        super().__init__()

        c1, c2, c3, c4, c5 = ch

        self.net = nn.Sequential(
            nn.Conv2d(3, c1, 3, padding=1),
            nn.ReLU(inplace=True),

            nn.Conv2d(c1, c2, 3, stride=2, padding=1),
            nn.ReLU(inplace=True),

            nn.Conv2d(c2, c3, 3, stride=2, padding=1),
            nn.ReLU(inplace=True),

            nn.Conv2d(c3, c4, 3, stride=2, padding=1),
            nn.ReLU(inplace=True),

            nn.Conv2d(c4, c5, 3, padding=1)
        )

    def forward(self, x):
        return self.net(x)

    def extract(self, x):
        return self.forward(x)


# ============================================================
# FEATURE POOLING
# ============================================================

def pool_features(f):
    p1 = F.adaptive_avg_pool2d(f, 1)
    p2 = F.adaptive_avg_pool2d(f, 2)

    v = torch.cat(
        [p1.flatten(1), p2.flatten(1)],
        dim=1
    )

    return F.normalize(v, dim=1)


# ============================================================
# MEMORY BANK
# ============================================================

@torch.no_grad()
def build_memory(model, loader, K=64):

    model.eval()

    feats = []

    for batch in loader:

        x = batch["image"].to(DEVICE)

        f = model.extract(x)

        feats.append(
            pool_features(f).cpu()
        )

    feats = torch.cat(feats)

    feats = F.normalize(feats, dim=1)

    K = min(K, len(feats))

    idx = torch.randperm(len(feats))[:K]

    proto = feats[idx]

    for _ in range(5):

        sim = feats @ proto.T

        assign = sim.argmax(1)

        new_proto = []

        for k in range(K):

            mask = assign == k

            if mask.sum() > 0:
                new_proto.append(
                    feats[mask].mean(0)
                )
            else:
                new_proto.append(proto[k])

        proto = F.normalize(
            torch.stack(new_proto),
            dim=1
        )

    return proto.to(DEVICE)


# ============================================================
# ANOMALY SCORE
# ============================================================

def anomaly_score(f, memory):

    v = pool_features(f)

    memory = F.normalize(memory, dim=1)

    dist = (
        (v.unsqueeze(1) - memory.unsqueeze(0)) ** 2
    ).sum(dim=2)

    score = dist.min(dim=1).values

    return score


# ============================================================
# THRESHOLD
# ============================================================

@torch.no_grad()
def compute_threshold(model, loader, memory):

    model.eval()

    scores = []

    for batch in loader:

        x = batch["image"].to(DEVICE)

        f = model.extract(x)

        s = anomaly_score(f, memory)

        scores.append(s.cpu())

    scores = torch.cat(scores).numpy()

    mu = scores.mean()
    sigma = scores.std()

    threshold = mu 

    print(
        f"threshold={threshold:.6f} "
        f"(mu={mu:.6f}, sigma={sigma:.6f})"
    )

    return threshold


# ============================================================
# METRICS
# ============================================================

def compute_metrics(scores, labels, threshold):

    scores = np.asarray(scores)
    labels = np.asarray(labels)

    pred = (scores > threshold).astype(int)

    acc = (pred == labels).mean()

    f1 = f1_score(
        labels,
        pred,
        zero_division=0
    )

    if len(np.unique(labels)) > 1:
        auc = roc_auc_score(labels, scores)
    else:
        auc = float("nan")

    return auc, acc, f1


# ============================================================
# TRAIN
# ============================================================


def train(model, loader, epochs=25):

    opt = torch.optim.Adam(
        model.parameters(),
        lr=2e-4
    )

    for ep in range(epochs):

        model.train()

        running = 0.0

        for batch in loader:

            x = batch["image"].to(DEVICE)

            f = model.extract(x)

            # your original loss
            loss = f.var(dim=1).mean()

            opt.zero_grad()

            loss.backward()

            opt.step()

            running += loss.item()

        print(
            f"Epoch {ep+1:02d} "
            f"Loss {running/len(loader):.8f}"
        )


# ============================================================
# EVALUATE
# ============================================================

@torch.no_grad()
def evaluate(
    model,
    test_loader,
    memory,
    threshold
):

    model.eval()

    scores = []
    labels = []

    for batch in test_loader:

        x = batch["image"].to(DEVICE)

        y = int(batch["is_anomaly"])

        f = model.extract(x)

        s = anomaly_score(f, memory)

        scores.append(float(s.item()))
        labels.append(y)

    return compute_metrics(
        scores,
        labels,
        threshold
    )


# ============================================================
# PRUNING
# ============================================================

def structured_prune(model, ratio=0.2):

    old_layers = list(model.net)

    new_layers = []

    keep_prev = None

    for layer in old_layers:

        if not isinstance(layer, nn.Conv2d):
            new_layers.append(copy.deepcopy(layer))
            continue

        importance = (
            layer.weight.data
            .abs()
            .mean(dim=(1, 2, 3))
        )

        keep_n = max(
            1,
            int(len(importance) * (1 - ratio))
        )

        keep_out = torch.topk(
            importance,
            keep_n
        ).indices

        new_conv = nn.Conv2d(
            in_channels=(
                layer.in_channels
                if keep_prev is None
                else len(keep_prev)
            ),
            out_channels=len(keep_out),
            kernel_size=layer.kernel_size,
            stride=layer.stride,
            padding=layer.padding,
            bias=(layer.bias is not None)
        )

        with torch.no_grad():

            w = layer.weight.data[keep_out]

            if keep_prev is not None:
                w = w[:, keep_prev]

            new_conv.weight.copy_(w)

            if layer.bias is not None:
                new_conv.bias.copy_(
                    layer.bias.data[keep_out]
                )

        new_layers.append(new_conv)

        keep_prev = keep_out

    model.net = nn.Sequential(*new_layers)

    return model


# ============================================================
# UTILITIES
# ============================================================

def count_params(model):
    return sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )


def model_size(model):

    tmp = "_tmp.pt"

    torch.save(model.state_dict(), tmp)

    size = os.path.getsize(tmp) / (1024 ** 2)

    os.remove(tmp)

    return size


def save_checkpoint(
    model,
    memory,
    prune_ratio,
    classname
):

    path = os.path.join(
        OUTPUT_DIR,
        f"{classname}_prune_{int(prune_ratio*100)}.pth"
    )

    channels = [
        m.out_channels
        for m in model.net
        if isinstance(m, nn.Conv2d)
    ]

    torch.save(
        {
            "model_state": model.state_dict(),
            "memory": memory.cpu(),
            "channels": channels,
            "prune_ratio": prune_ratio
        },
        path
    )


def export_for_mcu(model):

    print("Exporting TorchScript...")

    model = model.cpu().eval()

    example = torch.randn(
        1,
        3,
        IMG_SIZE,
        IMG_SIZE
    )

    traced = torch.jit.trace(
        model,
        example
    )

    traced.save(
        os.path.join(
            OUTPUT_DIR,
            "student_model.pt"
        )
    )


# ============================================================
# DATA LOADERS
# ============================================================

def build_loaders(classname):

    train_ds = MVTecDataset(
        source=MVTEC_ROOT,
        classname=classname,
        split=DatasetSplit.TRAIN,
        resize=IMG_SIZE,
        imagesize=IMG_SIZE,
        contamination_rate=0.0
    )

    test_ds = MVTecDataset(
        source=MVTEC_ROOT,
        classname=classname,
        split=DatasetSplit.TEST,
        resize=IMG_SIZE,
        imagesize=IMG_SIZE
    )

    train_loader = DataLoader(
        train_ds,
        batch_size=16,
        shuffle=True,
        num_workers=4,
        pin_memory=True
    )

    test_loader = DataLoader(
        test_ds,
        batch_size=1,
        shuffle=False,
        num_workers=4,
        pin_memory=True
    )

    return train_loader, test_loader


# ============================================================
# MAIN
# ============================================================

def main():

    all_results = []

    for classname in MVTEC_CLASSES:

        print("\n" + "=" * 70)
        print(f"CLASS: {classname}")
        print("=" * 70)

        train_loader, test_loader = build_loaders(
            classname
        )

        model = StudentCNN().to(DEVICE)

        train(
            model,
            train_loader,
            epochs=25
        )

        memory = build_memory(
            model,
            train_loader,
            K=64
        )

        threshold = compute_threshold(
            model,
            train_loader,
            memory
        )

        auc, acc, f1 = evaluate(
            model,
            test_loader,
            memory,
            threshold
        )

        print(
            f"[BASE] "
            f"AUC={auc:.4f} "
            f"ACC={acc:.4f} "
            f"F1={f1:.4f}"
        )

        print(
            f"PARAMS={count_params(model):,}"
        )

        save_checkpoint(
            model,
            memory,
            0.0,
            classname
        )

        all_results.append(auc)

        # -----------------------
        # pruning sweep
        # -----------------------

        for pct in [10, 20, 30, 40, 50]:

            print(
                f"\nPruning {pct}%"
            )

            pruned = copy.deepcopy(model)

            pruned = structured_prune(
                pruned,
                pct / 100.0
            ).to(DEVICE)

            train(
                pruned,
                train_loader,
                epochs=3
            )

            memory_p = build_memory(
                pruned,
                train_loader,
                K=64
            )

            auc_p, acc_p, f1_p = evaluate(
                pruned,
                test_loader,
                memory_p,
                threshold
            )

            print(
                f"AUC={auc_p:.4f} "
                f"ACC={acc_p:.4f} "
                f"F1={f1_p:.4f} "
                f"SIZE={model_size(pruned):.3f}MB"
            )

            save_checkpoint(
                pruned,
                memory_p,
                pct / 100.0,
                classname
            )

    print("\n")
    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)

    print(
        f"Mean AUROC: "
        f"{np.nanmean(all_results):.4f}"
    )

    export_for_mcu(
        StudentCNN()
    )


if __name__ == "__main__":
    main()
