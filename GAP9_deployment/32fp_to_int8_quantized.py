from nntool.api import NNGraph
from nntool.api.utils import quantization_options
import numpy as np
import os

# Load the float32 ONNX model with quantization information if available
G = NNGraph.load_graph(
    'model_fp32.onnx',
    load_quantization=True,
    remove_quantize_ops=True,
    onnx_qdq_qrec_conversion=True
)

# Adjust tensor ordering to CHW (default for GAP)
G.adjust_order()

# --- Quantization Setup ---
# Collect statistics from calibration data if quantization info isn't in the model
# If you have calibration data, replace this with:
# stats = G.collect_statistics(calibration_data_iterator())
# 
# For now, using min/max ranges from the model itself or you can provide calibration data

# NOTE: With Scaled8, NNTool will add quantization/dequantization layers:
# - Input layer: dequantizes int8 input to float32 (applies input_scale, input_zero_point)
# - Output layer: quantizes float32 to int8 (applies output_scale, output_zero_point)
# These scale/zero-point values will be in the generated C code but the actual
# int8->float32 and float32->int8 transformations happen OUTSIDE the MCU model
# (you apply them on the host side before/after inference)

try:
    # Try to use statistics from the loaded ONNX quantization info
    stats = G.collect_statistics()
except:
    # Fallback: if no calibration data, quantization will use model defaults
    stats = None
    print("WARNING: No calibration statistics available. Consider providing calibration data.")

# --- Fuse operations ---
G.fusions('scaled_match_group')

# --- Quantize with Scaled8 scheme ---
# Scaled8 = 8bit symmetric per-channel weights, 8bit symmetric per-tensor activations
G.quantize(
    stats,
    schemes=['scaled'],  # Linear/Uniform quantization
    graph_options=quantization_options(
        # Scaled8 settings
        hwc=False,  # Keep CHW ordering (set True if you need HWC)
        # Clipping strategy for constants (weights)
        const_clip_type="std5",  # Use mean ± 5*std for weight ranges
        # Clipping strategy for activations
        clip_type="none",  # Use actual min/max from statistics
    )
)

# --- Generate GAP9 project ---
# Input is int8, output will be int8 (with quantization layers handling scaling)
os.makedirs('gap9_int8', exist_ok=True)
G.gen_project(
    input_tensors=[np.zeros((1, 224, 224, 3), dtype=np.int8)],
    directory='gap9_int8',
    platform='gvsoc',
    cmake=True,
)

print("✓ Project generated in 'gap9_int8/'")
print("\nIMPORTANT - Quantization scaling handling:")
print("- Input: Convert your float32 images to int8 using the quantization scale/zero-point")
print("  from gap9_int8/nntool_generated_quantization_data.h (or equivalent)")
print("- Output: Convert int8 output back to float32 using output scale/zero-point")
print("- These transformations are NOT in the MCU code—apply them on the host side")
