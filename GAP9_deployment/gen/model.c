#include <stdint.h>
#include <stdio.h>
#include "AutoTilerLib.h"
#include "CNN_Generators_SQ8.h"
#include "CNN_Generators.h"
#include "CNN_Generators_NE16.h"

#include "CNN_Copy_Generators.h"

void load_expressions_kernels() {
}





void networkModel(unsigned int L1Memory, unsigned int L2Memory, unsigned int L3Memory, unsigned int L3Flash)
{
    KernelOper_T Cop = KOP_CONV;

    // SetKernelOpts(KER_OPT_NONE, KER_OPT_BUFFER_PROMOTE);
    SetSymbolDynamics();

    SetUsedFilesNames(0, 6, "at_api.h", "network.h", "CNN_BasicKernels_SQ8.h", "CNN_BasicKernels.h", "CNN_BasicKernels_NE16.h", "Expression_Kernels.h");
    SetGeneratedFilesNames("networkKernels.c", "networkKernels.h");
    AT_SetGraphCtrl(AT_GRAPH_MONITOR_CYCLES, AT_OPT_ON);
    AT_SetGraphCtrl(AT_GRAPH_PRODUCE_NODE_NAMES, AT_OPT_ON);
    AT_SetGraphCtrl(AT_GRAPH_PRODUCE_OPERINFOS, AT_OPT_ON);

    SetMemoryDeviceInfos(4,
        AT_MEM_L1, L1Memory, "network_L1_Memory", 0, 0,
        AT_MEM_L2, L2Memory, "network_L2_Memory", 0, 1,
        AT_MEM_L3_DEFAULTRAM, L3Memory, "network_L3_Memory", 0, 0,
        AT_MEM_L3_DEFAULTFLASH, L3Flash, "network_L3_Flash", "network_L3_Flash_Const.dat", 0
    );

    LoadCNN_SQ8_Library();
    LoadCNNLibrary();
    LoadCNN_NE16_SQ8_Library();
    load_expressions_kernels();

    CNN_GenControl_T gen_ctrl_S4__net_net_0_Conv;
    CNN_InitGenCtrl(&gen_ctrl_S4__net_net_0_Conv);
    CNN_SetGenCtrl(&gen_ctrl_S4__net_net_0_Conv, "INPUT_DATASIZE", AT_OPT_VAL(-1));
    CNN_SetGenCtrl(&gen_ctrl_S4__net_net_0_Conv, "OUTPUT_DATASIZE", AT_OPT_VAL(-1));
    // generator for _net_net_0_Conv
    CNN_ConvolutionNE16("S4__net_net_0_Conv", &gen_ctrl_S4__net_net_0_Conv,
                        -1, -1, 4, 1, 8,
                        3, 9, 224, 224,
                        KOP_CONV, 3, 3, 1, 1, 1, 1, 1, 115,
                        KOP_NONE, 0, 0, 0, 0, 0, 0, 0,
                        KOP_NONE);
    
    CNN_GenControl_T gen_ctrl_S7__net_net_2_Conv;
    CNN_InitGenCtrl(&gen_ctrl_S7__net_net_2_Conv);
    CNN_SetGenCtrl(&gen_ctrl_S7__net_net_2_Conv, "INPUT_DATASIZE", AT_OPT_VAL(-1));
    CNN_SetGenCtrl(&gen_ctrl_S7__net_net_2_Conv, "OUTPUT_DATASIZE", AT_OPT_VAL(-1));
    // generator for _net_net_2_Conv
    CNN_ConvolutionNE16("S7__net_net_2_Conv", &gen_ctrl_S7__net_net_2_Conv,
                        -1, -1, 4, 1, 8,
                        9, 19, 224, 224,
                        KOP_CONV, 3, 3, 1, 1, 2, 2, 1, 128,
                        KOP_NONE, 0, 0, 0, 0, 0, 0, 0,
                        KOP_NONE);
    
    CNN_GenControl_T gen_ctrl_S10__net_net_4_Conv;
    CNN_InitGenCtrl(&gen_ctrl_S10__net_net_4_Conv);
    CNN_SetGenCtrl(&gen_ctrl_S10__net_net_4_Conv, "INPUT_DATASIZE", AT_OPT_VAL(-1));
    CNN_SetGenCtrl(&gen_ctrl_S10__net_net_4_Conv, "OUTPUT_DATASIZE", AT_OPT_VAL(-1));
    // generator for _net_net_4_Conv
    CNN_ConvolutionNE16("S10__net_net_4_Conv", &gen_ctrl_S10__net_net_4_Conv,
                        -1, -1, 4, 1, 8,
                        19, 38, 112, 112,
                        KOP_CONV, 3, 3, 1, 1, 2, 2, 1, 128,
                        KOP_NONE, 0, 0, 0, 0, 0, 0, 0,
                        KOP_NONE);
    
    CNN_GenControl_T gen_ctrl_S13__net_net_6_Conv;
    CNN_InitGenCtrl(&gen_ctrl_S13__net_net_6_Conv);
    CNN_SetGenCtrl(&gen_ctrl_S13__net_net_6_Conv, "INPUT_DATASIZE", AT_OPT_VAL(-1));
    CNN_SetGenCtrl(&gen_ctrl_S13__net_net_6_Conv, "OUTPUT_DATASIZE", AT_OPT_VAL(-1));
    // generator for _net_net_6_Conv
    CNN_ConvolutionNE16("S13__net_net_6_Conv", &gen_ctrl_S13__net_net_6_Conv,
                        -1, -1, 4, 1, 8,
                        38, 76, 56, 56,
                        KOP_CONV, 3, 3, 1, 1, 2, 2, 1, 128,
                        KOP_NONE, 0, 0, 0, 0, 0, 0, 0,
                        KOP_NONE);
    
    CNN_GenControl_T gen_ctrl_S16__net_net_8_Conv;
    CNN_InitGenCtrl(&gen_ctrl_S16__net_net_8_Conv);
    CNN_SetGenCtrl(&gen_ctrl_S16__net_net_8_Conv, "INPUT_DATASIZE", AT_OPT_VAL(-1));
    CNN_SetGenCtrl(&gen_ctrl_S16__net_net_8_Conv, "OUTPUT_DATASIZE", AT_OPT_VAL(-1));
    // generator for _net_net_8_Conv
    CNN_ConvolutionNE16("S16__net_net_8_Conv", &gen_ctrl_S16__net_net_8_Conv,
                        -1, -1, 4, 1, 8,
                        76, 76, 28, 28,
                        KOP_CONV, 3, 3, 1, 1, 1, 1, 1, 128,
                        KOP_NONE, 0, 0, 0, 0, 0, 0, 0,
                        KOP_NONE);
    

#define GRAPH
#ifdef GRAPH
    CreateGraph("networkCNN",
        /* Arguments either passed or globals */
            CArgs(27,
                TCArgInfo("unsigned char * __restrict__", "Input_1", ARG_SCOPE_ARG, ARG_DIR_IN, AT_MEM_L2, AT_MEM_L2, 0),
                TCArgInfo("unsigned char * __restrict__", "_net_net_0_conv_weights", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("_net_net_0_conv_weights.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed int * __restrict__", "Constant_net_0_bias_quantized", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("Constant_net_0_bias_quantized.tensor", 1, 1, 32, 0)),
                TCArgInfo("unsigned char * __restrict__", "S4_Mul_scale", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S4_Mul_scale.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed char * __restrict__", "S4_Mul_shift", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S4_Mul_shift.tensor", 1, 1, 8, 0)),
                // no activation BIASN: 0 PRENORM: 0 NE16_PADVAL: [115] NE16_WOFFSET: [-128]
                TCArgInfo("signed char * __restrict__", "S4_Infos", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S4_Infos.tensor", 1, 1, 8, 0)),
                TCArgInfo("unsigned char * __restrict__", "_net_net_2_conv_weights", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("_net_net_2_conv_weights.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed int * __restrict__", "Constant_net_2_bias_quantized", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("Constant_net_2_bias_quantized.tensor", 1, 1, 32, 0)),
                TCArgInfo("unsigned char * __restrict__", "S7_Mul_scale", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S7_Mul_scale.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed char * __restrict__", "S7_Mul_shift", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S7_Mul_shift.tensor", 1, 1, 8, 0)),
                // no activation BIASN: 0 PRENORM: 0 NE16_PADVAL: [128] NE16_WOFFSET: [-128]
                TCArgInfo("signed char * __restrict__", "S7_Infos", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S7_Infos.tensor", 1, 1, 8, 0)),
                TCArgInfo("unsigned char * __restrict__", "_net_net_4_conv_weights", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("_net_net_4_conv_weights.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed int * __restrict__", "Constant_net_4_bias_quantized", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("Constant_net_4_bias_quantized.tensor", 1, 1, 32, 0)),
                TCArgInfo("unsigned char * __restrict__", "S10_Mul_scale", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S10_Mul_scale.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed char * __restrict__", "S10_Mul_shift", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S10_Mul_shift.tensor", 1, 1, 8, 0)),
                // no activation BIASN: 0 PRENORM: 0 NE16_PADVAL: [128] NE16_WOFFSET: [-128]
                TCArgInfo("signed char * __restrict__", "S10_Infos", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S10_Infos.tensor", 1, 1, 8, 0)),
                TCArgInfo("unsigned char * __restrict__", "_net_net_6_conv_weights", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("_net_net_6_conv_weights.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed int * __restrict__", "Constant_net_6_bias_quantized", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("Constant_net_6_bias_quantized.tensor", 1, 1, 32, 0)),
                TCArgInfo("unsigned char * __restrict__", "S13_Mul_scale", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S13_Mul_scale.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed char * __restrict__", "S13_Mul_shift", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S13_Mul_shift.tensor", 1, 1, 8, 0)),
                // no activation BIASN: 0 PRENORM: 0 NE16_PADVAL: [128] NE16_WOFFSET: [-128]
                TCArgInfo("signed char * __restrict__", "S13_Infos", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S13_Infos.tensor", 1, 1, 8, 0)),
                TCArgInfo("unsigned char * __restrict__", "_net_net_8_conv_weights", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("_net_net_8_conv_weights.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed int * __restrict__", "Constant_net_8_bias_quantized", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("Constant_net_8_bias_quantized.tensor", 1, 1, 32, 0)),
                TCArgInfo("unsigned char * __restrict__", "S16_Mul_scale", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S16_Mul_scale.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed char * __restrict__", "S16_Mul_shift", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S16_Mul_shift.tensor", 1, 1, 8, 0)),
                // no activation BIASN: 0 PRENORM: 0 NE16_PADVAL: [128] NE16_WOFFSET: [-128]
                TCArgInfo("signed char * __restrict__", "S16_Infos", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S16_Infos.tensor", 1, 1, 8, 0)),
                TCArgInfo("unsigned char * __restrict__", "Output_1", ARG_SCOPE_ARG, ARG_DIR_OUT, AT_MEM_L2, AT_MEM_L2, 0)
            ),
        /* Locals, allocated dynamically */
        CArgs(4,
            TCArgInfo("unsigned char * __restrict__", "S4_Output", ARG_SCOPE_LOCAL, ARG_DIR_INOUT, AT_MEM_UNDEF, AT_MEM_UNDEF, 0),
            TCArgInfo("unsigned char * __restrict__", "S7_Output", ARG_SCOPE_LOCAL, ARG_DIR_INOUT, AT_MEM_UNDEF, AT_MEM_UNDEF, 0),
            TCArgInfo("unsigned char * __restrict__", "S10_Output", ARG_SCOPE_LOCAL, ARG_DIR_INOUT, AT_MEM_UNDEF, AT_MEM_UNDEF, 0),
            TCArgInfo("unsigned char * __restrict__", "S13_Output", ARG_SCOPE_LOCAL, ARG_DIR_INOUT, AT_MEM_UNDEF, AT_MEM_UNDEF, 0)
        )
    );



    // Node S4__net_net_0_Conv inq -2.12<(u8-115.00)*0.01845340<2.58 weightsq chan<(u8-128.00)*chan<chan outq -1.02<(u8-128.00)*0.00799756<1.02 biasesq chan<(i32-0.00)*chan<chan
    AddNode("S4__net_net_0_Conv",
        Bindings(7,
            GNodeArg(GNA_IN, "Input_1", 0),
            GNodeArg(GNA_IN, "_net_net_0_conv_weights", 0),
            GNodeArg(GNA_IN, "Constant_net_0_bias_quantized", 0),
            GNodeArg(GNA_OUT, "S4_Output", 0),
            GNodeArg(GNA_IN, "S4_Mul_scale", 0),
            GNodeArg(GNA_IN, "S4_Mul_shift", 0),
            GNodeArg(GNA_IN, "S4_Infos", 0)
        )
    );
    // Node S7__net_net_2_Conv inq -1.02<(u8-128.00)*0.00799756<1.02 weightsq chan<(u8-128.00)*chan<chan outq -0.18<(u8-128.00)*0.00138956<0.18 biasesq chan<(i32-0.00)*chan<chan
    AddNode("S7__net_net_2_Conv",
        Bindings(7,
            GNodeArg(GNA_IN, "S4_Output", 0),
            GNodeArg(GNA_IN, "_net_net_2_conv_weights", 0),
            GNodeArg(GNA_IN, "Constant_net_2_bias_quantized", 0),
            GNodeArg(GNA_OUT, "S7_Output", 0),
            GNodeArg(GNA_IN, "S7_Mul_scale", 0),
            GNodeArg(GNA_IN, "S7_Mul_shift", 0),
            GNodeArg(GNA_IN, "S7_Infos", 0)
        )
    );
    // Node S10__net_net_4_Conv inq -0.18<(u8-128.00)*0.00138956<0.18 weightsq chan<(u8-128.00)*chan<chan outq -0.10<(u8-128.00)*0.00078508<0.10 biasesq chan<(i32-0.00)*chan<chan
    AddNode("S10__net_net_4_Conv",
        Bindings(7,
            GNodeArg(GNA_IN, "S7_Output", 0),
            GNodeArg(GNA_IN, "_net_net_4_conv_weights", 0),
            GNodeArg(GNA_IN, "Constant_net_4_bias_quantized", 0),
            GNodeArg(GNA_OUT, "S10_Output", 0),
            GNodeArg(GNA_IN, "S10_Mul_scale", 0),
            GNodeArg(GNA_IN, "S10_Mul_shift", 0),
            GNodeArg(GNA_IN, "S10_Infos", 0)
        )
    );
    // Node S13__net_net_6_Conv inq -0.10<(u8-128.00)*0.00078508<0.10 weightsq chan<(u8-128.00)*chan<chan outq -0.01<(u8-128.00)*0.00009292<0.01 biasesq chan<(i32-0.00)*chan<chan
    AddNode("S13__net_net_6_Conv",
        Bindings(7,
            GNodeArg(GNA_IN, "S10_Output", 0),
            GNodeArg(GNA_IN, "_net_net_6_conv_weights", 0),
            GNodeArg(GNA_IN, "Constant_net_6_bias_quantized", 0),
            GNodeArg(GNA_OUT, "S13_Output", 0),
            GNodeArg(GNA_IN, "S13_Mul_scale", 0),
            GNodeArg(GNA_IN, "S13_Mul_shift", 0),
            GNodeArg(GNA_IN, "S13_Infos", 0)
        )
    );
    // Node S16__net_net_8_Conv inq -0.01<(u8-128.00)*0.00009292<0.01 weightsq chan<(u8-128.00)*chan<chan outq -0.01<(u8-128.00)*0.00009256<0.01 forced biasesq chan<(i32-0.00)*chan<chan
    AddNode("S16__net_net_8_Conv",
        Bindings(7,
            GNodeArg(GNA_IN, "S13_Output", 0),
            GNodeArg(GNA_IN, "_net_net_8_conv_weights", 0),
            GNodeArg(GNA_IN, "Constant_net_8_bias_quantized", 0),
            GNodeArg(GNA_OUT, "Output_1", 0),
            GNodeArg(GNA_IN, "S16_Mul_scale", 0),
            GNodeArg(GNA_IN, "S16_Mul_shift", 0),
            GNodeArg(GNA_IN, "S16_Infos", 0)
        )
    );
    CloseGraph();
#endif
}

int main(int argc, char **argv)

{
    if (TilerParseOptions(argc, argv)) {
            printf("Failed to initialize or incorrect output arguments directory.\n"); return 1;
    }
    networkModel(128000, 1200000, 8000000, 64*1024*1024);
    GenerateTilingCode();
    return 0;
}
