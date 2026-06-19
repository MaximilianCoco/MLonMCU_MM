from nntool.api import NNGraph
import numpy as np
import os

print("Loading QDQ ONNX model (quantization already embedded)...")
G = NNGraph.load_graph(
    'model_int8_qdq.onnx',
    load_quantization=True,
    remove_quantize_ops=False,
    onnx_qdq_qrec_conversion=False  # Keep Q/DQ as actual nodes, don't convert
)

print("Graph loaded. Input/Output nodes:")
for node in G.input_nodes():
    print(f"  input {node.name}: dims={node.out_dims}")
    qrec = getattr(node, 'out_quantization', None)
    if qrec and len(qrec):
        q = qrec[0]
        scale = float(getattr(q, 'scale', None) or 0)
        zp = int(getattr(q, 'zero_point', None) or 0)
        print(f"    → LOADED scale={scale:.15f}, zp={zp}")
for node in G.output_nodes():
    print(f"  output {node.name}: dims={node.in_dims}")
    qrec = getattr(node, 'out_quantization', None)
    if qrec and len(qrec):
        q = qrec[0]
        scale = float(getattr(q, 'scale', None) or 0)
        zp = int(getattr(q, 'zero_point', None) or 0)
        print(f"    → LOADED scale={scale:.15f}, zp={zp}")

print("\n=== ALL NODES IN GRAPH ===")
for node in G.nodes():
    node_type = node.__class__.__name__
    qrec = getattr(node, 'out_quantization', None)
    qstr = ""
    if qrec and len(qrec):
        q = qrec[0]
        scale = float(getattr(q, 'scale', None) or 0)
        zp = int(getattr(q, 'zero_point', None) or 0)
        qstr = f" [scale={scale:.6e}, zp={zp}]"
    print(f"  {node.name:40s} {node_type:20s}{qstr}")

# --- Apply fusions (but NO re-quantization) ---
print("\nApplying fusions...")
#G.fusions('scaled_match_group')

# Try to remove unnecessary quantize operators (optional, for cleanup)
try:
    print("Removing unnecessary quantize operators...")
    G.fusions('remove_unnecessary_quantize_operators')
except Exception as e:
    print(f"  (skipped — not available: {e})")

print("\n=== QUANTIZATION BEFORE CODE GENERATION ===")
print("Sampling first 5 Conv/MatMul layers:")
count = 0
for node in G.nodes():
    if 'Conv' in node.__class__.__name__ or 'MatMul' in node.__class__.__name__:
        qrec = getattr(node, 'out_quantization', None)
        if qrec and len(qrec):
            q = qrec[0]
            scale = float(getattr(q, 'scale', None) or 0)
            zp = int(getattr(q, 'zero_point', None) or 0)
            print(f"  {node.name}: scale={scale:.9e}, zp={zp}")
            count += 1
            if count >= 5:
                break

print("\nPost-fusion graph:")
G.show()

# --- Generate GAP9 project ---
# NO G.quantize() call — quantization is already in the QDQ model
# NNTool will respect the embedded int8 scales/zero-points from Q/DQ layers
print("\nGenerating GAP9 project...")
os.makedirs('gap9_int8_qdq', exist_ok=True)
G.gen_project(
    input_tensors=[np.zeros((1, 224, 224, 3), dtype=np.int8)],
    directory='gap9_int8_qdq',
    platform='gvsoc',
    cmake=True,
)

print("✓ Project generated in 'gap9_int8_qdq/'")
print("\nNOTE:")
print("- Your QDQ model is already quantized (scales/zp embedded in Q/DQ ops)")
print("- NNTool will NOT re-quantize; it respects your original quantization")
print("- Asymmetric Q/DQ layers are expected and handled automatically")
print("- Use the generated C code as-is with int8 input/output")
