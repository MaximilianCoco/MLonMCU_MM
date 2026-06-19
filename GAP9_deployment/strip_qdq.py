import sys
import onnx
from onnx import numpy_helper

def strip_io_qdq(model_path, output_path):
    # Load the model
    model = onnx.load(model_path)
    graph = model.graph
    
    # Map initializers for easy lookup
    initializers = {init.name: init for init in graph.initializer}
    def get_constant_value(name):
        if name in initializers:
            tensor = initializers[name]
            return numpy_helper.to_array(tensor).item()
        return None

    nodes_to_remove = []
    input_remap = {}   
    output_remap = {}  
    io_quant_info = {"inputs": {}, "outputs": {}}

    # Process Input QuantizeLinear (Q) layers
    graph_input_names = {inp.name for inp in graph.input}
    for node in graph.node:
        if node.op_type == "QuantizeLinear" and node.input[0] in graph_input_names:
            input_name = node.input[0]
            q_output_name = node.output[0]
            
            scale = get_constant_value(node.input[1])
            zp = get_constant_value(node.input[2]) if len(node.input) > 2 else 0
            io_quant_info["inputs"][input_name] = {"scale": scale, "zero_point": zp}
            
            nodes_to_remove.append(node)
            input_remap[input_name] = q_output_name

    # Process Output DequantizeLinear (DQ) layers
    graph_output_names = {out.name for out in graph.output}
    for node in graph.node:
        if node.op_type == "DequantizeLinear" and node.output[0] in graph_output_names:
            dq_input_name = node.input[0]
            output_name = node.output[0]
            
            scale = get_constant_value(node.input[1])
            zp = get_constant_value(node.input[2]) if len(node.input) > 2 else 0
            io_quant_info["outputs"][output_name] = {"scale": scale, "zero_point": zp}
            
            nodes_to_remove.append(node)
            output_remap[output_name] = dq_input_name

    # Remove the QDQ nodes
    for node in nodes_to_remove:
        graph.node.remove(node)

    # Update Graph Inputs to INT8
    for graph_input in graph.input:
        if graph_input.name in input_remap:
            graph_input.type.tensor_type.elem_type = onnx.TensorProto.INT8
            graph_input.name = input_remap[graph_input.name]
            
    # Update Graph Outputs to INT8
    for graph_output in graph.output:
        if graph_output.name in output_remap:
            graph_output.type.tensor_type.elem_type = onnx.TensorProto.INT8
            graph_output.name = output_remap[graph_output.name]

    # Save the modified model
    onnx.checker.check_model(model)
    onnx.save(model, output_path)
    
    print("Successfully created raw INT8 model!")
    print("Write down these values for your app code:\n", io_quant_info)
    return io_quant_info

# This triggers execution when you run the file from terminal
if __name__ == "__main__":
    # REPLACE THESE WITH YOUR ACTUAL FILE NAMES
    input_file = "model_int8_qdq.onnx"
    output_file = "stripped_int8_model.onnx"
    
    strip_io_qdq(input_file, output_file)
