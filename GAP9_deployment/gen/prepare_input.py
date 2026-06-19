#!/usr/bin/env python3
"""
Prepare input for GAP9 model 'network'
Generated from QDQ ONNX with symmetric NNTool quantization.
"""
import numpy as np
import sys
from PIL import Image

GAP9_SCALE = 2.0000000000e-02
GAP9_ZP    = 0
ONNX_SCALE = 1.8453400000e-02
ONNX_ZP    = -13

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
    print(f"Saved Input_1.bin, shape={q.shape}, min={q.min()}, max={q.max()}")

if __name__ == "__main__":
    main()
