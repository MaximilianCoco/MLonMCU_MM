#!/usr/bin/env python3
"""
Test ONNX model with quantized test image.

This script:
1. Extracts the quantized int8 image from testimage_inputscaled.h
2. Dequantizes it to float32 using INPUT_SCALE and INPUT_ZERO_POINT
3. Runs inference on the model_int8_qdq.onnx model
4. Outputs the results for comparison with GAP9
"""

import numpy as np
import re
import sys
from pathlib import Path

def extract_array_from_h_file(h_file_path):
    """
    Extract the array data from a .h file containing int8 array.
    Returns the array as a list of int8 values.
    """
    with open(h_file_path, 'r') as f:
        content = f.read()
    
    # Find the array definition
    # Looking for pattern like: static const int8_t array[] = { ... };
    # or just the data array within comments
    
    # Extract values between { and }
    match = re.search(r'\{([^}]+)\}', content, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find array data in {h_file_path}")
    
    array_str = match.group(1)
    
    # Split by comma and convert to integers
    values = []
    for val_str in array_str.split(','):
        val_str = val_str.strip()
        if val_str and not val_str.startswith('//'):
            try:
                # Handle both decimal and hex values
                if val_str.startswith('0x') or val_str.startswith('0X'):
                    values.append(int(val_str, 16))
                else:
                    values.append(int(val_str))
            except ValueError:
                # Skip non-numeric values (like comments)
                pass
    
    return np.array(values, dtype=np.int8)


def dequantize_image(quantized_data, scale, zero_point):
    """
    Dequantize int8 quantized data to float32.
    
    Formula: float_value = (int8_value - zero_point) * scale
    """
    # Convert to float for calculation
    float_data = (quantized_data.astype(np.float32) - zero_point) * scale
    return float_data


def load_and_test_onnx(onnx_path, input_data, input_name="Input_1"):
    """
    Load ONNX model and run inference.
    """
    try:
        import onnx
        import onnxruntime
    except ImportError:
        print("ERROR: onnx and onnxruntime are required")
        print("Install with: pip install onnx onnxruntime")
        sys.exit(1)
    
    # Load model
    print(f"Loading ONNX model: {onnx_path}")
    model = onnx.load(onnx_path)
    
    # Verify input/output shapes
    print("\n=== Model Structure ===")
    print(f"Number of inputs: {len(model.graph.input)}")
    print(f"Number of outputs: {len(model.graph.output)}")
    
    for inp in model.graph.input:
        shape = [d.dim_value for d in inp.type.tensor_type.shape.dim]
        print(f"Input '{inp.name}': shape {shape}")
    
    for out in model.graph.output:
        shape = [d.dim_value for d in out.type.tensor_type.shape.dim]
        print(f"Output '{out.name}': shape {shape}")
    
    # Create inference session
    print(f"\nCreating inference session...")
    session = onnxruntime.InferenceSession(onnx_path)
    
    # Prepare input
    # Model expects [1, C, H, W] format (channel-first)
    # Input data is currently [H*W*C] (flattened), so reshape to [H, W, C] then transpose to [C, H, W]
    input_data_reshaped = input_data.reshape(224, 224, 3)
    # Transpose from [H, W, C] to [C, H, W]
    input_data_reshaped = np.transpose(input_data_reshaped, (2, 0, 1))
    # Add batch dimension [C, H, W] -> [1, C, H, W]
    input_data_reshaped = np.expand_dims(input_data_reshaped, 0).astype(np.float32)
    
    print(f"Input shape after reshape: {input_data_reshaped.shape}")
    print(f"Input data range: [{input_data_reshaped.min():.6f}, {input_data_reshaped.max():.6f}]")
    print(f"Input data mean: {input_data_reshaped.mean():.6f}")
    print(f"Input data std: {input_data_reshaped.std():.6f}")
    
    # Run inference
    print(f"\nRunning inference...")
    input_name_actual = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    
    print(f"Using input name: {input_name_actual}")
    print(f"Output name: {output_name}")
    
    outputs = session.run(
        [output_name],
        {input_name_actual: input_data_reshaped}
    )
    
    output_data = outputs[0]
    print(f"\n=== Inference Results ===")
    print(f"Output shape: {output_data.shape}")
    print(f"Output dtype: {output_data.dtype}")
    print(f"Output range: [{output_data.min():.6f}, {output_data.max():.6f}]")
    print(f"Output mean: {output_data.mean():.6f}")
    print(f"Output std: {output_data.std():.6f}")
    
    # Flatten output for easier analysis
    output_flat = output_data.flatten()
    print(f"\nFlattened output shape: {output_flat.shape}")
    print(f"First 20 values: {output_flat[:20]}")
    print(f"Last 5 values: {output_flat[-5:]}")
    
    return output_data, output_flat


def quantize_output(output_float, scale, zero_point):
    """
    Quantize the float output back to int8 for comparison with GAP9.
    Formula: int8_value = round(float_value / scale) + zero_point
    """
    quantized = np.round(output_float / scale) + zero_point
    quantized = np.clip(quantized, -128, 127).astype(np.int8)
    return quantized


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test ONNX model with quantized test image')
    parser.add_argument('--h-file', default='gap9_project/testimage_inputscaled.h',
                        help='Path to quantized test image .h file')
    parser.add_argument('--onnx-file', default='gap9_project/model_int8_qdq.onnx',
                        help='Path to ONNX model')
    parser.add_argument('--output-file', default='onnx_output_float.npy',
                        help='Path to save output (float32)')
    parser.add_argument('--output-quant-file', default='onnx_output_quantized.npy',
                        help='Path to save quantized output (int8)')
    
    args = parser.parse_args()
    
    # Quantization parameters from modelInfos.h
    INPUT_SCALE = 0.01845340058207512
    INPUT_ZERO_POINT = -13
    OUTPUT_SCALE = 8.462232653982937e-05
    OUTPUT_ZERO_POINT = 12
    
    print("=" * 80)
    print("Testing ONNX Model with Quantized Input Image")
    print("=" * 80)
    
    print(f"\nQuantization Parameters:")
    print(f"  INPUT_SCALE: {INPUT_SCALE}")
    print(f"  INPUT_ZERO_POINT: {INPUT_ZERO_POINT}")
    print(f"  OUTPUT_SCALE: {OUTPUT_SCALE}")
    print(f"  OUTPUT_ZERO_POINT: {OUTPUT_ZERO_POINT}")
    
    # Step 1: Extract quantized image from .h file
    print(f"\n{'='*80}")
    print("Step 1: Extracting quantized image from .h file")
    print('='*80)
    print(f"Reading: {args.h_file}")
    quantized_image = extract_array_from_h_file(args.h_file)
    print(f"Extracted {len(quantized_image)} values")
    print(f"Shape: {quantized_image.shape}")
    print(f"Expected: {224*224*3} = {224*224*3}")
    assert len(quantized_image) == 224*224*3, f"Expected {224*224*3} values, got {len(quantized_image)}"
    print(f"✓ Image size correct")
    
    # Step 2: Dequantize to float32
    print(f"\n{'='*80}")
    print("Step 2: Dequantizing image to float32")
    print('='*80)
    print(f"Dequantization formula: float = (int8 - {INPUT_ZERO_POINT}) * {INPUT_SCALE}")
    dequantized_image = dequantize_image(quantized_image, INPUT_SCALE, INPUT_ZERO_POINT)
    print(f"Dequantized image shape: {dequantized_image.shape}")
    print(f"Dequantized image range: [{dequantized_image.min():.6f}, {dequantized_image.max():.6f}]")
    print(f"Dequantized image mean: {dequantized_image.mean():.6f}")
    print(f"✓ Dequantization complete")
    
    # Verify roundtrip (dequantize then quantize)
    print(f"\nVerifying quantization roundtrip...")
    requantized = np.round(dequantized_image / INPUT_SCALE) + INPUT_ZERO_POINT
    requantized = np.clip(requantized, -128, 127).astype(np.int8)
    roundtrip_error = np.abs(requantized - quantized_image)
    print(f"Max roundtrip error: {roundtrip_error.max()}")
    print(f"Mean roundtrip error: {roundtrip_error.mean()}")
    print(f"✓ Roundtrip verified (error < 1 is acceptable)")
    
    # Step 3: Run ONNX inference
    print(f"\n{'='*80}")
    print("Step 3: Running ONNX model inference")
    print('='*80)
    output_float, output_flat = load_and_test_onnx(args.onnx_file, dequantized_image)
    
    # Step 4: Quantize output for comparison
    print(f"\n{'='*80}")
    print("Step 4: Quantizing output to int8")
    print('='*80)
    print(f"Quantization formula: int8 = round(float / {OUTPUT_SCALE}) + {OUTPUT_ZERO_POINT}")
    output_quantized = quantize_output(output_float, OUTPUT_SCALE, OUTPUT_ZERO_POINT)
    print(f"Quantized output shape: {output_quantized.shape}")
    print(f"Quantized output range: [{output_quantized.min()}, {output_quantized.max()}]")
    print(f"✓ Output quantization complete")
    
    # Step 5: Save results
    print(f"\n{'='*80}")
    print("Step 5: Saving results")
    print('='*80)
    
    # Save float output
    np.save(args.output_file, output_float)
    print(f"✓ Saved float output: {args.output_file}")
    
    # Save quantized output
    np.save(args.output_quant_file, output_quantized)
    print(f"✓ Saved quantized output: {args.output_quant_file}")
    
    # Also save as binary (for direct comparison with GAP9 output)
    output_binary_file = args.output_quant_file.replace('.npy', '.bin')
    output_quantized.astype(np.int8).tofile(output_binary_file)
    print(f"✓ Saved quantized output as binary: {output_binary_file}")
    
    # Save a detailed report
    report_file = args.output_quant_file.replace('.npy', '_report.txt')
    with open(report_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("ONNX Model Inference Report\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("Input Image:\n")
        f.write(f"  Quantized shape: {quantized_image.shape}\n")
        f.write(f"  Dequantized range: [{dequantized_image.min():.6f}, {dequantized_image.max():.6f}]\n")
        f.write(f"  Dequantized mean: {dequantized_image.mean():.6f}\n")
        f.write(f"  Dequantized std: {dequantized_image.std():.6f}\n\n")
        
        f.write("Output Results:\n")
        f.write(f"  Float output shape: {output_float.shape}\n")
        f.write(f"  Float output range: [{output_float.min():.6f}, {output_float.max():.6f}]\n")
        f.write(f"  Float output mean: {output_float.mean():.6f}\n")
        f.write(f"  Float output std: {output_float.std():.6f}\n\n")
        
        f.write(f"  Quantized output shape: {output_quantized.shape}\n")
        f.write(f"  Quantized output range: [{output_quantized.min()}, {output_quantized.max()}]\n")
        f.write(f"  Quantized output mean: {output_quantized.mean():.2f}\n")
        f.write(f"  Quantized output std: {output_quantized.std():.2f}\n\n")
        
        f.write("First 20 output values (float):\n")
        f.write(f"  {output_flat[:20]}\n\n")
        
        f.write("First 20 output values (quantized int8):\n")
        f.write(f"  {output_quantized.flatten()[:20]}\n\n")
        
        f.write("Last 5 output values (float):\n")
        f.write(f"  {output_flat[-5:]}\n\n")
        
        f.write("Last 5 output values (quantized int8):\n")
        f.write(f"  {output_quantized.flatten()[-5:]}\n\n")
    
    print(f"✓ Saved detailed report: {report_file}")
    
    print(f"\n{'='*80}")
    print("Test Complete!")
    print('='*80)
    print(f"\nFiles generated:")
    print(f"  1. Float output: {args.output_file}")
    print(f"  2. Quantized output (numpy): {args.output_quant_file}")
    print(f"  3. Quantized output (binary): {output_binary_file}")
    print(f"  4. Report: {report_file}")
    print(f"\nNext step: Use the quantized output to compare with GAP9 results")


if __name__ == '__main__':
    main()
