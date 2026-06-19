from nntool.api import NNGraph
import numpy as np
import os

G = NNGraph.load_graph(
    'model_int8_qdq.onnx',
    load_quantization=True,
    remove_quantize_ops=True,
    onnx_qdq_qrec_conversion=True  # Only valid combination
)

print("Available quantization nodes:")
for key in sorted(G.quantization.keys()):
    qrec = G.quantization[key]
    in_s  = qrec.in_qs[0].scale  if qrec.in_qs  and qrec.in_qs[0]  is not None else "N/A"
    out_s = qrec.out_qs[0].scale if qrec.out_qs and qrec.out_qs[0] is not None else "N/A"
    in_z  = qrec.in_qs[0].zero_point  if qrec.in_qs  and qrec.in_qs[0]  is not None else "N/A"
    out_z = qrec.out_qs[0].zero_point if qrec.out_qs and qrec.out_qs[0] is not None else "N/A"
    print(f"  {key}: in_scale={in_s}, in_zp={in_z} | out_scale={out_s}, out_zp={out_z}")