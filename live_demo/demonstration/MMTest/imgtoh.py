
from PIL import Image
import numpy as np
import glob
import os
import re
import torchvision.transforms as T

# Create headers directory if it doesn't exist
OUTPUT_DIR = r'C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\headers'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ImageNet normalization parameters (same as MMSDataset)
k= 1
IMAGENET_MEAN = [0.485*k, 0.456*k, 0.406*k]
IMAGENET_STD = [0.229, 0.224, 0.225]

# ONNX Model quantization parameters
# These match the INPUT quantization in the ONNX QDQ model
INPUT_SCALE = 0.01845340058207512
INPUT_ZERO_POINT = -13

# Find all PNG files in subdirectories
image_files = (
    glob.glob(r'C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\cropped/**/*.png', recursive=True) +
    glob.glob(r'C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\cropped/**/*.jpg', recursive=True) +
    glob.glob(r'C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\cropped/**/*.jpeg', recursive=True)
)
if not image_files:
    print("No PNG files found in subdirectories")
else:
    print(f"Found {len(image_files)} PNG file(s)\n")

    for png_path in image_files:
        try:
            # Get directory path and filename
            dir_path = os.path.dirname(png_path)
            base_name = os.path.splitext(os.path.basename(png_path))[0]
            
            # Build filename with directory structure: folder1_folder2_filename
            if dir_path:
                # Replace path separators with underscores
                dir_part = dir_path.replace(os.sep, '_').replace('/', '_')
                filename_with_dir = f"{base_name}"
            else:
                filename_with_dir = base_name
            
            # Convert filename to valid C identifier (replace special chars with underscores)
            c_identifier = re.sub(r'[^a-zA-Z0-9_]', '_', filename_with_dir)
            # Ensure it doesn't start with a number
            if c_identifier[0].isdigit():
                c_identifier = '_' + c_identifier
            
            # Create output header filename with full path
            output_filename = os.path.join(OUTPUT_DIR, f"{filename_with_dir}.h")
            
            print(f"Processing: {png_path}")
            
            # Load and process image
            img = Image.open(png_path)
            print(f"  Original size: {img.size}, Mode: {img.mode}")
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to 224x224
            img_resized = img.resize((224, 224), Image.Resampling.LANCZOS)
            print(f"  Resized to: {img_resized.size}")
            
            # Convert to numpy array and normalize (SAME as simplified.py / MMSDataset)
            img_array = np.array(img_resized, dtype=np.float32) / 255.0  # [0, 1]
            print(f"  Array shape (HWC): {img_array.shape}")
            
            # IMPORTANT: Match simplified.py which uses CHW format (channels first)
            # Permute from (H, W, C) to (C, H, W) - PyTorch default
            img_array = np.transpose(img_array, (2, 0, 1))
            print(f"  Array shape (CHW): {img_array.shape}")
            
            # Apply ImageNet normalization per channel
            # img_array is now (C, H, W) - channels are [R, G, B]
            for c in range(3):
                img_array[c] = (img_array[c] - IMAGENET_MEAN[c]) / IMAGENET_STD[c]
            
            # Flatten to 1D array (CHW format - all R values, then all G, then all B)
            img_float = img_array.flatten()
            print(f"  Flattened size (float32): {len(img_float)} values ({len(img_float) * 4} bytes)")
            
            # QUANTIZE to int8 using ONNX model parameters
            # Formula: int8 = clip(round(float_value / scale + zero_point), -128, 127)
            img_quantized = np.clip(
                np.round(img_float / INPUT_SCALE) + INPUT_ZERO_POINT,
                -128, 127
            ).astype(np.int8)
            print(f"  Quantized size (int8):   {len(img_quantized)} values ({len(img_quantized)} bytes)")
            print(f"  Quantized value range: [{img_quantized.min()}, {img_quantized.max()}]")
            
            # Generate C header file
            guard_name = c_identifier.upper() + "_H"
            output_filename_base = os.path.basename(output_filename)
            header_content = f"""/**
 * @file {output_filename_base}
 * @brief Image data - 224x224 RGB quantized to int8 for MCU inference
 * Generated from {png_path}
 * 
 * Preprocessing pipeline:
 * 1. Resize to 224x224
 * 2. Convert to float [0, 1] by dividing uint8 by 255
 * 3. Subtract mean: [0.485, 0.456, 0.406] per channel (ImageNet normalization)
 * 4. Divide by std:  [0.229, 0.224, 0.225] per channel (ImageNet normalization)
 * 5. Quantize to int8 using ONNX model parameters:
 *    - SCALE: {INPUT_SCALE}
 *    - ZERO_POINT: {INPUT_ZERO_POINT}
 *    - Formula: q = clip(round(f / scale + zero_point), -128, 127)
 * 
 * Data layout: CHW (Channels-Height-Width)
 * All Red channel pixels, then all Green, then all Blue
 * Ready to send over UART to MCU as binary data
 */

#ifndef {guard_name}
#define {guard_name}

#include <stdint.h>

#define {c_identifier.upper()}_WIDTH    (224)
#define {c_identifier.upper()}_HEIGHT   (224)
#define {c_identifier.upper()}_CHANNELS (3)
#define {c_identifier.upper()}_SIZE     ({c_identifier.upper()}_WIDTH * {c_identifier.upper()}_HEIGHT * {c_identifier.upper()}_CHANNELS)

/* Image data: 224x224 RGB image quantized to int8 = 150,528 bytes */
static const int8_t {c_identifier}_data[{c_identifier.upper()}_SIZE] = {{
"""
            
            # Add quantized image data in chunks of 16 hex values per line
            # Convert int8 to uint8 for hex representation
            img_uint8 = img_quantized.astype(np.uint8)
            for i in range(0, len(img_uint8), 16):
                chunk = img_uint8[i:i+16]
                hex_values = [f"0x{v:02X}" for v in chunk]
                header_content += "    " + ", ".join(hex_values)
                if i + 16 < len(img_uint8):
                    header_content += ",\n"
                else:
                    header_content += "\n"
            
            header_content += f"""
}};

#endif /* {guard_name} */
"""
            
            # Write to file in headers directory
            with open(output_filename, 'w') as f:
                f.write(header_content)
            
            print(f"  ✓ Generated {output_filename}\n")
            
        except Exception as e:
            print(f"  ✗ Error processing {png_path}: {e}\n")
            continue

print("Done!")

