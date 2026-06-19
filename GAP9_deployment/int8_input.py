#!/usr/bin/env python3
"""
Prepare GAP9 test input by extracting quantized image to binary format
"""

import re
import struct
import numpy as np
from pathlib import Path

def extract_array_from_h_file(h_file):
    """Extract array from .h file and return as numpy array."""
    with open(h_file, 'r') as f:
        content = f.read()
    
    # Find the specific array for mms_rpi_test_crack_hole_IMG_0038_data
    # The array starts with 'mms_rpi_test_crack_hole_IMG_0038_data[...] = {' and ends with '}'
    match = re.search(
        r'static\s+const\s+int8_t\s+mms_rpi_test_crack_hole_IMG_0038_data\[.*?\]\s*=\s*\{([^}]+)\}',
        content, 
        re.DOTALL
    )
    if not match:
        raise ValueError(f"Could not find mms_rpi_test_crack_hole_IMG_0038_data array in {h_file}")
    
    array_content = match.group(1)
    
    # Extract hex values (0xNN format) - this file uses hex values
    hex_values = re.findall(r'0x([0-9A-Fa-f]{2})', array_content)
    
    if not hex_values:
        # Try decimal format as fallback
        numbers = re.findall(r'-?\d+', array_content)
        array = np.array([int(n) for n in numbers], dtype=np.int8)
    else:
        # Convert hex to int8 (handle both positive and negative)
        values = []
        for hex_val in hex_values:
            val = int(hex_val, 16)
            # Convert to signed int8
            if val > 127:
                val = val - 256
            values.append(val)
        array = np.array(values, dtype=np.int8)
    
    return array

def main():
    print("=" * 80)
    print("Preparing GAP9 Input")
    print("=" * 80)
    
    h_file = Path("*.h")
    output_file = Path("gen/Input_1.bin")
    
    print(f"\n1. Extracting image from: {h_file}")
    image_array = extract_array_from_h_file(h_file)
    print(f"   Extracted shape: {image_array.shape}")
    print(f"   Expected: (150528,)")
    print(f"   Dtype: {image_array.dtype}")
    print(f"   Range: [{image_array.min()}, {image_array.max()}]")
    
    if image_array.size != 150528:
        raise ValueError(f"Expected 150528 values, got {image_array.size}")
    
    print(f"\n2. Converting to binary format")
    binary_data = image_array.tobytes()
    print(f"   Binary size: {len(binary_data)} bytes")
    print(f"   Expected: 150528 bytes")
    
    if len(binary_data) != 150528:
        raise ValueError(f"Expected 150528 bytes, got {len(binary_data)}")
    
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
    verify_array = np.frombuffer(verify_data, dtype=np.int8)
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
