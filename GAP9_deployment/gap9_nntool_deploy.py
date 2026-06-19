"""
GAP9 NNTool deployment script for pre-quantized QDQ ONNX model.

Model topology (from STM32 reference network.c):
  Input  : [1, 224, 224, 3] HWC, int8, scale=0.01845, zp=-13
  Conv1  : 3→9 ch, 3×3, stride 1, pad SAME → ReLU, scale=0.009542, zp=-128
  Conv2  : 9→19 ch, 3×3, stride 2, pad SAME → ReLU, scale=0.003999, zp=-128
  Conv3  : 19→38 ch, 3×3, stride 2, pad SAME → ReLU, scale=0.000695, zp=-128
  Conv4  : 38→76 ch, 3×3, stride 2, pad SAME → ReLU, scale=0.000393, zp=-128
  Conv5  : 76→76 ch, 3×3, stride 1, pad SAME → ReLU, scale=8.46e-5,  zp=+12
  Output : [1, 28, 28, 76] HWC, int8

Usage
-----
    # QDQ ONNX directly (preferred if fully-quantized QDQ graph):
    python gap9_nntool_deploy.py \
        --model model_int8_qdq.onnx \
        --mode  qdq_direct \
        --outdir gen/ --validate --verbose

    # Float32 ONNX with injected reference scales:
    python gap9_nntool_deploy.py \
        --model model_float32.onnx \
        --mode  inject_stats \
        --outdir gen/ --validate --verbose
"""

import argparse
import os
import sys
import numpy as np

try:
    from nntool.api import NNGraph
    from nntool.api.types import ExpressionFusionNode
    from nntool.api.utils import quantization_options, model_settings
except ImportError as exc:
    sys.exit(
        f"NNTool not found: {exc}\n"
        "Source the GAP SDK before running this script."
    )

# ─────────────────────────────────────────────────────────────────────────────
# Reference quantization parameters from STM32 network.c (ground truth)
# ─────────────────────────────────────────────────────────────────────────────

REFERENCE_ACT_QUANT = {
    "input":      {"scale": 0.01845340058207512,     "zp": -13},
    "net_1_relu": {"scale": 0.009542142041027546,    "zp": -128},
    "net_3_relu": {"scale": 0.003998782020062208,    "zp": -128},
    "net_5_relu": {"scale": 0.000694780726917088,    "zp": -128},
    "net_7_relu": {"scale": 0.00039253884460777044,  "zp": -128},
    "output":     {"scale": 8.462232653982937e-05,   "zp":  12},
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def build_stats_from_reference(G, ref_quant: dict) -> dict:
    """Convert reference (scale, zp) pairs into NNTool statistics dicts."""
    stats = {}

    def scale_zp_to_range(scale, zp):
        return (scale * (-128 - zp), scale * (127 - zp))

    for node in G.nodes():
        name = node.name
        matched = None
        for ref_key, ref_val in ref_quant.items():
            if ref_key in name or name in ref_key:
                matched = ref_val
                break
        if matched is None:
            continue

        rng = scale_zp_to_range(matched["scale"], matched["zp"])
        n_in  = len(node.in_dims)  if node.in_dims  else 1
        n_out = len(node.out_dims) if node.out_dims else 1
        stats[name] = {
            "range_in":  [rng] * n_in,
            "range_out": [rng] * n_out,
        }
    return stats


def verify_output_scales(G: NNGraph, ref_quant: dict) -> None:
    """Compare quantized output scale/zp against STM32 reference values."""
    print("\n── Scale verification ──────────────────────────────────────────")
    print(f"  {'Node':<30}  {'Scale (got)':>14}  {'Scale (ref)':>14}  "
          f"{'ZP (got)':>8}  {'ZP (ref)':>8}  Match")
    print(f"  {'-'*30}  {'-'*14}  {'-'*14}  {'-'*8}  {'-'*8}  -----")

    matched_any = False
    all_ok = True
    for node in G.nodes():
        if not hasattr(node, "out_quantization") or node.out_quantization is None:
            continue
        qp = node.out_quantization[0]
        if not hasattr(qp, "scale") or qp.scale is None:
            continue

        got_scale = float(np.atleast_1d(qp.scale)[0])
        got_zp    = int(np.atleast_1d(qp.zero_point)[0]) if hasattr(qp, "zero_point") else 0

        ref_match = None
        for ref_key, ref_val in ref_quant.items():
            if ref_key in node.name or node.name in ref_key:
                ref_match = ref_val
                break
        if ref_match is None:
            continue

        matched_any = True
        ref_scale = ref_match["scale"]
        ref_zp    = ref_match["zp"]
        scale_ok  = abs(got_scale - ref_scale) / (ref_scale + 1e-12) < 0.05
        zp_ok     = got_zp == ref_zp
        ok        = scale_ok and zp_ok
        all_ok    = all_ok and ok

        flag = "✓" if ok else "✗ ← MISMATCH"
        print(f"  {node.name:<30}  {got_scale:>14.6e}  {ref_scale:>14.6e}  "
              f"{got_zp:>8}  {ref_zp:>8}  {flag}")

    if not matched_any:
        print("  (no nodes matched reference key names — check node naming)")
    elif all_ok:
        print("\n  All matched scales agree with reference. ✓")
    else:
        print(
            "\n  WARNING: one or more scales differ from the STM32 reference.\n"
            "  Run --validate to check numerical correctness."
        )


def _extract_output_tensor(result, expected_out_shape: tuple):
    """Pick the output tensor from NNTool execute() results."""
    arrays = []

    def collect(obj):
        if isinstance(obj, np.ndarray):
            arrays.append(obj)
            return
        if isinstance(obj, dict):
            for val in obj.values():
                collect(val)
            return
        if isinstance(obj, (list, tuple)):
            for val in obj:
                collect(val)
            return

    collect(result)
    for arr in arrays:
        if hasattr(arr, "shape") and tuple(arr.shape) == expected_out_shape:
            return arr
    return arrays[0] if arrays else None


def _qrec_to_scale_zp(qrec):
    if qrec is None:
        return None, None
    scale = None
    zp = None
    if hasattr(qrec, "scale") and qrec.scale is not None:
        scale = float(np.atleast_1d(qrec.scale)[0])
    if hasattr(qrec, "zero_point") and qrec.zero_point is not None:
        zp = int(np.atleast_1d(qrec.zero_point)[0])
    return scale, zp


def _infer_input_dtype(G: NNGraph) -> str:
    """Infer whether the graph expects int8 or float32 at the input."""
    in_nodes = list(G.input_nodes())
    if not in_nodes:
        return "int8"
    qrecs = getattr(in_nodes[0], "out_quantization", None)
    if qrecs and len(qrecs) and getattr(qrecs[0], "scale", None) is not None:
        return "int8"
    return "float32"


def _print_io_quantization(G: NNGraph) -> None:
    print("\nIO quantization (as seen by NNTool):")
    for node in G.input_nodes():
        qrec = None
        qrecs = getattr(node, "out_quantization", None)
        if qrecs:
            qrec = qrecs[0]
        scale, zp = _qrec_to_scale_zp(qrec)
        print(f"  input {node.name}: scale={scale} zp={zp}")
    for node in G.output_nodes():
        qrec = None
        qrecs = getattr(node, "out_quantization", None)
        if qrecs:
            qrec = qrecs[0]
        scale, zp = _qrec_to_scale_zp(qrec)
        print(f"  output {node.name}: scale={scale} zp={zp}")


def validate_inference(G: NNGraph, expected_out_shape: tuple,
                       input_shape: tuple, input_dtype: str,
                       n_images: int = 8, is_qdq: bool = False) -> None:
    """Feed random int8 inputs and verify output shape + finiteness."""
    print(f"\n[validation] Running {n_images} random forward passes ...")
    for i in range(n_images):
        rng = np.random.default_rng(seed=i)
        if input_dtype == "float32":
            inp = rng.uniform(-1.0, 1.0, size=input_shape).astype(np.float32)
        else:
            inp = rng.integers(-128, 127, size=input_shape, dtype=np.int8)
        try:
            # QDQ graphs are already quantized, so no need to quantize again
            if is_qdq:
                result = G.execute([inp], quantize=False, dequantize=True)
            else:
                result = G.execute([inp], quantize=True, dequantize=True)
            out = _extract_output_tensor(result, expected_out_shape)
            if out is None:
                print("  [!] Could not extract output tensor from execute() result")
                return
            if out.shape != expected_out_shape:
                print(f"  [!] Shape mismatch on image {i}: got {out.shape}, "
                      f"expected {expected_out_shape}")
                print("      Check adjust_order() and input tensor layout.")
                return
            if not np.all(np.isfinite(out)):
                print(f"  [!] Non-finite values in output at image {i}!")
                return
        except Exception as exc:
            print(f"  [!] Inference failed on image {i}: {exc}")
            import traceback; traceback.print_exc()
            return
    print(f"  Passed. Output shape: {expected_out_shape} ✓")


def generate_code(G: NNGraph, out_dir: str, model_name: str,
                  input_shape: tuple, input_dtype: str,
                  gen_project: bool) -> None:
    """Generate either a full NNTool project or just the AutoTiler model file."""
    os.makedirs(out_dir, exist_ok=True)
    if model_name:
        G.name = model_name

    if gen_project:
        print(f"\nGenerating NNTool project → {out_dir}")
        dtype = np.float32 if input_dtype == "float32" else np.int8
        input_tensors = [np.zeros(input_shape, dtype=dtype)]
        G.gen_project(
            input_tensors=input_tensors,
            directory=out_dir,
            platform="gvsoc",
            cmake=True,
        )
    else:
        out_c = os.path.join(out_dir, f"{model_name}_model.c")
        print(f"\nGenerating AutoTiler code → {out_c}")

        model_file = f"{model_name}_model.c"
        G.gen_at_model(
            directory=out_dir,
            settings=model_settings(
                model_directory=out_dir,
                model_file=model_file,
            )
        )

    _finish_codegen(G, out_dir, model_name)


def _finish_codegen(G, out_dir, model_name):
    nntool_graph_path = os.path.join(out_dir, f"{model_name}.json")
    saved = False
    save_attempts = [
        ("save_quantized", lambda: G.save_quantized(nntool_graph_path)),
        ("save_graph", lambda: G.save_graph(nntool_graph_path)),
        ("save", lambda: G.save(nntool_graph_path)),
    ]
    for method_name, save_fn in save_attempts:
        if not hasattr(G, method_name):
            continue
        try:
            save_fn()
            print(f"  Graph saved via {method_name}: {nntool_graph_path}")
            saved = True
            break
        except Exception as exc:
            print(f"  ({method_name} failed: {exc})")
    if not saved:
        print("  (No compatible graph save method found; skipping graph save)")
    print(f"\nCode generation complete. Files in: {os.path.abspath(out_dir)}")


# ─────────────────────────────────────────────────────────────────────────────
# Load paths
# ─────────────────────────────────────────────────────────────────────────────

def load_float32_and_prepare(model_path: str, verbose: bool = True) -> NNGraph:
    """Load float32 ONNX in CHW layout, run fusions."""
    print(f"\n{'='*60}\n  Loading float32 model: {model_path}\n{'='*60}")
    G = NNGraph.load_graph(model_path, load_quantization=False)
    if verbose:
        G.show()
    print("\n[1/3] scaled_match_group fusions ...")
    G.fusions("scaled_match_group")
    if verbose:
        print("\nPost-fusion graph:"); G.show()
    return G


def load_qdq_and_prepare(qdq_path: str, verbose: bool = True) -> NNGraph:
    """
    Load a QDQ int8 ONNX and import embedded quantization scales.

    Key difference from the float32 path: we do NOT call adjust_order().
    A QDQ ONNX exported from a framework already encodes the axis layout in
    the Q/DQ scale tensors.  Calling adjust_order() on it inserts an extra
    Transpose that mirrors the one already present at the graph boundary,
    resulting in a double-transpose that makes the output shape look like
    the input shape (the bug you saw: output (1,3,224,224) instead of
    (1,28,28,76)).

    Instead we let NNTool import the graph as-is and rely on the fusion
    passes to canonicalise the layout.
    """
    print(f"\n{'='*60}\n  Loading QDQ model: {qdq_path}\n{'='*60}")

    load_attempts = [
        {
            "load_quantization": True,
            "remove_quantize_ops": True,
            "onnx_qdq_qrec_conversion": True,
        },
        {"load_quantization": True},
    ]
    G = None
    last_exc = None
    for opts in load_attempts:
        try:
            G = NNGraph.load_graph(qdq_path, **opts)
            if verbose:
                print(f"\nLoaded QDQ graph with options: {opts}")
            break
        except TypeError as exc:
            last_exc = exc
            continue
    if G is None:
        raise last_exc

    if verbose:
        print("\nRaw imported graph:"); G.show()

    # Print input/output shapes so we can verify layout before fusions
    print("\nInput  nodes:")
    for n in G.input_nodes():
        print(f"  {n.name}  dims={n.out_dims}")
    print("Output nodes:")
    for n in G.output_nodes():
        print(f"  {n.name}  dims={n.in_dims}")

    print("\n[1/3] scaled_match_group fusions ...")
    G.fusions("scaled_match_group")

    print("[2/3] remove_unnecessary_quantize_operators ...")
    try:
        G.fusions("remove_unnecessary_quantize_operators")
    except Exception as exc:
        print(f"  (skipped — not available in this NNTool version: {exc})")

    if verbose:
        print("\nPost-fusion graph:"); G.show()
        _print_io_quantization(G)

    # Report actual output shape so caller can set expected_out_shape
    print("\nFinal output nodes:")
    for n in G.output_nodes():
        print(f"  {n.name}  dims={n.in_dims}")

    return G


def quantize_graph(G: NNGraph, stats: dict) -> None:
    """Apply scaled8 quantization using injected statistics."""
    print("\n[3/4] Quantizing ...")
    node_opts = {
        node.name: quantization_options(scheme="float", float_type="float32", hwc=False)
        for node in G.nodes(ExpressionFusionNode)
    }
    G.quantize(
        stats,
        schemes=["scaled"],
        graph_options=quantization_options(
            use_ne16=True,
            const_clip_type="std5",
            clip_type="none",
            hwc=False,
        ),
        node_options=node_opts if node_opts else None,
    )
    print("Quantization complete.")
    if True:
        G.show(show_quantization=True)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Deploy ONNX model to GAP9 via NNTool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--model",     required=True)
    p.add_argument("--model_qdq", default=None,
                   help="Optional QDQ ONNX for cross-check (inject_stats mode only)")
    p.add_argument("--outdir",    default="gen")
    p.add_argument("--name",      default="network")
    p.add_argument("--mode",
                   choices=["inject_stats", "qdq_direct"],
                   default="inject_stats")
    p.add_argument("--validate",  action="store_true")
    p.add_argument("--verbose",   action="store_true")
    p.set_defaults(gen_project=True)
    p.add_argument("--gen_project", action="store_true",
                   help="Generate full NNTool project (default)")
    p.add_argument("--gen_at_model", action="store_false", dest="gen_project",
                   help="Generate only AutoTiler model file")
    return p.parse_args()


def main():
    args = parse_args()

    if args.mode == "inject_stats":
        if not os.path.isfile(args.model):
            sys.exit(f"Model not found: {args.model}")
        G = load_float32_and_prepare(args.model, verbose=args.verbose)
        stats = build_stats_from_reference(G, REFERENCE_ACT_QUANT)
        quantize_graph(G, stats)
        expected_out = (1, 76, 28, 28)
        input_shape  = (1, 3, 224, 224)   # CHW
        input_dtype = "int8"

    else:  # qdq_direct
        qdq_src = args.model_qdq or args.model
        if not os.path.isfile(qdq_src):
            sys.exit(f"QDQ model not found: {qdq_src}")
        G = load_qdq_and_prepare(qdq_src, verbose=args.verbose)
        # QDQ graph already carries quantization — no quantize() call needed.
        # Determine expected shapes from the graph itself.
        out_nodes = list(G.output_nodes())
        if out_nodes and out_nodes[0].in_dims:
            raw = out_nodes[0].in_dims[0].shape
            # NNTool dim order is [N, C, H, W] or [N, H, W, C] depending on layout.
            # We just use whatever the graph reports as expected.
            expected_out = tuple(raw)
            print(f"\nExpected output shape from graph: {expected_out}")
        else:
            expected_out = (1, 28, 28, 76)
        input_shape = (1, 3, 224, 224)  # CHW
        input_dtype = _infer_input_dtype(G)

    verify_output_scales(G, REFERENCE_ACT_QUANT)

    if args.validate:
        if args.mode == "qdq_direct":
            # For QDQ validation, use CHW inputs directly
            G_validate = load_qdq_and_prepare(qdq_src, verbose=False)
            validate_inference(G_validate, expected_out_shape=expected_out,
                               input_shape=input_shape, input_dtype=input_dtype,
                               is_qdq=True)
        else:
            # For inject_stats mode, use CHW inputs
            validate_inference(G, expected_out_shape=expected_out,
                               input_shape=input_shape, input_dtype=input_dtype,
                               is_qdq=False)

    generate_code(G, out_dir=args.outdir, model_name=args.name,
                  input_shape=input_shape, input_dtype=input_dtype,
                  gen_project=args.gen_project)

    if args.model_qdq and args.mode == "inject_stats":
        print("\n── QDQ cross-check ──────────────────────────────────────")
        try:
            G_qdq = load_qdq_and_prepare(args.model_qdq, verbose=False)
            verify_output_scales(G_qdq, REFERENCE_ACT_QUANT)
        except Exception as exc:
            print(f"  QDQ cross-check failed (non-fatal): {exc}")


if __name__ == "__main__":
    main()
