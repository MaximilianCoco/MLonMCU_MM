from nntool.api import NNGraph

G = NNGraph.load_graph(
    'model_int8_qdq.onnx',
    load_quantization=True,
    remove_quantize_ops=True,
    onnx_qdq_qrec_conversion=True
)

# Print all keys
print("=== All quantization keys ===")
keys = list(G.quantization.keys())
for k in keys:
    print(k)

# Input QRec details
qrec_in = G.quantization["input_1"]
print("\n=== Input QRec out_qs[0] ===")
qtype_in = qrec_in.out_qs[0]
print("scale:", qtype_in.scale)
print("zero_point:", qtype_in.zero_point)
print("scale type:", type(qtype_in.scale))
print("zero_point type:", type(qtype_in.zero_point))

# Output QRec (likely _net_net_8_Conv_reshape_out_qout0)
out_key = "_net_net_8_Conv_reshape_out_qout0"
if out_key in G.quantization:
    qrec_out = G.quantization[out_key]
    print("\n=== Output QRec ===")
    print("in_qs:", qrec_out.in_qs)
    if qrec_out.in_qs:
        qtype_out = qrec_out.in_qs[0]
        print("scale:", qtype_out.scale)
        print("zero_point:", qtype_out.zero_point)
    print("out_qs:", qrec_out.out_qs)
else:
    print(f"Key {out_key} not found. Trying to find output tensor...")
    # Search for the key that likely feeds output_1
    # We can look at the graph edges, but easier: last few keys
    print("Last few keys:", keys[-5:])
    # Let's check output_1
    if "output_1" in G.quantization:
        qrec_out = G.quantization["output_1"]
        print("Using 'output_1' key")
        print("in_qs:", qrec_out.in_qs)
