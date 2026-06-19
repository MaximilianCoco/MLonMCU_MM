#!/usr/bin/env python3
"""
GAP9 NNTool deployment — pre-quantized QDQ ONNX to GAP9 AutoTiler project.

Final working version.
"""

import argparse
import os
import sys
import numpy as np

try:
    import onnx
    from onnx import numpy_helper
except ImportError:
    sys.exit("pip install onnx")

try:
    from nntool.api import NNGraph
    from nntool.api.types import ExpressionFusionNode
    from nntool.api.utils import quantization_options
except ImportError as exc:
    sys.exit(f"NNTool not found: {exc}\nSource the GAP SDK first.")


# -----------------------------------------------------------------------------
# Step 1: Extract QDQ activation quantizers in order
# -----------------------------------------------------------------------------

def extract_qdq_activations(qdq_path: str) -> list:
    model = onnx.load(qdq_path)
    graph = model.graph
    inits = {init.name: numpy_helper.to_array(init) for init in graph.initializer}

    ordered = []
    for node in graph.node:
        if node.op_type != "QuantizeLinear":
            continue
        if len(node.input) < 3:
            continue
        scale_arr = inits.get(node.input[1])
        zp_arr = inits.get(node.input[2])
        if scale_arr is None or zp_arr is None:
            continue
        # Skip per-channel (weight) quantizers -> vector scales
        if scale_arr.ndim > 0 and scale_arr.size > 1:
            continue
        scale = float(scale_arr.flat[0])
        zp = int(zp_arr.flat[0])
        ordered.append({"scale": scale, "zp": zp, "tensor": node.output[0]})

    print(f"\nExtracted {len(ordered)} activation QDQ nodes:")
    for i, p in enumerate(ordered):
        print(f"  [{i}] scale={p['scale']:.6e}  zp={p['zp']:4d}  tensor='{p['tensor']}'")
    return ordered


# -----------------------------------------------------------------------------
# Step 2: Load and fuse
# -----------------------------------------------------------------------------

def load_and_fuse(model_path: str, verbose: bool) -> NNGraph:
    print(f"\n{'='*60}\n  Loading: {model_path}\n{'='*60}")
    G = NNGraph.load_graph(model_path, load_quantization=False)
    print("  Loaded with load_quantization=False (float32 mode)")
    if verbose:
        print("\nRaw graph:"); G.show()
    print("\n[1/3] Running scaled_match_group fusions ...")
    G.fusions("scaled_match_group")
    if verbose:
        print("\nAfter fusions:")
        for n in G.nodes():
            print(f"  {n.name!r:40s} type={type(n).__name__}")
    return G


# -----------------------------------------------------------------------------
# Step 3: Build stats dictionary for nodes that need quantization
# -----------------------------------------------------------------------------

def build_stats_from_qdq(G: NNGraph, qdq_list: list) -> dict:
    TARGET_TYPES = {"Conv2DNode", "OutputNode"}
    eligible_nodes = [n for n in G.nodes() if type(n).__name__ in TARGET_TYPES]
    print(f"\n  Eligible nodes for QDQ mapping: {[n.name for n in eligible_nodes]}")

    def scale_zp_to_range_dict(scale, zp):
        real_min = scale * (-128 - zp)
        real_max = scale * (127 - zp)
        extent = max(abs(real_min), abs(real_max))
        return {"min": -extent, "max": extent}

    stats = {}
    if len(qdq_list) < 1:
        return stats

    # Input node
    in_nodes = list(G.input_nodes())
    if in_nodes:
        inp_node = in_nodes[0]
        qdq0 = qdq_list[0]
        rng = scale_zp_to_range_dict(qdq0["scale"], qdq0["zp"])
        n_out = len(inp_node.out_dims) if inp_node.out_dims else 1
        stats[inp_node.name] = {
            "range_in": [rng],
            "range_out": [rng] * n_out
        }
        print(f"  Mapped input '{inp_node.name}' <- QDQ[0] (scale={qdq0['scale']:.4e})")

    # Map remaining QDQ to eligible nodes (including output)
    qdq_idx = 1
    for node in eligible_nodes:
        if qdq_idx >= len(qdq_list):
            break
        qdq = qdq_list[qdq_idx]
        rng = scale_zp_to_range_dict(qdq["scale"], qdq["zp"])
        n_in = len(node.in_dims) if node.in_dims else 1
        n_out = len(node.out_dims) if node.out_dims else 1
        stats[node.name] = {
            "range_in": [rng] * n_in,
            "range_out": [rng] * n_out
        }
        print(f"  Mapped {type(node).__name__} '{node.name}' <- QDQ[{qdq_idx}] (scale={qdq['scale']:.4e})")
        qdq_idx += 1

    if qdq_idx < len(qdq_list):
        print(f"  Warning: {len(qdq_list)-qdq_idx} unused QDQ entries")
    return stats


# -----------------------------------------------------------------------------
# Step 4: Quantize
# -----------------------------------------------------------------------------

def quantize_graph(G: NNGraph, stats: dict, verbose: bool) -> None:
    print("\n[2/3] Quantizing with injected stats ...")
    node_opts = {
        node.name: quantization_options(scheme="float", float_type="float32")
        for node in G.nodes(ExpressionFusionNode)
    }
    G.quantize(
        stats,
        schemes=["scaled"],
        graph_options=quantization_options(
            use_ne16=True,
            const_clip_type="none",
            clip_type="none",
        ),
        node_options=node_opts if node_opts else None,
    )
    if verbose:
        # Fix: show() does not accept show_quantization argument
        G.show()


# -----------------------------------------------------------------------------
# Step 5: Verify scales
# -----------------------------------------------------------------------------

def verify_scales(G: NNGraph, qdq_list: list) -> dict:
    print("\n── Quantization verification ───────────────────────────────────")
    print(f"  {'Node':<38}  {'GAP9 scale':>12}  {'QDQ scale':>12}  "
          f"{'GAP9 zp':>7}  {'QDQ zp':>6}  Notes")
    print(f"  {'-'*38}  {'-'*12}  {'-'*12}  {'-'*7}  {'-'*6}  -----")

    qdq_iter = iter(qdq_list)
    gap9_io = {}
    for node in G.nodes():
        qrecs = getattr(node, "out_quantization", None)
        if not qrecs:
            continue
        qrec = qrecs[0]
        if not hasattr(qrec, "scale") or qrec.scale is None:
            continue
        gap9_scale = float(np.atleast_1d(qrec.scale)[0])
        gap9_zp = int(np.atleast_1d(qrec.zero_point)[0]) if hasattr(qrec, "zero_point") and qrec.zero_point is not None else 0

        qdq_entry = next(qdq_iter, None)
        if qdq_entry is None:
            qdq_scale_str = "   (no ref)"
            qdq_zp_str = "  —"
            note = ""
        else:
            qdq_scale = qdq_entry["scale"]
            qdq_zp = qdq_entry["zp"]
            ratio = gap9_scale / (qdq_scale + 1e-15)
            qdq_scale_str = f"{qdq_scale:>12.6e}"
            qdq_zp_str = f"{qdq_zp:>6d}"
            if abs(ratio - 1.0) < 0.05:
                note = "✓ close"
            elif abs(ratio - 1.0) < 0.20:
                note = "~ within 20%"
            else:
                note = f"✗ ratio={ratio:.2f}"
        name = node.name[:38]
        print(f"  {name:<38}  {gap9_scale:>12.6e}  {qdq_scale_str}  "
              f"{gap9_zp:>7d}  {qdq_zp_str}  {note}")
        if type(node).__name__ == "InputNode":
            gap9_io["input_scale"] = gap9_scale
            gap9_io["input_zp"] = gap9_zp
            if qdq_entry:
                gap9_io["qdq_input_scale"] = qdq_entry["scale"]
                gap9_io["qdq_input_zp"] = qdq_entry["zp"]
        if type(node).__name__ == "OutputNode":
            gap9_io["output_scale"] = gap9_scale
            gap9_io["output_zp"] = gap9_zp
    return gap9_io


# -----------------------------------------------------------------------------
# Step 6: Generate project
# -----------------------------------------------------------------------------

def generate_project(G: NNGraph, out_dir: str, model_name: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    if model_name:
        G.name = model_name
    print(f"\n[3/3] Generating project → {out_dir}/")
    try:
        G.gen_at_model(directory=out_dir, model_name=model_name)
        print("  gen_at_model succeeded.")
    except Exception as e:
        print(f"  gen_at_model failed: {e}, trying fallback...")
        inp = np.zeros((1, 3, 224, 224), dtype=np.int8)
        G.gen_project(input_tensors=[inp], directory=out_dir, platform="gvsoc", cmake=True)
        print("  gen_project succeeded.")


# -----------------------------------------------------------------------------
# Step 7: Write input preparation script
# -----------------------------------------------------------------------------

def write_input_prep_script(out_dir: str, gap9_io: dict, model_name: str) -> None:
    gap9_in_scale = gap9_io.get("input_scale", 0.02)
    gap9_in_zp = gap9_io.get("input_zp", 0)
    qdq_in_scale = gap9_io.get("qdq_input_scale", 0.0184534)
    qdq_in_zp = gap9_io.get("qdq_input_zp", -13)

    code = f'''#!/usr/bin/env python3
"""
Prepare input for GAP9 model '{model_name}'
Generated from QDQ ONNX with symmetric NNTool quantization.
"""
import numpy as np
import sys
from PIL import Image

GAP9_SCALE = {gap9_in_scale:.10e}
GAP9_ZP    = {gap9_in_zp}
ONNX_SCALE = {qdq_in_scale:.10e}
ONNX_ZP    = {qdq_in_zp}

def quantize_for_gap9(img_float32):
    if img_float32.max() > 2.0:
        img_float32 = img_float32 / 255.0
    q = np.round(img_float32 / GAP9_SCALE) + GAP9_ZP
    q = np.clip(q, -128, 127).astype(np.int8)
    return q

def main():
    if len(sys.argv) != 2:
        print("Usage: prepare_input.py <image.jpg>")
        sys.exit(1)
    img = Image.open(sys.argv[1]).convert("RGB").resize((224,224))
    arr = np.array(img, dtype=np.float32).transpose(2,0,1)[np.newaxis] / 255.0
    q = quantize_for_gap9(arr)
    q.flatten().tofile("Input_1.bin")
    print(f"Saved Input_1.bin, shape={{q.shape}}, min={{q.min()}}, max={{q.max()}}")

if __name__ == "__main__":
    main()
'''
    out_path = os.path.join(out_dir, "prepare_input.py")
    with open(out_path, "w") as f:
        f.write(code)
    print(f"\nInput preparation script written: {out_path}")


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--outdir", default="gen")
    parser.add_argument("--name", default="network")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not os.path.isfile(args.model):
        sys.exit(f"Model not found: {args.model}")

    qdq_list = extract_qdq_activations(args.model)
    if len(qdq_list) < 2:
        sys.exit("Need at least input and one activation QDQ node.")

    G = load_and_fuse(args.model, args.verbose)

    stats = build_stats_from_qdq(G, qdq_list)
    if not stats:
        sys.exit("No stats built – check QDQ mapping.")

    quantize_graph(G, stats, args.verbose)

    gap9_io = verify_scales(G, qdq_list)

    generate_project(G, args.outdir, args.name)

    write_input_prep_script(args.outdir, gap9_io, args.name)

    print("\n✅ Deployment complete.")


if __name__ == "__main__":
    main()
