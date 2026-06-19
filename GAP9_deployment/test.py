#!/usr/bin/env python3
"""
compare_pipelines.py
────────────────────
Side-by-side comparison of:
  Pipeline A — ONNX FP32 (reference / gold standard)
  Pipeline B — nntool float simulation (quantized graph)

Both pipelines use:
  • The SAME memory bank (memory_bank.h, normalized — matches C code exactly)
  • The SAME feature extraction (adaptive avg pool 1×1 + 2×2 → cat → L2-norm)
  • The SAME anomaly score (min squared L2 distance)

Input:  int8 .bin files  (CHW, shape 1×3×224×224)
        ONNX dequantizes them back to float before inference.
        nntool receives them as-is (quantize=False).

Usage:
    python compare_pipelines.py

Expected output when everything is working:
    • feat cosine  ≈ 0.98–1.00  (feature maps nearly identical)
    • |score diff| ≈ 0.00–0.01  (small discrepancy from quantization)
    • Anomalous images score HIGHER than normal images (if your .bin set mixes both)

NOTE on score range:
    Scores are NOT bounded to [0, 1].
    For two unit-normalized vectors: dist = 2 - 2·cos_sim  ∈  [0, 4].
    A score of 0.09 means cos_sim ≈ 0.955  (fairly similar).
    A score of 2.00 means cos_sim ≈ 0.000  (orthogonal).
    The C-code threshold 0.006842 ≈ cos_sim 0.9966 — calibrated on normal training set.
"""

import numpy as np
import torch
import torch.nn.functional as F
import onnxruntime as ort
import glob, os, re

from nntool.api import NNGraph
from nntool.quantization.qtype import QType

# ─────────────────────────────────────────────────────────────────────────────
# PATHS  — adjust if your layout differs
# ─────────────────────────────────────────────────────────────────────────────
ONNX_FP32_PATH  = 'model_fp32.onnx'   # gold-standard reference
ONNX_INT8_PATH  = 'model_int8_qdq.onnx'            # what nntool loads
MEMORY_H_PATH   = 'memory_bank.h'
BIN_DIR         = 'input_bins'

# Activation quantization params (from network.c / STM X-CUBE-AI)
INPUT_SCALE       = 0.01845340058207512
INPUT_ZERO_POINT  = -13                 # dequant: float = (int8 - zp) * scale

OUTPUT_SCALE      = 8.462232653982937e-05
OUTPUT_ZERO_POINT = 12

MEMORY_SCALE_H    = 8.0180703662e-04   # defined in memory_bank.h

# Output index in nntool's execute() list after G.fusions()
# Confirmed by diagnostic: index 17 = _net_net_8_Conv_reshape_out, shape (1,76,28,28)
NNTOOL_OUT_IDX    = 17


# ═════════════════════════════════════════════════════════════════════════════
# 1.  MEMORY BANK  (single source of truth)
# ═════════════════════════════════════════════════════════════════════════════

def load_memory_from_header(path: str) -> torch.Tensor:
    """
    Parse memory_bank.h → dequantize → L2-normalize per row.
    This EXACTLY matches compute_anomaly_score() in app_x-cube-ai.c:
        mem_unnorm[d] = int8 * MEMORY_SCALE
        target_mem_val = mem_unnorm[d] / ||mem_unnorm||
    Returns: (64, 380) float32 tensor, each row is a unit vector.
    """
    with open(path) as f:
        content = f.read()
    outer = content[content.find('= {')+2 : content.rfind('};')]
    rows = []
    for m in re.finditer(r'\{([^}]+)\}', outer):
        rows.append([int(x) for x in re.findall(r'-?\d+', m.group(1))])

    mem_i8    = np.array(rows, dtype=np.float32)             # (64, 380)
    mem_float = mem_i8 * MEMORY_SCALE_H                      # dequantize
    norms     = np.linalg.norm(mem_float, axis=1, keepdims=True)
    mem_norm  = mem_float / np.where(norms > 1e-8, norms, 1.0)  # L2-normalize

    t = torch.from_numpy(mem_norm.astype(np.float32))
    row_norms = torch.norm(t, dim=1)
    assert torch.allclose(row_norms, torch.ones_like(row_norms), atol=1e-5), \
        f"Memory bank not unit-normalized! norms range [{row_norms.min():.6f}, {row_norms.max():.6f}]"
    return t  # (64, 380) unit-normalized

def check_memory_discrepancy(header_path: str, pt_path: str = None):
    """
    Compare the header-based memory (normalized) vs the 816-script INT8 memory
    (NOT re-normalized after dequant, ~normalized but not exact).

    The 816 INT8 benchmark uses:
        scale = fp32_memory.abs().max() / 127.0
        mem_int8_dequantized = int8 * scale   ← NO re-normalize
    The C code / nntool script re-normalizes:
        mem = normalize(int8 * scale)         ← explicit L2 norm per row

    These are numerically close (original memory was normalized before quantizing)
    but NOT identical.  Scores calibrated with one will differ slightly from the other.
    """
    print("\n── Memory bank discrepancy check ────────────────────────────────────")

    # Header version (normalized)
    with open(header_path) as f:
        content = f.read()
    outer = content[content.find('= {')+2 : content.rfind('};')]
    rows = []
    for m in re.finditer(r'\{([^}]+)\}', outer):
        rows.append([int(x) for x in re.findall(r'-?\d+', m.group(1))])
    mem_i8    = np.array(rows, dtype=np.float32)
    mem_float = mem_i8 * MEMORY_SCALE_H
    norms     = np.linalg.norm(mem_float, axis=1)
    mem_norm  = mem_float / norms[:, None]

    print(f"  Header (normalized):")
    print(f"    row norms: min={norms.min():.6f}  max={norms.max():.6f}  "
          f"(should be ~1.0 after re-norm)")
    print(f"    pre-norm row norms: min={norms.min():.6f}  max={norms.max():.6f}")
    print(f"    max deviation from unit norm: "
          f"{abs(np.linalg.norm(mem_norm, axis=1) - 1.0).max():.2e}")

    if pt_path and os.path.exists(pt_path):
        # 816-script INT8 version (NOT re-normalized)
        d = torch.load(pt_path, map_location='cpu')
        mi8 = d['memory_int8'].float()
        sc  = d['scale']
        mem_816 = (mi8 * sc).numpy()
        norms_816 = np.linalg.norm(mem_816, axis=1)
        print(f"\n  816-script INT8 (NOT re-normalized):")
        print(f"    row norms: min={norms_816.min():.6f}  max={norms_816.max():.6f}")
        print(f"    max |header_mem - 816_mem|: {abs(mem_norm - mem_816).max():.6f}")
        print(f"    ⚠  If this is non-zero, scores computed with each will differ!")
    else:
        print(f"\n  816-script INT8 .pt file not found at '{pt_path}' — skipping that comparison.")
        print(f"  Key fact: 816 INT8 path uses mem = int8*scale (NOT re-normalized),")
        print(f"  while C code + nntool script use mem = normalize(int8*scale).")
        print(f"  Row norms before re-norm: min={norms.min():.6f}  max={norms.max():.6f}")
        print(f"  (Close to 1 since original FP32 memory was normalized before quantizing.)")


# ═════════════════════════════════════════════════════════════════════════════
# 2.  SHARED POST-PROCESSING  (identical for both pipelines)
# ═════════════════════════════════════════════════════════════════════════════

def extract_features(feat_nchw: np.ndarray) -> torch.Tensor:
    """
    feat_nchw : (1, C, H, W) float32  — raw float output from model (any source)
    Returns   : (1, C + C*4) = (1, 380) L2-normalized float32 tensor

    Exactly matches the 816 benchmark anomaly_score() pooling:
        p1 = F.adaptive_avg_pool2d(f, 1)    # global average → (1, C, 1, 1)
        p2 = F.adaptive_avg_pool2d(f, 2)    # 2×2 → (1, C, 2, 2)
        v  = cat([p1.flatten(1), p2.flatten(1)], 1)   # (1, C + C*4)
        v  = F.normalize(v, dim=1)
    And matches C functions adaptive_avg_pool_1x1 / adaptive_avg_pool_2x2 / pool_features.
    """
    assert feat_nchw.ndim == 4, f"Expected (N,C,H,W), got shape {feat_nchw.shape}"
    t  = torch.from_numpy(feat_nchw.astype(np.float32))
    p1 = F.adaptive_avg_pool2d(t, 1).flatten(1)   # (1, 76)
    p2 = F.adaptive_avg_pool2d(t, 2).flatten(1)   # (1, 304)
    v  = torch.cat([p1, p2], dim=1)               # (1, 380)
    return F.normalize(v, dim=1)                   # unit vector


def anomaly_score(query: torch.Tensor, memory: torch.Tensor) -> float:
    """
    Computes min squared L2 distance between query and every memory vector.
    For unit-normalized inputs: dist = 2 - 2·cos_sim  ∈  [0, 4].
    VALID range is [0, 4] — scores above 1.0 are perfectly meaningful.

    Matches 816 benchmark anomaly_score() and C compute_anomaly_score().
    """
    assert query.shape[-1]  == memory.shape[-1],  "Dimension mismatch"
    dist = ((query.unsqueeze(1) - memory.unsqueeze(0)) ** 2).sum(dim=2)
    return dist.min(dim=1).values.item()


# ═════════════════════════════════════════════════════════════════════════════
# 3.  PIPELINE A — ONNX FP32
# ═════════════════════════════════════════════════════════════════════════════

def run_onnx(session: ort.InferenceSession, bin_path: str) -> np.ndarray:
    """
    1. Read raw int8 .bin  (CHW, shape 1×3×224×224)
    2. Dequantize to float:  fp32 = (int8 - INPUT_ZERO_POINT) * INPUT_SCALE
       This reconstructs the normalized float image the model was trained on.
    3. Run ONNX inference.
    Returns: (1, 76, 28, 28) float32 feature map.
    """
    int8_data = np.fromfile(bin_path, dtype=np.int8).reshape(1, 3, 224, 224)
    fp32_data = (int8_data.astype(np.float32) - INPUT_ZERO_POINT) * INPUT_SCALE
    feat = session.run(None, {session.get_inputs()[0].name: fp32_data})[0]
    assert feat.shape == (1, 76, 28, 28), \
        f"ONNX output shape {feat.shape} — expected (1, 76, 28, 28)"
    return feat   # (1, 76, 28, 28) float32, already in float space


# ═════════════════════════════════════════════════════════════════════════════
# 4.  PIPELINE B — nntool
# ═════════════════════════════════════════════════════════════════════════════

def _patch_qtype(qtype, scale, zp):
    s = np.array([scale], dtype=np.float64) if np.isscalar(scale) else np.array(scale, dtype=np.float64)
    z = np.array([zp],    dtype=np.int8)    if np.isscalar(zp)    else np.array(zp,    dtype=np.int8)
    return QType(
        q=qtype._q, bits=qtype._bits, signed=qtype._signed,
        scale=s, zero_point=z,
        min_val=qtype._min_val, max_val=qtype._max_val,
        quantized_dimension=qtype._quantized_dimension,
        dtype=qtype._dtype, offset=qtype._offset,
        narrow_range=qtype._narrow_range,
        forced=False, asymmetric=True,
        dont_copy_attr=qtype._dont_copy_attr,
    )


def build_nntool_graph(onnx_path: str) -> NNGraph:
    """Load, patch all quantization params (from network.c), fuse, return graph."""
    G = NNGraph.load_graph(
        onnx_path,
        load_quantization=True,
        remove_quantize_ops=True,
        onnx_qdq_qrec_conversion=True,
    )

    def patch(name, in_s=None, in_z=None, out_s=None, out_z=None):
        if name not in G.quantization:
            print(f"  ⚠  MISSING in quantization dict: {name}")
            return
        qrec = G.quantization[name]
        if in_s  is not None and qrec.in_qs  and qrec.in_qs[0]  is not None:
            qrec.in_qs[0]  = _patch_qtype(qrec.in_qs[0],  in_s,  in_z)
        if out_s is not None and qrec.out_qs and qrec.out_qs[0] is not None:
            qrec.out_qs[0] = _patch_qtype(qrec.out_qs[0], out_s, out_z)

    # Ground-truth activation quantization params (from network.c)
    s0,z0 = 0.01845340058207512,     -13
    s1,z1 = 0.009542142041027546,   -128
    s2,z2 = 0.003998782020062208,   -128
    s3,z3 = 0.000694780726917088,   -128
    s4,z4 = 0.00039253884460777044, -128
    s5,z5 = 8.462232653982937e-05,    12

    patch("input_1",                          out_s=s0,out_z=z0)
    patch("_net_net_0_Conv_reshape_in",        in_s=s0,in_z=z0, out_s=s0,out_z=z0)
    patch("_net_net_0_Conv",                   in_s=s0,in_z=z0, out_s=s1,out_z=z1)
    patch("_net_net_0_Conv_reshape_out",       in_s=s1,in_z=z1, out_s=s1,out_z=z1)
    patch("_net_net_2_Conv_reshape_in",        in_s=s1,in_z=z1, out_s=s1,out_z=z1)
    patch("_net_net_2_Conv_reshape_in_qout0",  in_s=s1,in_z=z1, out_s=s1,out_z=z1)
    patch("_net_net_2_Conv",                   in_s=s1,in_z=z1, out_s=s2,out_z=z2)
    patch("_net_net_2_Conv_reshape_out",       in_s=s2,in_z=z2, out_s=s2,out_z=z2)
    patch("_net_net_4_Conv_reshape_in",        in_s=s2,in_z=z2, out_s=s2,out_z=z2)
    patch("_net_net_4_Conv_reshape_in_qout0",  in_s=s2,in_z=z2, out_s=s2,out_z=z2)
    patch("_net_net_4_Conv",                   in_s=s2,in_z=z2, out_s=s3,out_z=z3)
    patch("_net_net_4_Conv_reshape_out",       in_s=s3,in_z=z3, out_s=s3,out_z=z3)
    patch("_net_net_6_Conv_reshape_in",        in_s=s3,in_z=z3, out_s=s3,out_z=z3)
    patch("_net_net_6_Conv_reshape_in_qout0",  in_s=s3,in_z=z3, out_s=s3,out_z=z3)
    patch("_net_net_6_Conv",                   in_s=s3,in_z=z3, out_s=s4,out_z=z4)
    patch("_net_net_6_Conv_reshape_out",       in_s=s4,in_z=z4, out_s=s4,out_z=z4)
    patch("_net_net_8_Conv_reshape_in",        in_s=s4,in_z=z4, out_s=s4,out_z=z4)
    patch("_net_net_8_Conv_reshape_in_qout0",  in_s=s4,in_z=z4, out_s=s4,out_z=z4)
    patch("_net_net_8_Conv",                   in_s=s4,in_z=z4, out_s=s5,out_z=z5)
    patch("_net_net_8_Conv_reshape_out",       in_s=s5,in_z=z5, out_s=s5,out_z=z5)
    patch("_net_net_8_Conv_reshape_out_qout0", in_s=s5,in_z=z5, out_s=s5,out_z=z5)
    patch("output_1",                          in_s=s5,in_z=z5, out_s=s5,out_z=z5)

    G.fusions('scaled_match_group')
    return G


def run_nntool(G: NNGraph, bin_path: str) -> np.ndarray:
    """
    Feed raw int8 data (as float) to nntool.
    With quantize=False nntool treats the int8 values as the pre-quantized input
    and runs the quantized graph in float simulation mode.
    Output at NNTOOL_OUT_IDX is ALREADY in float space — do NOT dequantize again.
    Returns: (1, 76, 28, 28) float32 feature map.
    """
    int8_data = np.fromfile(bin_path, dtype=np.int8).reshape(1, 3, 224, 224)
    outputs   = G.execute([int8_data], quantize=False, dequantize=False)
    feat      = np.array(outputs[NNTOOL_OUT_IDX][0])
    assert feat.shape == (1, 76, 28, 28), \
        f"nntool output shape {feat.shape} — check NNTOOL_OUT_IDX={NNTOOL_OUT_IDX}"
    return feat   # (1, 76, 28, 28) float32, already in float space


# ═════════════════════════════════════════════════════════════════════════════
# 5.  MAIN COMPARISON
# ═════════════════════════════════════════════════════════════════════════════

def main():
    # ── Memory ───────────────────────────────────────────────────────────────
    print("=" * 72)
    print("  PIPELINE COMPARISON: ONNX FP32  vs  nntool INT8 simulation")
    print("=" * 72)

    print(f"\nLoading memory bank from {MEMORY_H_PATH} ...")
    memory = load_memory_from_header(MEMORY_H_PATH)
    print(f"  Shape : {memory.shape}")
    norms  = torch.norm(memory, dim=1)
    print(f"  Norms : {norms.min():.8f} – {norms.max():.8f}  (all should be 1.0)")
    print(f"  Range : [{memory.min():.6f}, {memory.max():.6f}]")

    # Optional: surface the 816 INT8 memory vs header discrepancy
    check_memory_discrepancy(MEMORY_H_PATH, pt_path='onnx_models/memory_int8.pt')

    # ── Build models ─────────────────────────────────────────────────────────
    print(f"\nBuilding ONNX session from {ONNX_FP32_PATH} ...")
    onnx_session = ort.InferenceSession(ONNX_FP32_PATH,
                                        providers=['CPUExecutionProvider'])

    print(f"Building nntool graph from {ONNX_INT8_PATH} ...")
    G = build_nntool_graph(ONNX_INT8_PATH)

    # ── Find .bin files ───────────────────────────────────────────────────────
    bin_files = sorted(glob.glob(os.path.join(BIN_DIR, '*.bin')))
    if not bin_files:
        print(f"\nERROR: no .bin files found in '{BIN_DIR}/'")
        return
    print(f"\nFound {len(bin_files)} .bin files in '{BIN_DIR}/'\n")

    # ── Per-file comparison ───────────────────────────────────────────────────
    W = 50  # filename column width
    print(f"{'File':{W}}  {'ONNX':>10}  {'NNtool':>10}  {'|Δscore|':>10}  "
          f"{'q·cosine':>9}  {'feat‖Δ‖':>9}")
    print("─" * (W + 58))

    all_onnx, all_nnt = [], []

    for bf in bin_files:
        name = os.path.basename(bf)

        # Pipeline A — ONNX FP32
        feat_onnx  = run_onnx(onnx_session, bf)
        query_onnx = extract_features(feat_onnx)
        score_onnx = anomaly_score(query_onnx, memory)

        # Pipeline B — nntool
        feat_nnt   = run_nntool(G, bf)
        query_nnt  = extract_features(feat_nnt)
        score_nnt  = anomaly_score(query_nnt, memory)

        # Diagnostics
        cos_sim    = (query_onnx * query_nnt).sum().item()  # should be ~1.0
        feat_l2    = float(np.linalg.norm(feat_onnx.flatten() - feat_nnt.flatten()))
        delta      = abs(score_onnx - score_nnt)

        all_onnx.append(score_onnx)
        all_nnt.append(score_nnt)

        flag = " ←" if abs(cos_sim) < 0.9 else ""   # flag big divergences
        print(f"{name:{W}}  {score_onnx:>10.6f}  {score_nnt:>10.6f}  {delta:>10.6f}  "
              f"{cos_sim:>9.4f}  {feat_l2:>9.4f}{flag}")

    # ── Summary ───────────────────────────────────────────────────────────────
    ao, an = np.array(all_onnx), np.array(all_nnt)
    deltas = np.abs(ao - an)

    print("\n── Score summary ────────────────────────────────────────────────────")
    print(f"  {'':25}  {'ONNX FP32':>12}  {'NNtool INT8':>12}")
    print(f"  {'min':25}  {ao.min():>12.6f}  {an.min():>12.6f}")
    print(f"  {'max':25}  {ao.max():>12.6f}  {an.max():>12.6f}")
    print(f"  {'mean':25}  {ao.mean():>12.6f}  {an.mean():>12.6f}")
    print(f"  {'std':25}  {ao.std():>12.6f}  {an.std():>12.6f}")
    print(f"\n  Mean |score diff|   : {deltas.mean():.6f}")
    print(f"  Max  |score diff|   : {deltas.max():.6f}")
    print(f"  Correlation (r)     : {np.corrcoef(ao, an)[0,1]:.6f}  (want ~1.0)")

    # ── Interpretation guide ──────────────────────────────────────────────────
    print("\n── Interpretation guide ─────────────────────────────────────────────")
    print("  feat cosine ~1.0  → nntool feature maps match ONNX FP32 ✓")
    print("  feat cosine <0.9  → feature maps diverge — check input handling ✗")
    print()
    print("  Score range [0, 4] is CORRECT for normalized vectors:")
    print("    dist = 2 - 2·cos_sim  →  cos_sim=0.97  →  dist=0.06")
    print("    dist = 2 - 2·cos_sim  →  cos_sim=0.50  →  dist=1.00")
    print("    dist = 2 - 2·cos_sim  →  cos_sim=0.00  →  dist=2.00")
    print()
    print("  C-code threshold 0.006842 → cos_sim > 0.9966 classified as NORMAL")
    print("  If this was calibrated with non-normalized memory (816 INT8 path),")
    print("  it may need recalibration with the normalized memory used here.")

    # ── Key discrepancy: 816 INT8 vs C-code memory normalization ─────────────
    print("\n── Known discrepancy: memory bank normalization ─────────────────────")
    print("  816 benchmark INT8 path (quantize_onnx.py):")
    print("    mem_int8_dequantized = int8 * scale     ← NOT re-normalized")
    print("    comment says 'DO NOT re-normalize it in Python anymore!'")
    print()
    print("  C code (app_x-cube-ai.c) + this script + nntool:")
    print("    mem_val = (int8 * MEMORY_SCALE) / ||int8 * MEMORY_SCALE||  ← re-normalized")
    print()
    print("  Impact: small (original FP32 memory was normalized, so int8*scale ≈ unit),")
    print("  but the threshold 0.006842 was calibrated with one convention; if using")
    print("  the other, recompute threshold via compute_threshold() from the 816 script.")


if __name__ == '__main__':
    main()
