from nntool.api import NNGraph
from nntool.quantization.qtype import QType
import numpy as np
import glob
import os
from copy import deepcopy
import torch
import torch.nn.functional as F
import re

G = NNGraph.load_graph(
    'model_int8_qdq.onnx',
    load_quantization=True,
    remove_quantize_ops=True,
    onnx_qdq_qrec_conversion=True
)

# After loading G, before any patching
for node in G.nodes():
    print(f"{node.name}: in_dims={node.in_dims}  out_dims={node.out_dims}")

inp = G.inputs()[0]
print(f"Input node name: {inp.name}")
print(f"Input shape: {inp.out_dims}")

def patch_qtype(qtype, scale, zp):
    """Reconstruct a QType via its constructor, overriding scale and zero_point."""
    scale_arr = np.array([scale], dtype=np.float64) if np.isscalar(scale) else np.array(scale, dtype=np.float64)
    zp_arr    = np.array([zp],    dtype=np.int8)    if np.isscalar(zp)    else np.array(zp,    dtype=np.int8)
    return QType(
        q=qtype._q,
        bits=qtype._bits,
        signed=qtype._signed,
        scale=scale_arr,
        zero_point=zp_arr,
        min_val=qtype._min_val,
        max_val=qtype._max_val,
        quantized_dimension=qtype._quantized_dimension,
        dtype=qtype._dtype,
        offset=qtype._offset,
        narrow_range=qtype._narrow_range,
        forced=False,
        asymmetric=True,          # must be True to allow non-zero zero_point
        dont_copy_attr=qtype._dont_copy_attr,
    )

def patch(node_name, in_scale=None, in_zp=None, out_scale=None, out_zp=None):
    if node_name not in G.quantization:
        print(f"⚠️  MISSING: {node_name}")
        return
    qrec = G.quantization[node_name]
    if in_scale is not None and qrec.in_qs and qrec.in_qs[0] is not None:
        qrec.in_qs[0] = patch_qtype(qrec.in_qs[0], in_scale, in_zp)
    if out_scale is not None and qrec.out_qs and qrec.out_qs[0] is not None:
        qrec.out_qs[0] = patch_qtype(qrec.out_qs[0], out_scale, out_zp)
    print(f"✓ Patched {node_name}")

# Ground truth activation scales and zero-points from network.c
s0_scale, s0_zp = 0.01845340058207512,      -13
s1_scale, s1_zp = 0.009542142041027546,     -128
s2_scale, s2_zp = 0.003998782020062208,     -128
s3_scale, s3_zp = 0.000694780726917088,     -128
s4_scale, s4_zp = 0.00039253884460777044,   -128
s5_scale, s5_zp = 8.462232653982937e-05,      12

patch("input_1",
      out_scale=s0_scale, out_zp=s0_zp)

patch("_net_net_0_Conv_reshape_in",
      in_scale=s0_scale,  in_zp=s0_zp,
      out_scale=s0_scale, out_zp=s0_zp)
patch("_net_net_0_Conv",
      in_scale=s0_scale,  in_zp=s0_zp,
      out_scale=s1_scale, out_zp=s1_zp)
patch("_net_net_0_Conv_reshape_out",
      in_scale=s1_scale,  in_zp=s1_zp,
      out_scale=s1_scale, out_zp=s1_zp)

patch("_net_net_2_Conv_reshape_in",
      in_scale=s1_scale,  in_zp=s1_zp,
      out_scale=s1_scale, out_zp=s1_zp)
patch("_net_net_2_Conv_reshape_in_qout0",
      in_scale=s1_scale,  in_zp=s1_zp,
      out_scale=s1_scale, out_zp=s1_zp)
patch("_net_net_2_Conv",
      in_scale=s1_scale,  in_zp=s1_zp,
      out_scale=s2_scale, out_zp=s2_zp)
patch("_net_net_2_Conv_reshape_out",
      in_scale=s2_scale,  in_zp=s2_zp,
      out_scale=s2_scale, out_zp=s2_zp)

patch("_net_net_4_Conv_reshape_in",
      in_scale=s2_scale,  in_zp=s2_zp,
      out_scale=s2_scale, out_zp=s2_zp)
patch("_net_net_4_Conv_reshape_in_qout0",
      in_scale=s2_scale,  in_zp=s2_zp,
      out_scale=s2_scale, out_zp=s2_zp)
patch("_net_net_4_Conv",
      in_scale=s2_scale,  in_zp=s2_zp,
      out_scale=s3_scale, out_zp=s3_zp)
patch("_net_net_4_Conv_reshape_out",
      in_scale=s3_scale,  in_zp=s3_zp,
      out_scale=s3_scale, out_zp=s3_zp)

patch("_net_net_6_Conv_reshape_in",
      in_scale=s3_scale,  in_zp=s3_zp,
      out_scale=s3_scale, out_zp=s3_zp)
patch("_net_net_6_Conv_reshape_in_qout0",
      in_scale=s3_scale,  in_zp=s3_zp,
      out_scale=s3_scale, out_zp=s3_zp)
patch("_net_net_6_Conv",
      in_scale=s3_scale,  in_zp=s3_zp,
      out_scale=s4_scale, out_zp=s4_zp)
patch("_net_net_6_Conv_reshape_out",
      in_scale=s4_scale,  in_zp=s4_zp,
      out_scale=s4_scale, out_zp=s4_zp)

patch("_net_net_8_Conv_reshape_in",
      in_scale=s4_scale,  in_zp=s4_zp,
      out_scale=s4_scale, out_zp=s4_zp)
patch("_net_net_8_Conv_reshape_in_qout0",
      in_scale=s4_scale,  in_zp=s4_zp,
      out_scale=s4_scale, out_zp=s4_zp)
patch("_net_net_8_Conv",
      in_scale=s4_scale,  in_zp=s4_zp,
      out_scale=s5_scale, out_zp=s5_zp)
patch("_net_net_8_Conv_reshape_out",
      in_scale=s5_scale,  in_zp=s5_zp,
      out_scale=s5_scale, out_zp=s5_zp)
patch("_net_net_8_Conv_reshape_out_qout0",
      in_scale=s5_scale,  in_zp=s5_zp,
      out_scale=s5_scale, out_zp=s5_zp)

patch("output_1",
      in_scale=s5_scale,  in_zp=s5_zp,
      out_scale=s5_scale, out_zp=s5_zp)

# Verify
print("\n── Post-patch verification (activation nodes only) ──────────────────")
for key in sorted(G.quantization.keys()):
    if "weights" in key or "bias" in key:
        continue
    qrec = G.quantization[key]
    in_s  = qrec.in_qs[0].scale       if qrec.in_qs  and qrec.in_qs[0]  is not None else "N/A"
    out_s = qrec.out_qs[0].scale      if qrec.out_qs and qrec.out_qs[0] is not None else "N/A"
    in_z  = qrec.in_qs[0].zero_point  if qrec.in_qs  and qrec.in_qs[0]  is not None else "N/A"
    out_z = qrec.out_qs[0].zero_point if qrec.out_qs and qrec.out_qs[0] is not None else "N/A"
    print(f"  {key}: in=({in_s}, zp={in_z}) | out=({out_s}, zp={out_z})")

print("\nApplying fusions...")
G.fusions('scaled_match_group')

print("\nPost-fusion graph nodes:")
for i, node in enumerate(G.nodes()):
    print(f"  [{i:2d}] {node.name}: out_dims={node.out_dims}")

print(f"\nGraph output node(s): {[n.name for n in G.outputs()]}")

# ── 2. Python inference on your .bin files ────────────────────────────────────
# This runs on your laptop, no GAP9 needed.
# Use this to verify the model produces sensible feature maps.



# ── Memory bank loader ────────────────────────────────────────────────────────
def load_memory_bank(pt_path):
    """Load the int8 memory bank from the .pt file used in your Python pipeline."""
    d = torch.load(pt_path, map_location="cpu")
    mem_int8 = d["memory_int8"].float()   # (64, 380)
    scale    = d["scale"]
    mem_float = mem_int8 * scale           # dequantize
    mem_norm  = F.normalize(mem_float, dim=1)  # L2 normalize each row
    return mem_norm  # (64, 380) float32

def load_memory_bank_from_header(header_path):
    """
    Alternative: parse memory_bank.h directly if you don't have the .pt file.
    Matches the C code: dequantize with MEMORY_SCALE then L2-renormalize.
    """
    MEMORY_SCALE = 8.0180703662e-04

    with open(header_path, 'r') as f:
        content = f.read()

    # Extract all rows between outer { }
    outer = content[content.find('= {')+2 : content.rfind('};')]
    rows = []
    for row_match in re.finditer(r'\{([^}]+)\}', outer):
        vals = [int(x) for x in re.findall(r'-?\d+', row_match.group(1))]
        rows.append(vals)

    mem_int8  = np.array(rows, dtype=np.float32)          # (64, 380)
    mem_float = mem_int8 * MEMORY_SCALE                    # dequantize
    norms     = np.linalg.norm(mem_float, axis=1, keepdims=True)
    mem_norm  = mem_float / np.where(norms > 1e-8, norms, 1.0)
    return torch.from_numpy(mem_norm)                      # (64, 380)

# ── Feature extraction from model output ─────────────────────────────────────
OUTPUT_SCALE      = 8.462232653982937e-05
OUTPUT_ZERO_POINT = 12

def extract_features(feat_chw):
    """
    feat_chw: numpy array (1, 76, 28, 28) — already float, nntool dequantized it
    Returns: normalized feature vector (1, 380) float32 tensor
    """
    # nntool already dequantized — use directly
    t = torch.from_numpy(feat_chw.astype(np.float32))  # (1, 76, 28, 28)

    p1 = F.adaptive_avg_pool2d(t, 1).flatten(1)   # (1, 76)
    p2 = F.adaptive_avg_pool2d(t, 2).flatten(1)   # (1, 304)

    v = torch.cat([p1, p2], dim=1)                 # (1, 380)
    v = F.normalize(v, dim=1)

    return v  # (1, 380)

# ── Anomaly score ─────────────────────────────────────────────────────────────
def anomaly_score(query_vec, memory):
    """
    query_vec: (1, 380) normalized float32
    memory:    (64, 380) normalized float32
    Returns scalar: min squared L2 distance to memory bank
    Matches Python benchmark anomaly_score() exactly.
    """
    # (1, 64): squared L2 distance to each memory vector
    dist = ((query_vec.unsqueeze(1) - memory.unsqueeze(0)) ** 2).sum(dim=2)
    return dist.min(dim=1).values.item()

def run_inference_with_score(G, bin_path, memory):
    data = np.fromfile(bin_path, dtype=np.int8)
    inp  = data.reshape(1, 3, 224, 224)

    outputs = G.execute([inp], quantize=False, dequantize=False)

    # ✓ Correct index — (1, 76, 28, 28), already float from nntool simulation
    feat = np.array(outputs[17][0])

    # ✓ NO manual dequantization — nntool already runs in float
    # REMOVE: feat_float = (feat.astype(np.float32) - OUTPUT_ZERO_POINT) * OUTPUT_SCALE

    query = extract_features(feat)   # extract_features already expects float input

    print(f"feat shape: {feat.shape}, range: [{feat.min():.4f}, {feat.max():.4f}]")
    print(f"Query norm: {torch.norm(query):.4f}")       # should be ~1.0
    print(f"Query range: min={query.min():.4f}, max={query.max():.4f}")  # should be mixed +/-

    sims = (query @ memory.T).squeeze()
    print(f"Cosine sims: min={sims.min():.4f}, max={sims.max():.4f}, mean={sims.mean():.4f}")

    score = anomaly_score(query, memory)
    print(f"  {os.path.basename(bin_path):50s}  score={score:.6f}")
    return score


# ── Run ───────────────────────────────────────────────────────────────────────
# Pick whichever memory source you have available:
# memory = load_memory_bank('onnx_models/memory_int8.pt')
memory = load_memory_bank_from_header('memory_bank.h')

print("\n── Inference + anomaly scores ───────────────────────────────────────")
bin_files = sorted(glob.glob('input_bins/*.bin'))
scores = []
for bf in bin_files:
    s = run_inference_with_score(G, bf, memory)
    scores.append((os.path.basename(bf), s))

# Print summary
print("\n── Score summary ────────────────────────────────────────────────────")
vals = [s for _, s in scores]
print(f"  n={len(vals)}  min={min(vals):.6f}  max={max(vals):.6f}  "
      f"mean={np.mean(vals):.6f}  std={np.std(vals):.6f}")

# ── 3. Generate GAP9 project ─────────────────────────────────────────────────
# This produces C code for the chip. Completely separate from step 2.
# input_tensors here is just a shape hint — values are ignored.

print("Generating GAP9 project...")
os.makedirs('gap9_int8_qdq_brute_force', exist_ok=True)
G.gen_project(
    input_tensors=[np.zeros((1, 3, 224, 224), dtype=np.int8)],
    directory='gap9_int8_qdq_brute_force',
    platform='gvsoc',
    cmake=True,
)
print("✓ Done.")