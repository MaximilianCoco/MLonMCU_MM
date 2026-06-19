import numpy as np
import re
import glob
import os

def parse_header(header_path):
    """Extract flat int8 array from C header file."""
    with open(header_path, 'r') as f:
        content = f.read()
    match = re.search(r'\{([^}]+)\}', content, re.DOTALL)
    if not match:
        raise ValueError(f"No array data found in {header_path}")
    hex_vals = re.findall(r'0x[0-9A-Fa-f]+', match.group(1))
    values = []
    for h in hex_vals:
        v = int(h, 16)
        if v > 127:
            v -= 256  # unsigned byte → signed int8
        values.append(v)
    arr = np.array(values, dtype=np.int8)
    assert len(arr) == 224 * 224 * 3, f"Expected 150528 values, got {len(arr)}"
    return arr

def chw_to_hwc(flat_chw, C=3, H=224, W=224):
    """Convert flat CHW int8 array to flat HWC int8 array."""
    chw = flat_chw.reshape(C, H, W)       # (3, 224, 224)
    hwc = chw.transpose(1, 2, 0)          # (224, 224, 3)
    return hwc.flatten()

def hwc_to_chw(flat_hwc, C=3, H=224, W=224):
    """Convert flat HWC int8 array to flat CHW int8 array."""
    hwc = flat_hwc.reshape(H, W, C)       # (224, 224, 3)
    chw = hwc.transpose(2, 0, 1)          # (3, 224, 224)
    return chw.flatten()

def convert_headers_to_bins(header_dir, output_dir, target_format='hwc'):
    """
    Convert all .h files in header_dir to .bin files in output_dir.
    target_format: 'hwc' or 'chw'
    Headers are assumed to be CHW (as your comment states).
    """
    os.makedirs(output_dir, exist_ok=True)
    headers = glob.glob(os.path.join(header_dir, '*.h'))
    
    if not headers:
        print(f"No .h files found in {header_dir}")
        return

    for hf in sorted(headers):
        basename = os.path.splitext(os.path.basename(hf))[0]
        out_path = os.path.join(output_dir, basename + '.bin')
        
        flat_chw = parse_header(hf)
        
        if target_format == 'hwc':
            flat_out = chw_to_hwc(flat_chw)
            layout = 'HWC (1,224,224,3)'
        elif target_format == 'chw':
            flat_out = flat_chw          # already CHW, no conversion needed
            layout = 'CHW (1,3,224,224)'
        else:
            raise ValueError(f"Unknown format: {target_format}")
        
        flat_out.astype(np.int8).tofile(out_path)
        print(f"  {os.path.basename(hf)} → {os.path.basename(out_path)}  [{layout}]")

    print(f"\n✓ Converted {len(headers)} headers to {target_format.upper()} .bin files in {output_dir}/")

# ── Usage ────────────────────────────────────────────────────────────────────
# First run the diagnostic above to confirm nntool input format.
# Then call with the correct target_format.

# If nntool expects HWC:
# convert_headers_to_bins(
    # header_dir='your/headers/',
    # output_dir='input_bins/',
    # target_format='hwc'
#)

#If nntool expects CHW:
convert_headers_to_bins(
     header_dir='headers/',
     output_dir='input_bins/',
     target_format='chw'
)
