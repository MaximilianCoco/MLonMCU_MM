from nntool.api import NNGraph
import numpy as np
import os

G = NNGraph.load_graph(
    'model_int8_qdq.onnx',
    load_quantization=True,
    remove_quantize_ops=False,  # Keep Q/DQ ops to access quantization
    onnx_qdq_qrec_conversion=False  # Don't convert, keep as nodes
)

# Helper to create/replace QType with new scale/zero_point
def replace_qtype(qtype, scale, zero_point):
    """Create a new QType with updated scale and zero_point"""
    return type(qtype)(
        q=qtype.q,
        bits=qtype.bits,
        signed=qtype.signed,
        scale=np.array([scale], dtype=np.float64) if isinstance(scale, (int, float)) else np.array(scale, dtype=np.float64),
        zero_point=np.array([zero_point], dtype=np.int8) if isinstance(zero_point, (int, float)) else np.array(zero_point, dtype=np.int8),
        min_val=qtype.min_val,
        max_val=qtype.max_val,
        asymmetric=qtype.asymmetric,
        narrow_range=qtype.narrow_range,
        forced=qtype.forced,
        attr=qtype.attr,
    )

# Reference quantization from STM32 network.c
# Node names must match the quantization dict keys from G.quantization
STM_QUANT = {
    "input_DequantizeLinear":                           {"scale": 0.01845340058207512,      "zp": -13},
    "_net_net_1_Relu_output_0_DequantizeLinear":       {"scale": 0.009542142041027546,     "zp": -128},
    "_net_net_3_Relu_output_0_DequantizeLinear":       {"scale": 0.003998782020062208,     "zp": -128},
    "_net_net_5_Relu_output_0_DequantizeLinear":       {"scale": 0.000694780726917088,     "zp": -128},
    "_net_net_7_Relu_output_0_DequantizeLinear":       {"scale": 0.00039253884460777044,   "zp": -128},
    "features_QuantizeLinear_Input_DequantizeLinear":  {"scale": 8.462232653982937e-05,   "zp": 12},
}

print("Patching quantization values to match STM32 reference...")
print("=" * 60)

# Debug: Show available quantization keys
print("\nAvailable quantization nodes in graph:")
for key in sorted(G.quantization.keys()):
    print(f"  - {key}")
print()

# Patch each node that appears in the quantization dict
for node_name, target_vals in STM_QUANT.items():
    if node_name not in G.quantization:
        print(f"⚠️  WARNING: Node '{node_name}' not found in quantization dict")
        continue
    
    qrec = G.quantization[node_name]
    target_scale = target_vals["scale"]
    target_zp = target_vals["zp"]
    
    print(f"\n  Patching: {node_name}")
    print(f"    Target: scale={target_scale:.6e}, zp={target_zp}")
    
    # Update out_qs (output quantization) — always present for Q/DQ nodes
    if hasattr(qrec, 'out_qs') and qrec.out_qs and qrec.out_qs[0] is not None:
        qrec.out_qs[0] = replace_qtype(qrec.out_qs[0], target_scale, target_zp)
        print(f"    ✓ Updated out_qs")
    else:
        print(f"    ⚠️  out_qs not available or empty")
    
    # Update in_qs only if it exists and is not None
    if hasattr(qrec, 'in_qs') and qrec.in_qs and qrec.in_qs[0] is not None:
        qrec.in_qs[0] = replace_qtype(qrec.in_qs[0], target_scale, target_zp)
        print(f"    ✓ Updated in_qs")
    # else: skip silently if in_qs is None

print("\n" + "=" * 60)
print("Quantization patching complete.\n")

# --- Fuse and generate ---
print("Applying fusions...")
#G.fusions('scaled_match_group')

print("Generating GAP9 project...")
os.makedirs('gap9_int8_qdq', exist_ok=True)
G.gen_project(
    input_tensors=[np.zeros((1, 224, 224, 3), dtype=np.int8)],
    directory='gap9_int8_qdq_brute_force',
    platform='gvsoc',
    cmake=True,
)

print("✓ Project generated in 'gap9_int8_qdq_brute_force/'")
print("\nQuantization values now match STM32 reference implementation.")
