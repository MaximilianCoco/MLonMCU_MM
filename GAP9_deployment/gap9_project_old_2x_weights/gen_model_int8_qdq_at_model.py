import argparse
import argcomplete
import os
import numpy as np

from nntool.api import NNGraph
from nntool.api.utils import model_settings, quantization_options

def create_parser():
    # create the top-level parser
    parser = argparse.ArgumentParser(prog='gen_at_model')

    parser.add_argument('--trained_model', default=None,
                        help='Output - Trained model in tflite/onnx format')
    parser.add_argument('--tensors_dir', default="tensors",
                        help="Where nntool stores the weights/bias tensors dir")
    parser.add_argument('--at_model_path', default="build/model_dir/Model.c",
                        help="Path to the C autotiler model file to generate (only used in generate mode)")
    parser.add_argument('--ram_type', default="AT_MEM_L3_DEFAULTRAM", choices=['AT_MEM_L3_HRAM', 'AT_MEM_L3_QSPIRAM', 'AT_MEM_L3_OSPIRAM', 'AT_MEM_L3_DEFAULTRAM'],
                        help="Ram type to use during inference on platform")
    parser.add_argument('--flash_type', default="AT_MEM_L3_DEFAULTFLASH", choices=['AT_MEM_L3_PRI1', 'AT_MEM_L3_PRI2', 'AT_MEM_L3_HFLASH', 'AT_MEM_L3_QSPIFLASH', 'AT_MEM_L3_OSPIFLASH', 'AT_MEM_L3_MRAMFLASH', 'AT_MEM_L3_DEFAULTFLASH'],
                        help="Flash type to use during inference")
    parser.add_argument('--pri_flash_type', default=None, choices=['AT_MEM_L3_PRI1', 'AT_MEM_L3_HFLASH', 'AT_MEM_L3_QSPIFLASH', 'AT_MEM_L3_OSPIFLASH', 'AT_MEM_L3_MRAMFLASH', 'AT_MEM_L3_DEFAULTFLASH'],
                        help="Flash type to use during inference")
    return parser

if __name__ == '__main__':

    raise NotImplementedError('''
        Please replace in this script your code to prepare the model in NNTool
        (adjust, fusions, quantization, ...) and use CMakeLists.txt to pass the correct
        arguments to the script.
    ''')
    parser = create_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    # Example of model preparation
    G = NNGraph.load_graph(args.trained_model, load_quantization=False)

    # To change the model name which is used as the project target name
    # G.name = "my_model_name"

    G.adjust_order()
    G.fusions("scaled_match_group")

    def representative_dataset():
        # insert here the data you want to iterate on for quantization calibration
        calibration_data = [np.random.uniform(0, 1, G[0].in_dims[0].shape)]
        for data in calibration_data:
            data = data.reshape(G[0].in_dims[0].shape)
            yield data.astype(np.float32)
    stats = G.collect_statistics(representative_dataset())
    G.quantize(
        stats,
        graph_options=quantization_options(use_ne16=True)
    )

    # This function generates the Autotiler model
    # use model_settings to set the graph controller options of the autotiler model and other
    # settings (look the NNTool API documentation for more details)
    G.gen_at_model(
        directory=os.path.split(args.at_model_path)[0],
        settings=model_settings(
            tensor_directory=args.tensors_dir,
            model_directory=os.path.dirname(args.at_model_path),
            model_file=os.path.basename(args.at_model_path),
            l3_ram_device=args.ram_type,
            l3_flash_device=args.flash_type,

            graph_l1_promotion=2,
            graph_async_fork=True,
            graph_monitor_cycles=True,
            graph_produce_node_names=True,
            graph_produce_operinfos=True,
        )
    )