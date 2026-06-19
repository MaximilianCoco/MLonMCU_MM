import os
import torch


def pt_to_header(file_path, output_h="X-CUBE-AI/App/memory_bank.h"):
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return

    print("Loading file... (this may take a moment for large files)")
    try:
        data = torch.load(file_path, map_location=torch.device('cpu'), weights_only=False)
    except Exception as e:
        print(f"Failed to load .pt file: {e}")
        return

    if not isinstance(data, dict):
        print("Error: Expected a dict with 'memory_int8' and 'scale' keys.")
        return

    if 'memory_int8' not in data or 'scale' not in data:
        print(f"Error: Expected keys 'memory_int8' and 'scale', but found: {list(data.keys())}")
        return

    tensor: torch.Tensor = data['memory_int8']
    scale_tensor: torch.Tensor = data['scale']

    if tensor.ndim != 2:
        print(f"Error: Expected a 2D tensor, got shape {list(tensor.shape)}")
        return

    n_vectors, vector_dim = tensor.shape
    scale = scale_tensor.item()

    # Build the rows of the C array
    rows = []
    tensor_list = tensor.tolist()
    for row in tensor_list:
        row_str = ", ".join(str(v) for v in row)
        rows.append(f"    {{ {row_str} }}")

    rows_joined = ",\n".join(rows)

    header_guard = os.path.basename(output_h).upper().replace(".", "_")
    source_basename = os.path.basename(file_path)

    header_content = f"""\
/**
 * @file {os.path.basename(output_h)}
 * @brief Anomaly detection memory bank (int8 quantized)
 * Extracted from {source_basename}
 *
 * This memory bank contains {n_vectors} normal feature vectors used
 * for anomaly detection via similarity scoring.
 */

#ifndef {header_guard}
#define {header_guard}

#include <stdint.h>

#define MEMORY_N_VECTORS  ({n_vectors})
#define MEMORY_VECTOR_DIM ({vector_dim})
#define MEMORY_SCALE      ({scale:.10e}f)

/* Memory bank data - int8 quantized [{n_vectors}][{vector_dim}] */
static const int8_t memory_bank[MEMORY_N_VECTORS][MEMORY_VECTOR_DIM] = {{
{rows_joined}
}};

#endif /* {header_guard} */
"""

    with open(output_h, "w", encoding="utf-8") as f:
        f.write(header_content)

    print(f"Success! C header saved to: {output_h}")
    print(f"  Vectors : {n_vectors}")
    print(f"  Dim     : {vector_dim}")
    print(f"  Scale   : {scale}")


# Usage — replace with your actual filename
pt_to_header("memory_int8_old1.pt", "X-CUBE-AI/App/memory_bank_test.h")
