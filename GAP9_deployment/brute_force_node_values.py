from nntool.api import NNGraph
from nntool.quantization.qtype import QType
import numpy as np
import glob
import os
from copy import deepcopy

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

# ── 2. Python inference on your .bin files ────────────────────────────────────
# This runs on your laptop, no GAP9 needed.
# Use this to verify the model produces sensible feature maps.

def run_inference(G, bin_path):
    data = np.fromfile(bin_path, dtype=np.int8)
    inp = data.reshape(1, 3, 224, 224)           # CHW confirmed
    outputs = G.execute([inp], quantize=False, dequantize=False)
    feat = outputs[18][0]                          # shape (1, 76, 28, 28)
    print(f"  {os.path.basename(bin_path)}: output shape={feat.shape}, "
          f"min={feat.min()}, max={feat.max()}, mean={feat.mean():.4f}")
    return feat

print("\n── Python inference verification ────────────────────────────────────")
bin_files = sorted(glob.glob('input_bins/*.bin'))
if not bin_files:
    print("⚠️  No .bin files found in input_bins/")
else:
    for bf in bin_files[:20]:   # test first 3 to keep output short
        run_inference(G, bf)

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