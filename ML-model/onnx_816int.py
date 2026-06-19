import os
import csv
import shutil
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
import onnx
import onnxruntime as ort

from sklearn.metrics import roc_auc_score, f1_score

from onnxruntime.quantization import (
    quantize_static,
    CalibrationDataReader,
    QuantFormat,
    QuantType,
    CalibrationMethod
)

from onnxconverter_common import float16

from export_onnx_model import (
    MMSDataset,
    MEMORY_PATH,
    ONNX_PATH
)
import onnx

def count_onnx_weights(model_path):
    model = onnx.load(model_path)

    total_params = 0
    total_bytes = 0

    for init in model.graph.initializer:
        arr = onnx.numpy_helper.to_array(init)
        n = arr.size
        total_params += n
        total_bytes += arr.nbytes

    print("\n=== MODEL WEIGHTS ===")
    print(f"Total parameters: {total_params:,}")
    print(f"Weight memory   : {total_bytes / (1024**2):.3f} MB")

    return total_params, total_bytes
def estimate_activation_memory(model_path, batch_size=1):
    
    model = onnx.load(model_path)

    first_node = model.graph.node[0]
    output_name = first_node.output[0]

    # find matching value_info or inference shape
    for vi in model.graph.value_info:
        if vi.name == output_name:
            shape = []
            for d in vi.type.tensor_type.shape.dim:
                shape.append(d.dim_value if d.dim_value > 0 else 1)

            elems = np.prod(shape)
            mem = elems * 4

            print("\n=== FIRST NODE OUTPUT (PEAK MEMORY) ===")
            print(f"Tensor: {output_name}")
            print(f"Shape : {shape}")
            print(f"Memory: {mem / (1024**2):.3f} MB")

            return mem

    print("Shape info not found for first node output.")
    return None

# =========================
# OUTPUT DIR
# =========================
OUT_DIR = "onnx_models"
os.makedirs(OUT_DIR, exist_ok=True)

FP32_PATH = os.path.join(OUT_DIR, "model_fp32.onnx")
FP16_PATH = os.path.join(OUT_DIR, "model_fp16.onnx")
INT8_PATH = os.path.join(OUT_DIR, "model_int8_qdq.onnx")

MEM_FP32_PATH = os.path.join(OUT_DIR, "memory_fp32.pt")
MEM_FP16_PATH = os.path.join(OUT_DIR, "memory_fp16.pt")
MEM_INT8_PATH = os.path.join(OUT_DIR, "memory_int8.pt")

# =========================
# TEST SETS
# =========================
TEST_ROOT_1 = "tinyglass_mmdataset/tinyglass_mmdataset/mms_rpi"
TEST_ROOT_2 = "tinyglass_mmdataset/tinyglass_mmdataset/mms_stretch"

# =========================
def size_mb(path):
    return os.path.getsize(path) / (1024 * 1024)

# =========================
class CalibDataReader(CalibrationDataReader):
    def __init__(self, loader):
        self.loader = iter(loader)

    def get_next(self):
        try:
            x, _ = next(self.loader)
            return {"input": x.numpy().astype(np.float32)}
        except StopIteration:
            return None

# =========================
def export_fp16():
    print("\n=== FP16 EXPORT ===")
    model = onnx.load(ONNX_PATH)
    model_fp16 = float16.convert_float_to_float16(model, keep_io_types=True)
    onnx.save(model_fp16, FP16_PATH)

# =========================
def export_int8():
    print("\n=== INT8 QDQ EXPORT ===")

    calib_ds = MMSDataset(TEST_ROOT_1, "test")
    loader = DataLoader(calib_ds, batch_size=1, shuffle=True)

    dr = CalibDataReader(loader)

    quantize_static(
        model_input=ONNX_PATH,
        model_output=INT8_PATH,
        calibration_data_reader=dr,
        quant_format=QuantFormat.QDQ,
        activation_type=QuantType.QInt8,
        weight_type=QuantType.QInt8,
        calibrate_method=CalibrationMethod.MinMax,
        per_channel=True,
        reduce_range=True
    )

# =========================
def quantize_memory():
    mem = torch.load(MEMORY_PATH, map_location="cpu")
    mem = F.normalize(mem.float(), dim=1).contiguous()

    torch.save(mem, MEM_FP32_PATH)

    mem_fp16 = mem.half()
    torch.save(mem_fp16, MEM_FP16_PATH)

    # 1. Quantize normally
    scale = mem.abs().max() / 127.0
    mem_int8 = torch.round(mem / scale).clamp(-127, 127).to(torch.int8)

    # 2. Simulate exactly what C does right here: 
    # Dequantize, but DO NOT re-normalize it in Python anymore!
    mem_int8_dequantized = mem_int8.float() * scale

    # 3. Save it out
    torch.save({"memory_int8": mem_int8, "scale": scale}, MEM_INT8_PATH)

    # Return the un-normalized dequantized tensor so Python metrics 
    # perfectly match the microcontrollers hardware constraints!
    return mem, mem_fp16, mem_int8_dequantized

# =========================
def load_int8_memory(path):
    d = torch.load(path, map_location="cpu")
    mem_int8 = d["memory_int8"]
    scale = d["scale"]
    print("scale")
    print(scale)
    mem = mem_int8.float() * scale
    mem = F.normalize(mem, dim=1)

    return mem

# =========================
def anomaly_score(features_np, memory):

    f = torch.from_numpy(features_np)

    if f.ndim == 4:
        p1 = F.adaptive_avg_pool2d(f, 1)
        p2 = F.adaptive_avg_pool2d(f, 2)
        v = torch.cat([p1.flatten(1), p2.flatten(1)], 1)
    else:
        v = f

    v = F.normalize(v, dim=1)

    dist = ((v.unsqueeze(1) - memory.unsqueeze(0)) ** 2).sum(dim=2)
    score = dist.min(dim=1).values

    return score

# =========================
def compute_threshold(session, memory, loader):

    input_name = session.get_inputs()[0].name
    scores = []

    for x, y in loader:
        if y.item() != 0:
            continue

        x_np = x.numpy().astype(np.float32)
        feat = session.run(None, {input_name: x_np})[0]

        scores.append(anomaly_score(feat, memory)[0])

    scores = np.array(scores)

    mu = scores.mean()
    sigma = scores.std()

    threshold = mu + 4 * sigma

    print("\n=== THRESHOLD ===")
    print(f"mu    = {mu:.6f}")
    print(f"sigma = {sigma:.6f}")
    print(f"thr   = {threshold:.6f}")

    return threshold

# =========================
def run(model_path, memory, name, test_root, threshold):

    session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name

    ds = MMSDataset(test_root, "test")
    loader = DataLoader(ds, batch_size=1, shuffle=False)

    scores, labels, filenames = [], [], []

    # ==================================================
    # SAFE FILENAME EXTRACTION (UPDATED)
    # ==================================================
    scores, labels, filenames = [], [], []

    # 1. Try common attribute names used in custom datasets
    if hasattr(ds, "filenames"):
        file_list = ds.filenames
    elif hasattr(ds, "samples"):
        # If it's a list of tuples like (path, label)
        file_list = [s[0] for s in ds.samples]
    elif hasattr(ds, "imgs"):
        file_list = [i[0] for i in ds.imgs]
    else:
        # 2. Fallback to indexing the dataset element directly, but safely check length
        try:
            sample_element = ds[0]
            if isinstance(sample_element, (list, tuple)) and len(sample_element) > 2:
                file_list = [ds[idx][2] for idx in range(len(ds))]
            else:
                file_list = None
        except Exception:
            file_list = None

    # ==================================================
    # MAIN INFERENCE LOOP
    # ==================================================
    for i, (x, y) in enumerate(loader):

        x_np = x.numpy().astype(np.float32)
        feat = session.run(None, {input_name: x_np})[0]

        s = anomaly_score(feat, memory).cpu().numpy()

        scores.append(s[0])
        labels.append(y.item())

        # Safely extract the filename from our resolved file_list
        if file_list is not None and i < len(file_list):
            fn = os.path.basename(str(file_list[i]))
        else:
            fn = f"img_{i}.png"  # Hard fallback if everything else fails
            
        filenames.append(fn)

    scores = np.array(scores)
    labels = np.array(labels)

    # INT8 normalization (unchanged)

    pred = (scores > threshold).astype(int)

    auc = roc_auc_score(labels, scores)
    acc = (pred == labels).mean()
    f1 = f1_score(labels, pred)

    print(f"\n--- {name} ---")
    print(f"AUC {auc:.4f} | ACC {acc:.4f} | F1 {f1:.4f}")
    print(f"USED THRESHOLD: {threshold:.6f}")

    # =========================
    # CSV EXPORT (ADDED)
    # =========================
    safe_name = name.replace(" ", "_").replace("-", "_")
    csv_path = os.path.join(OUT_DIR, f"scores_{safe_name}.csv")

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "score", "label", "pred"])

        for fn, sc, lb, pr in zip(filenames, scores, labels, pred):
            writer.writerow([
                fn,
                float(sc),
                int(lb),
                int(pr)
            ])

    print(f"\n[SAVED CSV] {csv_path}")

    return auc, acc, f1

# =========================
def main():

    print("\n============================")
    print(" FIXED BENCHMARK PIPELINE")
    print("============================")

    mem_fp32, mem_fp16, mem_int8 = quantize_memory()

    shutil.copy(ONNX_PATH, FP32_PATH)

    export_fp16()
    export_int8()

    print("\n=== MODEL SIZES ===")
    print(f"FP32 : {size_mb(FP32_PATH):.3f} MB")
    print(f"FP16 : {size_mb(FP16_PATH):.3f} MB")
    print(f"INT8 : {size_mb(INT8_PATH):.3f} MB")

    print("\n================ THRESHOLD =================")

    train_loader = DataLoader(
        MMSDataset(TEST_ROOT_1, "train"),
        batch_size=1,
        shuffle=False
    )

    th_fp32 = compute_threshold(
        ort.InferenceSession(FP32_PATH, providers=["CPUExecutionProvider"]),
        mem_fp32,
        train_loader
    )

    th_fp16 = compute_threshold(
        ort.InferenceSession(FP16_PATH, providers=["CPUExecutionProvider"]),
        mem_fp16,
        train_loader
    )

    mem_int8_fixed = load_int8_memory(MEM_INT8_PATH)

    th_int8 = compute_threshold(
        ort.InferenceSession(INT8_PATH, providers=["CPUExecutionProvider"]),
        mem_int8_fixed,
        train_loader
    )

    print("\n================ TEST 1 / 2 ================")

    run(FP32_PATH, mem_fp32, "FP32 - TEST 1", TEST_ROOT_1, th_fp32)
    run(FP32_PATH, mem_fp32, "FP32 - TEST 2", TEST_ROOT_2, th_fp32)

    run(FP16_PATH, mem_fp16, "FP16 - TEST 1", TEST_ROOT_1, th_fp16)
    run(FP16_PATH, mem_fp16, "FP16 - TEST 2", TEST_ROOT_2, th_fp16)

    run(INT8_PATH, mem_int8_fixed, "INT8 - TEST 1", TEST_ROOT_1, th_int8)
    run(INT8_PATH, mem_int8_fixed, "INT8 - TEST 2", TEST_ROOT_2, th_int8)
    print("\n================ MODEL ANALYSIS ================")

    count_onnx_weights(FP32_PATH)
    estimate_activation_memory(FP32_PATH)

    count_onnx_weights(FP16_PATH)
    estimate_activation_memory(FP16_PATH)

    count_onnx_weights(INT8_PATH)
    estimate_activation_memory(INT8_PATH)

if __name__ == "__main__":
    main()