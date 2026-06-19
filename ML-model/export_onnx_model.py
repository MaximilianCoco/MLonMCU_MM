import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as T
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import numpy as np
from sklearn.metrics import roc_auc_score, f1_score, roc_curve

import onnx
import onnxruntime as ort

# =========================
# CONFIG
# =========================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMG_SIZE = 224

MODEL_PATH = "saved_models/model_pruned_40pct.pth"
MEMORY_PATH = "saved_models/memory_40pct.pt"
TEST_ROOT = "tinyglass_mmdataset/tinyglass_mmdataset/mms_stretch"
ONNX_PATH = "studentcnn_40pct.onnx"
FIXED_THRESHOLD = 0.00155658


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
                self.samples.append((os.path.join(cpath, f), label))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, i):
        p, y = self.samples[i]
        img = Image.open(p).convert("RGB")
        return self.tfm(img), y


# =========================
# MODEL
# =========================
class StudentCNN(nn.Module):

    def __init__(self, channels):
        super().__init__()
        c1, c2, c3, c4, c5 = channels

        self.net = nn.Sequential(
            nn.Conv2d(3, c1, 3, padding=1), nn.ReLU(),
            nn.Conv2d(c1, c2, 3, 2, 1), nn.ReLU(),
            nn.Conv2d(c2, c3, 3, 2, 1), nn.ReLU(),
            nn.Conv2d(c3, c4, 3, 2, 1), nn.ReLU(),
            nn.Conv2d(c4, c5, 3, padding=1)
        )

    def forward(self, x):
        return self.net(x)


# =========================
# 🔥 MATCH TRAINING pool_features EXACTLY
# =========================
def pool_features(f):
    p1 = F.adaptive_avg_pool2d(f, 1)
    p2 = F.adaptive_avg_pool2d(f, 2)
    v = torch.cat([p1.flatten(1), p2.flatten(1)], dim=1)
    return F.normalize(v, dim=1)


# =========================
# 🔥 FIXED ANOMALY SCORE (NOW MATCHES TRAIN SCRIPT EXACTLY)
# =========================
def anomaly_score(features_np, memory):

    f = torch.from_numpy(features_np)

    # same pooling as training
    if f.ndim == 4:
        v = pool_features(f)
    else:
        v = f

    v = F.normalize(v, dim=1)
    memory = F.normalize(memory, dim=1).to(v.dtype)

    # 🔥 MATCH TRAINING EXACTLY: dot product, NOT cosine_similarity()
    sim = v @ memory.T

    return (1 - sim.max(dim=1).values).cpu().numpy()


# =========================
# METRICS
# =========================
def compute_metrics(scores, labels, threshold):

    scores = np.array(scores)
    labels = np.array(labels)

    pred = (scores > threshold).astype(int)

    return (
        roc_auc_score(labels, scores),
        (pred == labels).mean(),
        f1_score(labels, pred)
    )


# =========================
# EXPORT ONNX
# =========================
def export_onnx(model):

    print("\n=== EXPORTING ONNX ===")

    model.eval().cpu()

    dummy = torch.randn(1, 3, 224, 224)

    torch.onnx.export(
        model,
        dummy,
        ONNX_PATH,
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["features"]
    )

    onnx_model = onnx.load(ONNX_PATH)
    onnx.checker.check_model(onnx_model)

    print("✅ ONNX exported:", ONNX_PATH)


# =========================
# ONNX TEST (FIXED & MATCHING PYTORCH PIPELINE)
# =========================
def run_onnx_test(test_loader):

    print("\n=== ONNX INFERENCE TEST ===")

    memory = torch.load(MEMORY_PATH, map_location="cpu")

    # keep EXACT same normalization as training
    memory = F.normalize(memory.float(), dim=1)

    providers = (
        ["CUDAExecutionProvider"]
        if "CUDAExecutionProvider" in ort.get_available_providers()
        else ["CPUExecutionProvider"]
    )

    session = ort.InferenceSession(ONNX_PATH, providers=providers)
    input_name = session.get_inputs()[0].name

    scores, labels = [], []

    for x, y in test_loader:

        x_np = x.numpy().astype(np.float32)

        feat = session.run(None, {input_name: x_np})[0]

        if isinstance(feat, list):
            feat = feat[0]

        # IMPORTANT: keep feature format identical
        score = anomaly_score(feat, memory)

        scores.append(score[0])
        labels.append(y.item())

    scores = np.array(scores)
    labels = np.array(labels)

    auc, acc, f1 = compute_metrics(scores, labels, FIXED_THRESHOLD)

    print("\n=== RESULTS ===")
    print(f"AUC : {auc:.4f}")
    print(f"ACC : {acc:.4f}")
    print(f"F1  : {f1:.4f}")


# =========================
# MAIN
# =========================
def main():

    ckpt = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=False)
    sd = ckpt["model_state"]

    channels = [
        sd["net.0.weight"].shape[0],
        sd["net.2.weight"].shape[0],
        sd["net.4.weight"].shape[0],
        sd["net.6.weight"].shape[0],
        sd["net.8.weight"].shape[0],
    ]

    print("Detected channels:", channels)
    print("\nPrune Ratio:", ckpt["prune_ratio"])

    model = StudentCNN(channels).to(DEVICE)
    model.load_state_dict(sd)
    model.eval()

    export_onnx(model)

    test_ds = MMSDataset(TEST_ROOT, "test")
    test_loader = DataLoader(test_ds, batch_size=1, shuffle=False)

    run_onnx_test(test_loader)


if __name__ == "__main__":
    main()