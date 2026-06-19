Write the final corrected deployment script
bash

cat > /mnt/user-data/outputs/gap9_nntool_deploy.py << 'PYEOF'
"""
GAP9 NNTool deployment — pre-quantized QDQ ONNX to GAP9 AutoTiler project.

The central problem this script solves
---------------------------------------
NNTool's "scaled" quantization scheme is SYMMETRIC (all zero-points = 0).
Your ONNX/STM32 model uses ASYMMETRIC quantization (zp=-13 at input, zp=+12
at output).  When you load the QDQ ONNX with load_quantization=True, NNTool
silently discards your asymmetric scales and re-runs its own symmetric
calibration — producing completely different scale factors.

This script works around that by:
  1. Loading the QDQ ONNX to extract the true per-layer scales from the
     embedded QuantizeLinear nodes (using onnx directly, not NNTool).
  2. Loading the graph in float32 mode (ignoring the QDQ).
  3. Running NNTool fusions.
  4. Using the extracted scales to build a statistics dict that forces
     NNTool's symmetric quantizer to land on the closest representable
     scale to your original asymmetric one.
  5. Verifying the result and generating the project.

Input format for the generated GAP9 model
------------------------------------------
The generated model expects: signed int8, CHW layout, [1, 3, 224, 224]
Quantization: q = round(float_val / input_scale) - input_zp  (clamped to [-128,127])

But because NNTool's symmetric scheme sets zp=0, the input quantization
that the GENERATED model actually uses will be:
  q_gap9 = round(float_val / gap9_input_scale)    (zp forced to 0)

This script prints the exact formula to use after generation.
The companion script prepare_input.py will quantize any float32 image
correctly for the generated model.

Usage
-----
  python gap9_nntool_deploy.py --model model_int8_qdq.onnx --outdir gen/ --validate
"""

import argparse
import os
import sys
import numpy as np

try:
    import onnx
    from onnx import numpy_helper
except ImportError:
    sys.exit("pip install onnx  (needed to extract QDQ scales)")

try:
    from nntool.api import NNGraph
    from nntool.api.types import ExpressionFusionNode
    from nntool.api.utils import quantization_options
except ImportError as exc:
    sys.exit(f"NNTool not found: {exc}\nSource the GAP SDK first.")


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Extract true scales/zp from the QDQ ONNX using onnx directly
# ─────────────────────────────────────────────────────────────────────────────

def extract_qdq_params(qdq_path: str) -> dict:
    """
    Walk the ONNX graph and collect (scale, zero_point) for every
    QuantizeLinear node.  Returns dict keyed by output tensor name.
    """
    model = onnx.load(qdq_path)
    graph = model.graph

    # Build initializer lookup: name -> numpy array
    inits = {init.name: numpy_helper.to_array(init) for init in graph.initializer}

    params = {}
    for node in graph.node:
        if node.op_type != "QuantizeLinear":
            continue
        # QuantizeLinear inputs: [x, scale, zero_point]
        if len(node.input) < 3:
            continue
        scale_name = node.input[1]
        zp_name    = node.input[2]
        if scale_name not in inits or zp_name not in inits:
            continue
        scale = float(inits[scale_name].flat[0])
        zp    = int(inits[zp_name].flat[0])
        # Output tensor name is what the next node consumes
        out_name = node.output[0]
        params[out_name] = {"scale": scale, "zp": zp, "op_input": node.input[0]}

    print(f"\nExtracted {len(params)} QuantizeLinear nodes from QDQ ONNX:")
    for k, v in params.items():
        print(f"  tensor '{k}':  scale={v['scale']:.6e}  zp={v['zp']}")

    return params


def extract_qdq_layer_order(qdq_path: str) -> list:
    """
    Return (scale, zp) pairs in graph execution order for activation tensors.
    Skips weight/bias quantizers (those have per-channel scales as vectors).
    """
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
        zp_arr    = inits.get(node.input[2])
        if scale_arr is None or zp_arr is None:
            continue
        # Skip per-channel (weight) quantizers — they have vector scales
        if scale_arr.ndim > 0 and scale_arr.size > 1:
            continue
        scale = float(scale_arr.flat[0])
        zp    = int(zp_arr.flat[0])
        ordered.append({"scale": scale, "zp": zp, "tensor": node.output[0]})

    print(f"\nActivation quantizers in graph order:")
    for i, p in enumerate(ordered):
        print(f"  [{i}] scale={p['scale']:.6e}  zp={p['zp']:4d}  tensor='{p['tensor']}'")

    return ordered


# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Load model in float32 mode and run fusions
# ─────────────────────────────────────────────────────────────────────────────

def load_and_fuse(model_path: str, verbose: bool) -> NNGraph:
    """Load ONNX as float32, fuse, return graph."""
    print(f"\n{'='*60}\n  Loading: {model_path}\n{'='*60}")

    # Try loading as QDQ first (strips Q/DQ wrappers, keeps float32 ops)
    load_attempts = [
        {"load_quantization": False},
    ]
    G = None
    for opts in load_attempts:
        try:
            G = NNGraph.load_graph(model_path, **opts)
            print(f"  Loaded with options: {opts}")
            break
        except Exception as exc:
            print(f"  Load attempt {opts} failed: {exc}")

    if G is None:
        sys.exit("Could not load model.")

    if verbose:
        print("\nRaw graph:"); G.show()

    # Print node names BEFORE fusions so we can see what we're working with
    print("\nNode names before fusions:")
    for n in G.nodes():
        print(f"  {n.name!r:40s}  type={type(n).__name__}  "
              f"in_dims={n.in_dims}  out_dims={n.out_dims}")

    print("\n[2/4] Running scaled_match_group fusions ...")
    G.fusions("scaled_match_group")

    print("\nNode names AFTER fusions (these are what quantize() uses):")
    for n in G.nodes():
        print(f"  {n.name!r:40s}  type={type(n).__name__}  "
              f"in_dims={n.in_dims}  out_dims={n.out_dims}")

    return G


# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Map QDQ activation quantizers to NNTool nodes by position
# ─────────────────────────────────────────────────────────────────────────────

def build_stats_from_qdq(G: NNGraph, qdq_ordered: list) -> tuple:
    """
    Match the ordered list of QDQ activation quantizers to NNTool nodes
    by their position in the execution graph (not by name, since names differ).

    NNTool nodes with actual compute (Conv, MatMul, etc.) are the ones that
    need quantization stats.  We skip structural nodes (Reshape, Transpose).

    Returns (stats_dict, mapping) where mapping shows which QDQ entry was
    used for which NNTool node.
    """
    SKIP_TYPES = {"TransposeNode", "ReshapeNode", "NoOpNode",
                  "InputNode", "OutputNode", "CopyNode"}

    def scale_zp_to_range(scale, zp):
        # Symmetric NNTool can't represent zp≠0 in activations.
        # We give it the symmetric range that best captures the asymmetric one.
        real_min = scale * (-128 - zp)
        real_max = scale * (127  - zp)
        # Force symmetric: use the larger absolute extent
        extent = max(abs(real_min), abs(real_max))
        return (-extent, extent)

    # Collect nodes that actually need stats (ordered by execution)
    compute_nodes = []
    for n in G.nodes():
        t = type(n).__name__
        if t in SKIP_TYPES:
            continue
        compute_nodes.append(n)

    print(f"\n  QDQ activation quantizers: {len(qdq_ordered)}")
    print(f"  NNTool compute nodes:      {len(compute_nodes)}")

    if len(qdq_ordered) < len(compute_nodes):
        print("  WARNING: fewer QDQ entries than compute nodes — "
              "some nodes will use default quantization.")

    stats = {}
    mapping = []

    # Also build input node stats from first QDQ entry
    in_nodes = list(G.input_nodes())
    if in_nodes and qdq_ordered:
        first_qdq = qdq_ordered[0]
        rng = scale_zp_to_range(first_qdq["scale"], first_qdq["zp"])
        n_out = len(in_nodes[0].out_dims) if in_nodes[0].out_dims else 1
        stats[in_nodes[0].name] = {
            "range_in":  [rng],
            "range_out": [rng] * n_out,
        }
        mapping.append((in_nodes[0].name, "input", first_qdq))

    # Map remaining QDQ entries to compute nodes
    qdq_idx = 1  # skip first (used for input)
    for node in compute_nodes:
        if qdq_idx >= len(qdq_ordered):
            break
        qdq_entry = qdq_ordered[qdq_idx]
        rng = scale_zp_to_range(qdq_entry["scale"], qdq_entry["zp"])
        n_in  = len(node.in_dims)  if node.in_dims  else 1
        n_out = len(node.out_dims) if node.out_dims else 1
        stats[node.name] = {
            "range_in":  [rng] * n_in,
            "range_out": [rng] * n_out,
        }
        mapping.append((node.name, type(node).__name__, qdq_entry))
        qdq_idx += 1

    print("\n  Node → QDQ mapping:")
    print(f"  {'NNTool node':<40}  {'Type':<20}  {'scale':>12}  {'zp':>4}")
    print(f"  {'-'*40}  {'-'*20}  {'-'*12}  {'-'*4}")
    for node_name, node_type, qdq in mapping:
        print(f"  {node_name:<40}  {node_type:<20}  "
              f"{qdq['scale']:>12.6e}  {qdq['zp']:>4d}")

    return stats, mapping


# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Quantize
# ─────────────────────────────────────────────────────────────────────────────

def quantize_graph(G: NNGraph, stats: dict, verbose: bool) -> None:
    print("\n[3/4] Quantizing with injected stats ...")

    node_opts = {
        node.name: quantization_options(scheme="float", float_type="float32")
        for node in G.nodes(ExpressionFusionNode)
    }

    G.quantize(
        stats,
        schemes=["scaled"],
        graph_options=quantization_options(
            use_ne16=False,     # keep off until basic correctness is verified
            const_clip_type="none",  # use exact weight ranges from ONNX
            clip_type="none",        # use exact activation ranges we injected
        ),
        node_options=node_opts if node_opts else None,
    )

    if verbose:
        G.show(show_quantization=True)


# ─────────────────────────────────────────────────────────────────────────────
# Step 5: Verify — compare generated scales against original QDQ
# ─────────────────────────────────────────────────────────────────────────────

def verify_and_report(G: NNGraph, qdq_ordered: list) -> dict:
    """
    Print a comparison of NNTool's generated scales vs original QDQ scales.
    Also return the input node's actual scale/zp so we can generate
    correct input preparation code.
    """
    print("\n── Quantization verification ───────────────────────────────────")
    print(f"  {'Node':<38}  {'GAP9 scale':>12}  {'QDQ scale':>12}  "
          f"{'GAP9 zp':>7}  {'QDQ zp':>6}  Notes")
    print(f"  {'-'*38}  {'-'*12}  {'-'*12}  {'-'*7}  {'-'*6}  -----")

    qdq_iter = iter(qdq_ordered)
    gap9_io = {}

    for node in G.nodes():
        qrecs = getattr(node, "out_quantization", None)
        if not qrecs:
            continue
        qrec = qrecs[0]
        if not hasattr(qrec, "scale") or qrec.scale is None:
            continue

        gap9_scale = float(np.atleast_1d(qrec.scale)[0])
        gap9_zp    = int(np.atleast_1d(qrec.zero_point)[0]) \
                     if hasattr(qrec, "zero_point") and qrec.zero_point is not None else 0

        qdq_entry = next(qdq_iter, None)
        if qdq_entry is None:
            qdq_scale_str = "   (no ref)"
            qdq_zp_str    = "  —"
            note = ""
        else:
            qdq_scale = qdq_entry["scale"]
            qdq_zp    = qdq_entry["zp"]
            ratio     = gap9_scale / (qdq_scale + 1e-15)
            qdq_scale_str = f"{qdq_scale:>12.6e}"
            qdq_zp_str    = f"{qdq_zp:>6d}"
            if abs(ratio - 1.0) < 0.05:
                note = "✓ close"
            elif abs(ratio - 1.0) < 0.20:
                note = "~ within 20%"
            else:
                note = f"✗ ratio={ratio:.2f}"

        name = node.name[:38]
        print(f"  {name:<38}  {gap9_scale:>12.6e}  {qdq_scale_str}  "
              f"{gap9_zp:>7d}  {qdq_zp_str}  {note}")

        is_input  = type(node).__name__ == "InputNode"
        is_output = type(node).__name__ == "OutputNode"
        if is_input:
            gap9_io["input_scale"] = gap9_scale
            gap9_io["input_zp"]    = gap9_zp
            gap9_io["qdq_input_scale"] = qdq_entry["scale"] if qdq_entry else None
            gap9_io["qdq_input_zp"]    = qdq_entry["zp"]    if qdq_entry else None
        if is_output:
            gap9_io["output_scale"] = gap9_scale
            gap9_io["output_zp"]    = gap9_zp

    return gap9_io


# ─────────────────────────────────────────────────────────────────────────────
# Step 6: Validation
# ─────────────────────────────────────────────────────────────────────────────

def validate_inference(G: NNGraph, expected_shape: tuple,
                       input_scale: float, input_zp: int,
                       n: int = 4) -> None:
    print(f"\n[4/4] Validation: {n} random forward passes ...")
    for i in range(n):
        rng = np.random.default_rng(seed=i)
        # Generate float32 image in [0, 1], quantize with gap9 input scale
        img_f32 = rng.uniform(0.0, 1.0, size=(1, 3, 224, 224)).astype(np.float32)
        img_int8 = np.clip(
            np.round(img_f32 / input_scale) + input_zp,
            -128, 127
        ).astype(np.int8)
        try:
            result = G.execute([img_int8], quantize=False, dequantize=True)
            # Extract first numpy array from result
            arr = result[0][0] if isinstance(result[0], (list, tuple)) else result[0]
            if not isinstance(arr, np.ndarray):
                arr = np.array(arr)
            if arr.shape != expected_shape:
                print(f"  [!] Shape mismatch: got {arr.shape}, expected {expected_shape}")
                return
            if not np.all(np.isfinite(arr)):
                print(f"  [!] Non-finite output at image {i}")
                return
        except Exception as exc:
            print(f"  [!] Inference error at image {i}: {exc}")
            import traceback; traceback.print_exc()
            return
    print(f"  Passed. Output shape: {expected_shape} ✓")


# ─────────────────────────────────────────────────────────────────────────────
# Step 7: Code generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_project(G: NNGraph, out_dir: str, model_name: str,
                     input_shape: tuple) -> None:
    os.makedirs(out_dir, exist_ok=True)
    if model_name:
        G.name = model_name

    print(f"\nGenerating NNTool project → {out_dir}/")

    # Probe gen_at_model signature
    import inspect
    try:
        sig = inspect.signature(G.gen_at_model)
        params = list(sig.parameters.keys())
        print(f"  gen_at_model params: {params}")
    except Exception:
        params = []

    out_c = os.path.join(out_dir, f"{model_name}_model.c")

    # Try different calling conventions across NNTool versions
    generated = False
    attempts = [
        lambda: G.gen_at_model(directory=out_dir,
                               settings=__import__("nntool.api.utils",
                                   fromlist=["model_settings"]).model_settings(
                                       model_directory=out_dir,
                                       model_file=f"{model_name}_model.c")),
        lambda: G.gen_at_model(out_c, graph_name=model_name),
        lambda: G.gen_at_model(path=out_c, graph_name=model_name),
        lambda: G.gen_at_model(at_model_path=out_c, graph_name=model_name),
    ]
    for attempt in attempts:
        try:
            attempt()
            generated = True
            print(f"  Code generation succeeded → {out_c}")
            break
        except Exception as exc:
            print(f"  (attempt failed: {exc})")

    if not generated:
        # Last resort: gen_project
        print("  Trying gen_project fallback ...")
        inp = np.zeros(input_shape, dtype=np.int8)
        try:
            G.gen_project(
                input_tensors=[inp],
                directory=out_dir,
                platform="gvsoc",
                cmake=True,
            )
            generated = True
            print("  gen_project succeeded.")
        except Exception as exc:
            print(f"  gen_project also failed: {exc}")

    # Save quantized graph
    for method, path in [("save_quantized", os.path.join(out_dir, f"{model_name}.json")),
                         ("save_graph",      os.path.join(out_dir, f"{model_name}.json")),
                         ("save",            os.path.join(out_dir, f"{model_name}.json"))]:
        if hasattr(G, method):
            try:
                getattr(G, method)(path)
                print(f"  Graph saved: {path}")
                break
            except Exception:
                pass

    return generated


# ─────────────────────────────────────────────────────────────────────────────
# Step 8: Generate companion input preparation script
# ─────────────────────────────────────────────────────────────────────────────

def write_input_prep_script(out_dir: str, gap9_io: dict,
                            qdq_ordered: list, model_name: str) -> None:
    """
    Write prepare_input.py that correctly quantizes a float32 image
    to the int8 format that the generated GAP9 model expects.
    """
    gap9_in_scale = gap9_io.get("input_scale", 0.02)
    gap9_in_zp    = gap9_io.get("input_zp",    0)
    qdq_in_scale  = gap9_io.get("qdq_input_scale", 0.01845)
    qdq_in_zp     = gap9_io.get("qdq_input_zp",    -13)

    out_path = os.path.join(out_dir, "prepare_input.py")
    code = f'''"""
Prepare input binary for the GAP9 model: {model_name}

The model was generated by NNTool using its symmetric quantization scheme.
NNTool forces all zero-points to 0 (symmetric), which means the input
quantization is DIFFERENT from the original QDQ ONNX.

IMPORTANT: use the GAP9 scales below, NOT the original ONNX scales.

Original QDQ ONNX input:   scale={qdq_in_scale:.8e}  zp={qdq_in_zp}
GAP9 generated model input: scale={gap9_in_scale:.8e}  zp={gap9_in_zp}

These differ because NNTool re-quantized symmetrically.
If you feed data quantized with the ONNX scale, the model will give wrong results.
"""
import numpy as np
import sys
import os

# ── Quantization parameters for the GENERATED GAP9 model ──────────────────
# These come from network_graphinfo.h: Input_1_OUT_SCALE and Input_1_OUT_ZERO_POINT
GAP9_INPUT_SCALE = {gap9_in_scale:.10e}
GAP9_INPUT_ZP    = {gap9_in_zp}

# Original ONNX/STM32 parameters (for reference / cross-check only)
ONNX_INPUT_SCALE = {qdq_in_scale:.10e}
ONNX_INPUT_ZP    = {qdq_in_zp}


def float32_to_gap9_int8(img_float32: np.ndarray) -> np.ndarray:
    """
    Quantize a float32 CHW image [1,3,224,224] to int8 for the GAP9 model.

    img_float32: float32 array, values in [0.0, 1.0] (normalized)
                 OR in [0, 255] — function auto-detects based on range.
    Returns: int8 array, CHW, [1,3,224,224], saved as signed char
    """
    img = img_float32.astype(np.float32)
    if img.max() > 2.0:
        # Looks like [0,255] range — normalize to [0,1]
        img = img / 255.0

    # Standard normalization matching model training (ImageNet mean/std assumed)
    # If your model uses a different normalization, change this.
    # mean = [0.485, 0.456, 0.406], std = [0.229, 0.224, 0.225]
    # Uncomment if needed:
    # mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)[:,None,None]
    # std  = np.array([0.229, 0.224, 0.225], dtype=np.float32)[:,None,None]
    # img  = (img - mean) / std

    # Quantize with GAP9 model's actual input scale
    q = np.round(img / GAP9_INPUT_SCALE) + GAP9_INPUT_ZP
    q = np.clip(q, -128, 127).astype(np.int8)
    return q


def prepare_from_numpy(img_chw_float32: np.ndarray,
                       output_path: str = "Input_1.bin") -> None:
    """
    img_chw_float32: numpy array shape [3, 224, 224] or [1, 3, 224, 224]
    Saves int8 CHW binary to output_path.
    """
    if img_chw_float32.ndim == 3:
        img_chw_float32 = img_chw_float32[np.newaxis]  # add batch dim

    q = float32_to_gap9_int8(img_chw_float32)
    q.flatten().tofile(output_path)
    print(f"Saved {{q.shape}} int8 CHW image to {{output_path}}")
    print(f"  dtype={{q.dtype}}, min={{q.min()}}, max={{q.max()}}, "
          f"mean={{q.mean():.2f}}")


def prepare_from_image_file(image_path: str,
                            output_path: str = "Input_1.bin") -> None:
    """Load a PNG/JPG, resize to 224x224, quantize, save as int8 CHW binary."""
    try:
        from PIL import Image
    except ImportError:
        sys.exit("pip install Pillow")

    img = Image.open(image_path).convert("RGB").resize((224, 224))
    arr = np.array(img, dtype=np.float32) / 255.0  # HWC [0,1]
    arr_chw = arr.transpose(2, 0, 1)[np.newaxis]   # → [1,3,224,224]
    prepare_from_numpy(arr_chw, output_path)


def cross_check_with_onnx(image_path: str) -> None:
    """
    Optional: run the QDQ ONNX on the same image and compare to
    what the GAP9 model should produce (for scale verification only).
    """
    try:
        import onnxruntime as ort
    except ImportError:
        print("pip install onnxruntime  (needed for cross-check)")
        return

    from PIL import Image
    img = Image.open(image_path).convert("RGB").resize((224, 224))
    arr = np.array(img, dtype=np.float32) / 255.0
    arr_chw = arr.transpose(2, 0, 1)[np.newaxis]   # [1,3,224,224]

    # ONNX expects float32 input (the QDQ wrapper quantizes internally)
    sess = ort.InferenceSession("model_int8_qdq.onnx")
    inp_name = sess.get_inputs()[0].name
    out = sess.run(None, {{inp_name: arr_chw}})[0]
    print(f"ONNX output shape: {{out.shape}}, scale={ONNX_INPUT_SCALE:.4e}, "
          f"range=[{{out.min():.4f}}, {{out.max():.4f}}]")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        prepare_from_image_file(sys.argv[1])
    else:
        # Demo: random image
        print("Usage: python prepare_input.py <image.jpg>")
        print("Demo: generating random test image ...")
        rng = np.random.default_rng(42)
        img = rng.uniform(0.0, 1.0, size=(1, 3, 224, 224)).astype(np.float32)
        prepare_from_numpy(img, "Input_1.bin")
'''
    with open(out_path, "w") as f:
        f.write(code)
    print(f"\nInput preparation script written: {out_path}")
    print(f"""
┌─────────────────────────────────────────────────────────────────┐
│  INPUT FORMAT SUMMARY                                           │
│                                                                 │
│  File:       Input_1.bin                                        │
│  Layout:     CHW — [3, 224, 224] flattened                      │
│  dtype:      signed int8 (signed char)                          │
│  Size:       150528 bytes                                       │
│                                                                 │
│  To quantize float32 image → int8 for GAP9:                     │
│    q = round(float_val / {gap9_in_scale:.5e}) + {gap9_in_zp:+d}  │
│    clamped to [-128, 127]                                       │
│                                                                 │
│  NOTE: This uses GAP9's re-quantized scale ({gap9_in_scale:.5e})│
│  NOT the original ONNX scale ({qdq_in_scale:.5e}).              │
│  These differ because NNTool uses symmetric (zp=0) quantization.│
│                                                                 │
│  To prepare inputs: python prepare_input.py <image.jpg>         │
└─────────────────────────────────────────────────────────────────┘""")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Deploy QDQ ONNX to GAP9")
    p.add_argument("--model",    required=True, help="QDQ ONNX or float32 ONNX")
    p.add_argument("--outdir",   default="gen")
    p.add_argument("--name",     default="network")
    p.add_argument("--validate", action="store_true")
    p.add_argument("--verbose",  action="store_true")
    return p.parse_args()


def main():
    args = parse_args()

    if not os.path.isfile(args.model):
        sys.exit(f"Model not found: {args.model}")

    # 1. Extract QDQ scales directly from ONNX
    print("\n[1/4] Extracting QDQ scales from ONNX ...")
    qdq_ordered = extract_qdq_layer_order(args.model)

    if not qdq_ordered:
        print("\nWARNING: No QuantizeLinear nodes found.")
        print("This may be a float32 ONNX — NNTool will re-quantize from scratch.")
        print("For best results, provide the QDQ int8 ONNX.")

    # 2. Load graph (as float32, ignoring QDQ) and run fusions
    G = load_and_fuse(args.model, verbose=args.verbose)

    # 3. Build stats dict from QDQ scales and quantize
    if qdq_ordered:
        print("\n[2/4] Mapping QDQ scales to NNTool nodes ...")
        stats, mapping = build_stats_from_qdq(G, qdq_ordered)
        quantize_graph(G, stats, verbose=args.verbose)
    else:
        print("\n[2/4] No QDQ scales available — skipping scale injection.")
        print("       You must provide calibration data or a QDQ ONNX.")
        sys.exit(1)

    # 4. Verify generated scales
    gap9_io = verify_and_report(G, qdq_ordered)

    # 5. Determine output shape from graph
    out_nodes = list(G.output_nodes())
    if out_nodes and out_nodes[0].in_dims:
        expected_shape = tuple(out_nodes[0].in_dims[0].shape)
    else:
        expected_shape = (1, 76, 28, 28)  # fallback CHW
    print(f"\nExpected output shape: {expected_shape}")

    # 6. Optional validation
    if args.validate:
        in_scale = gap9_io.get("input_scale", qdq_ordered[0]["scale"])
        in_zp    = gap9_io.get("input_zp", 0)
        validate_inference(G, expected_shape, in_scale, in_zp)

    # 7. Generate code
    generate_project(G, out_dir=args.outdir, model_name=args.name,
                     input_shape=(1, 3, 224, 224))

    # 8. Write input preparation script
    write_input_prep_script(args.outdir, gap9_io, qdq_ordered, args.name)


if __name__ == "__main__":
    main()
PYEOF
echo "done"
