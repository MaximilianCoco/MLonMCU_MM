#!/usr/bin/env python3
"""
Prepare GAP9 test input by extracting float32 image data to binary format.
"""

import re
import argparse
import numpy as np
from pathlib import Path

def extract_array_from_h_file(h_file):
    """Extract array from .h file and return as numpy array."""
    with open(h_file, 'r') as f:
        content = f.read()
    
    # Find the float32 array in the header
    match = re.search(
        r'static\s+const\s+float\s+([A-Za-z0-9_]+)\[.*?\]\s*=\s*\{([^}]+)\}',
        content,
        re.DOTALL,
    )
    if not match:
        raise ValueError(f"Could not find float data array in {h_file}")

    array_content = match.group(2)

    numbers = re.findall(
        r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?',
        array_content,
    )
    if not numbers:
        raise ValueError(f"No numeric values found in {h_file}")
    array = np.array([float(n) for n in numbers], dtype=np.float32)
    
    return array

def main():
    print("=" * 80)
    print("Preparing GAP9 Input")
    print("=" * 80)
    
    parser = argparse.ArgumentParser(description="Prepare GAP9 float32 input")
    parser.add_argument("--input", default="mms_rpi_test_crack_hole_IMG_0038.h")
    parser.add_argument("--output", default="gen/Input_1.bin")
    args = parser.parse_args()

    h_file = Path(args.input)
    output_file = Path(args.output)
    
    print(f"\n1. Extracting image from: {h_file}")
    image_array = extract_array_from_h_file(h_file)
    print(f"   Extracted shape: {image_array.shape}")
    print(f"   Expected: (150528,)")
    print(f"   Dtype: {image_array.dtype}")
    print(f"   Range: [{image_array.min()}, {image_array.max()}]")
    
    if image_array.size != 150528:
        raise ValueError(f"Expected 150528 values, got {image_array.size}")
    
    print(f"\n2. Converting to binary format")
    binary_data = image_array.astype(np.float32).tobytes()
    expected_bytes = image_array.size * 4
    print(f"   Binary size: {len(binary_data)} bytes")
    print(f"   Expected: {expected_bytes} bytes")
    
    if len(binary_data) != expected_bytes:
        raise ValueError(f"Expected {expected_bytes} bytes, got {len(binary_data)}")
    
    print(f"\n3. Saving to: {output_file}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'wb') as f:
        f.write(binary_data)
    print(f"   ✓ Saved {len(binary_data)} bytes")
    
    print(f"\n4. Verification")
    # Read back and verify
    with open(output_file, 'rb') as f:
        verify_data = f.read()
    
    if verify_data == binary_data:
        print(f"   ✓ File verification passed")
    else:
        print(f"   ✗ File verification FAILED")
        return False
    
    # Verify content
    verify_array = np.frombuffer(verify_data, dtype=np.float32)
    if np.array_equal(verify_array, image_array):
        print(f"   ✓ Data content verification passed")
    else:
        print(f"   ✗ Data content verification FAILED")
        return False
    
    print(f"\n" + "=" * 80)
    print(f"✓ GAP9 input prepared successfully")
    print(f"  File: {output_file}")
    print(f"  Size: {len(binary_data)} bytes")
    print(f"=" * 80)
    
    # Also save as numpy for reference
    npy_file = output_file.with_suffix('.npy')
    np.save(npy_file, image_array)
    print(f"\nReference numpy file also saved: {npy_file}")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
