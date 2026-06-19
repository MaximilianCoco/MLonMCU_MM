#include <stdint.h>
#include <stdio.h>
#include "AutoTilerLib.h"
#include "CNN_Generators_SQ8.h"
#include "CNN_Generators.h"

#include "CNN_Copy_Generators.h"

void load_expressions_kernels() {
}





void model_int8_qdqModel(unsigned int L1Memory, unsigned int L2Memory, unsigned int L3Memory, unsigned int L3Flash)
{
    KernelOper_T Cop = KOP_CONV;

    // SetKernelOpts(KER_OPT_NONE, KER_OPT_BUFFER_PROMOTE);
    SetSymbolDynamics();

    SetUsedFilesNames(0, 5, "at_api.h", "model_int8_qdq.h", "CNN_BasicKernels_SQ8.h", "CNN_BasicKernels.h", "Expression_Kernels.h");
    SetGeneratedFilesNames("model_int8_qdqKernels.c", "model_int8_qdqKernels.h");
    AT_SetGraphCtrl(AT_GRAPH_MONITOR_CYCLES, AT_OPT_ON);
    AT_SetGraphCtrl(AT_GRAPH_PRODUCE_NODE_NAMES, AT_OPT_ON);
    AT_SetGraphCtrl(AT_GRAPH_PRODUCE_OPERINFOS, AT_OPT_ON);

    SetMemoryDeviceInfos(4,
        AT_MEM_L1, L1Memory, "model_int8_qdq_L1_Memory", 0, 0,
        AT_MEM_L2, L2Memory, "model_int8_qdq_L2_Memory", 0, 1,
        AT_MEM_L3_DEFAULTRAM, L3Memory, "model_int8_qdq_L3_Memory", 0, 0,
        AT_MEM_L3_DEFAULTFLASH, L3Flash, "model_int8_qdq_L3_Flash", "model_int8_qdq_L3_Flash_Const.dat", 0
    );

    LoadCNN_SQ8_Library();
    LoadCNNLibrary();
    load_expressions_kernels();

    CNN_GenControl_T gen_ctrl_S4__net_net_0_Conv;
    CNN_InitGenCtrl(&gen_ctrl_S4__net_net_0_Conv);
    CNN_SetGenCtrl(&gen_ctrl_S4__net_net_0_Conv, "INPUT_DATASIZE", AT_OPT_VAL(1));
    CNN_SetGenCtrl(&gen_ctrl_S4__net_net_0_Conv, "OUTPUT_DATASIZE", AT_OPT_VAL(1));
    // generator for _net_net_0_Conv
    CNN_ConvolutionPoolAct_SQ8("S4__net_net_0_Conv", &gen_ctrl_S4__net_net_0_Conv,
                               4, 1,
                               3, 9, 224, 224,
                               KOP_CONV, 3, 3, 1, 1, 1, 1, 1,
                               KOP_NONE, 0, 0, 0, 0, 0, 0, 0,
                               KOP_NONE);
    
    CNN_GenControl_T gen_ctrl_S9__net_net_2_Conv;
    CNN_InitGenCtrl(&gen_ctrl_S9__net_net_2_Conv);
    CNN_SetGenCtrl(&gen_ctrl_S9__net_net_2_Conv, "INPUT_DATASIZE", AT_OPT_VAL(1));
    CNN_SetGenCtrl(&gen_ctrl_S9__net_net_2_Conv, "OUTPUT_DATASIZE", AT_OPT_VAL(1));
    // generator for _net_net_2_Conv
    CNN_ConvolutionPoolAct_SQ8("S9__net_net_2_Conv", &gen_ctrl_S9__net_net_2_Conv,
                               4, 1,
                               9, 19, 224, 224,
                               KOP_CONV, 3, 3, 1, 1, 2, 2, 1,
                               KOP_NONE, 0, 0, 0, 0, 0, 0, 0,
                               KOP_NONE);
    
    CNN_GenControl_T gen_ctrl_S14__net_net_4_Conv;
    CNN_InitGenCtrl(&gen_ctrl_S14__net_net_4_Conv);
    CNN_SetGenCtrl(&gen_ctrl_S14__net_net_4_Conv, "INPUT_DATASIZE", AT_OPT_VAL(1));
    CNN_SetGenCtrl(&gen_ctrl_S14__net_net_4_Conv, "OUTPUT_DATASIZE", AT_OPT_VAL(1));
    // generator for _net_net_4_Conv
    CNN_ConvolutionPoolAct_SQ8("S14__net_net_4_Conv", &gen_ctrl_S14__net_net_4_Conv,
                               4, 1,
                               19, 38, 112, 112,
                               KOP_CONV, 3, 3, 1, 1, 2, 2, 1,
                               KOP_NONE, 0, 0, 0, 0, 0, 0, 0,
                               KOP_NONE);
    
    CNN_GenControl_T gen_ctrl_S19__net_net_6_Conv;
    CNN_InitGenCtrl(&gen_ctrl_S19__net_net_6_Conv);
    CNN_SetGenCtrl(&gen_ctrl_S19__net_net_6_Conv, "INPUT_DATASIZE", AT_OPT_VAL(1));
    CNN_SetGenCtrl(&gen_ctrl_S19__net_net_6_Conv, "OUTPUT_DATASIZE", AT_OPT_VAL(1));
    // generator for _net_net_6_Conv
    CNN_ConvolutionPoolAct_SQ8("S19__net_net_6_Conv", &gen_ctrl_S19__net_net_6_Conv,
                               4, 1,
                               38, 76, 56, 56,
                               KOP_CONV, 3, 3, 1, 1, 2, 2, 1,
                               KOP_NONE, 0, 0, 0, 0, 0, 0, 0,
                               KOP_NONE);
    
    CNN_GenControl_T gen_ctrl_S24__net_net_8_Conv;
    CNN_InitGenCtrl(&gen_ctrl_S24__net_net_8_Conv);
    CNN_SetGenCtrl(&gen_ctrl_S24__net_net_8_Conv, "INPUT_DATASIZE", AT_OPT_VAL(1));
    CNN_SetGenCtrl(&gen_ctrl_S24__net_net_8_Conv, "OUTPUT_DATASIZE", AT_OPT_VAL(1));
    // generator for _net_net_8_Conv
    CNN_ConvolutionPoolAct_SQ8("S24__net_net_8_Conv", &gen_ctrl_S24__net_net_8_Conv,
                               4, 1,
                               76, 76, 28, 28,
                               KOP_CONV, 3, 3, 1, 1, 1, 1, 1,
                               KOP_NONE, 0, 0, 0, 0, 0, 0, 0,
                               KOP_NONE);
    

#define GRAPH
#ifdef GRAPH
    CreateGraph("model_int8_qdqCNN",
        /* Arguments either passed or globals */
            CArgs(27,
                TCArgInfo("signed char * __restrict__", "Input_1", ARG_SCOPE_ARG, ARG_DIR_IN, AT_MEM_L2, AT_MEM_L2, 0),
                TCArgInfo("signed char * __restrict__", "_net_net_0_conv_weights", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("_net_net_0_conv_weights.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed int * __restrict__", "Constant_net_0_bias_quantized", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("Constant_net_0_bias_quantized.tensor", 1, 1, 32, 0)),
                TCArgInfo("unsigned char * __restrict__", "S4_Mul_scale", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S4_Mul_scale.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed char * __restrict__", "S4_Mul_shift", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S4_Mul_shift.tensor", 1, 1, 8, 0)),
                // no activation BIASN: 0 PRENORM: 0
                TCArgInfo("signed char * __restrict__", "S4_Infos", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S4_Infos.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed char * __restrict__", "_net_net_2_conv_weights", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("_net_net_2_conv_weights.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed int * __restrict__", "Constant_net_2_bias_quantized", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("Constant_net_2_bias_quantized.tensor", 1, 1, 32, 0)),
                TCArgInfo("unsigned char * __restrict__", "S9_Mul_scale", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S9_Mul_scale.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed char * __restrict__", "S9_Mul_shift", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S9_Mul_shift.tensor", 1, 1, 8, 0)),
                // no activation BIASN: 0 PRENORM: 0
                TCArgInfo("signed char * __restrict__", "S9_Infos", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S9_Infos.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed char * __restrict__", "_net_net_4_conv_weights", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("_net_net_4_conv_weights.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed int * __restrict__", "Constant_net_4_bias_quantized", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("Constant_net_4_bias_quantized.tensor", 1, 1, 32, 0)),
                TCArgInfo("unsigned char * __restrict__", "S14_Mul_scale", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S14_Mul_scale.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed char * __restrict__", "S14_Mul_shift", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S14_Mul_shift.tensor", 1, 1, 8, 0)),
                // no activation BIASN: 0 PRENORM: 0
                TCArgInfo("signed char * __restrict__", "S14_Infos", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S14_Infos.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed char * __restrict__", "_net_net_6_conv_weights", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("_net_net_6_conv_weights.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed int * __restrict__", "Constant_net_6_bias_quantized", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("Constant_net_6_bias_quantized.tensor", 1, 1, 32, 0)),
                TCArgInfo("unsigned char * __restrict__", "S19_Mul_scale", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S19_Mul_scale.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed char * __restrict__", "S19_Mul_shift", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S19_Mul_shift.tensor", 1, 1, 8, 0)),
                // no activation BIASN: 0 PRENORM: 0
                TCArgInfo("signed char * __restrict__", "S19_Infos", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S19_Infos.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed char * __restrict__", "_net_net_8_conv_weights", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("_net_net_8_conv_weights.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed int * __restrict__", "Constant_net_8_bias_quantized", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("Constant_net_8_bias_quantized.tensor", 1, 1, 32, 0)),
                TCArgInfo("unsigned char * __restrict__", "S24_Mul_scale", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S24_Mul_scale.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed char * __restrict__", "S24_Mul_shift", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S24_Mul_shift.tensor", 1, 1, 8, 0)),
                // no activation BIASN: 0 PRENORM: 0
                TCArgInfo("signed char * __restrict__", "S24_Infos", ARG_SCOPE_GLOBAL, ARG_DIR_CONSTIN, AT_MEM_L3_DEFAULTFLASH, AT_MEM_UNDEF, ConstInfo("S24_Infos.tensor", 1, 1, 8, 0)),
                TCArgInfo("signed char * __restrict__", "Output_1", ARG_SCOPE_ARG, ARG_DIR_OUT, AT_MEM_L2, AT_MEM_L2, 0)
            ),
        /* Locals, allocated dynamically */
        CArgs(4,
            TCArgInfo("signed char * __restrict__", "S4_Output", ARG_SCOPE_LOCAL, ARG_DIR_INOUT, AT_MEM_UNDEF, AT_MEM_UNDEF, 0),
            TCArgInfo("signed char * __restrict__", "S9_Output", ARG_SCOPE_LOCAL, ARG_DIR_INOUT, AT_MEM_UNDEF, AT_MEM_UNDEF, 0),
            TCArgInfo("signed char * __restrict__", "S14_Output", ARG_SCOPE_LOCAL, ARG_DIR_INOUT, AT_MEM_UNDEF, AT_MEM_UNDEF, 0),
            TCArgInfo("signed char * __restrict__", "S19_Output", ARG_SCOPE_LOCAL, ARG_DIR_INOUT, AT_MEM_UNDEF, AT_MEM_UNDEF, 0)
        )
    );



    // Node S4__net_net_0_Conv inq -2.60<(i8-0.00)*0.02034233<2.58 forced weightsq chan<(i8-0.00)*chan<chan outq -2.45<(i8-0.00)*0.01915942<2.43 forced biasesq chan<(i32-0.00)*chan<chan
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
    // Node S9__net_net_2_Conv inq -2.45<(i8-0.00)*0.01915942<2.43 forced weightsq chan<(i8-0.00)*chan<chan outq -1.03<(i8-0.00)*0.00802905<1.02 forced biasesq chan<(i32-0.00)*chan<chan
    AddNode("S9__net_net_2_Conv",
        Bindings(7,
            GNodeArg(GNA_IN, "S4_Output", 0),
            GNodeArg(GNA_IN, "_net_net_2_conv_weights", 0),
            GNodeArg(GNA_IN, "Constant_net_2_bias_quantized", 0),
            GNodeArg(GNA_OUT, "S9_Output", 0),
            GNodeArg(GNA_IN, "S9_Mul_scale", 0),
            GNodeArg(GNA_IN, "S9_Mul_shift", 0),
            GNodeArg(GNA_IN, "S9_Infos", 0)
        )
    );
    // Node S14__net_net_4_Conv inq -1.03<(i8-0.00)*0.00802905<1.02 forced weightsq chan<(i8-0.00)*chan<chan outq -0.18<(i8-0.00)*0.00139503<0.18 forced biasesq chan<(i32-0.00)*chan<chan
    AddNode("S14__net_net_4_Conv",
        Bindings(7,
            GNodeArg(GNA_IN, "S9_Output", 0),
            GNodeArg(GNA_IN, "_net_net_4_conv_weights", 0),
            GNodeArg(GNA_IN, "Constant_net_4_bias_quantized", 0),
            GNodeArg(GNA_OUT, "S14_Output", 0),
            GNodeArg(GNA_IN, "S14_Mul_scale", 0),
            GNodeArg(GNA_IN, "S14_Mul_shift", 0),
            GNodeArg(GNA_IN, "S14_Infos", 0)
        )
    );
    // Node S19__net_net_6_Conv inq -0.18<(i8-0.00)*0.00139503<0.18 forced weightsq chan<(i8-0.00)*chan<chan outq -0.10<(i8-0.00)*0.00078817<0.10 forced biasesq chan<(i32-0.00)*chan<chan
    AddNode("S19__net_net_6_Conv",
        Bindings(7,
            GNodeArg(GNA_IN, "S14_Output", 0),
            GNodeArg(GNA_IN, "_net_net_6_conv_weights", 0),
            GNodeArg(GNA_IN, "Constant_net_6_bias_quantized", 0),
            GNodeArg(GNA_OUT, "S19_Output", 0),
            GNodeArg(GNA_IN, "S19_Mul_scale", 0),
            GNodeArg(GNA_IN, "S19_Mul_shift", 0),
            GNodeArg(GNA_IN, "S19_Infos", 0)
        )
    );
    // Node S24__net_net_8_Conv inq -0.10<(i8-0.00)*0.00078817<0.10 forced weightsq chan<(i8-0.00)*chan<chan outq -0.01<(i8-0.00)*0.00009256<0.01 forced biasesq chan<(i32-0.00)*chan<chan
    AddNode("S24__net_net_8_Conv",
        Bindings(7,
            GNodeArg(GNA_IN, "S19_Output", 0),
            GNodeArg(GNA_IN, "_net_net_8_conv_weights", 0),
            GNodeArg(GNA_IN, "Constant_net_8_bias_quantized", 0),
            GNodeArg(GNA_OUT, "Output_1", 0),
            GNodeArg(GNA_IN, "S24_Mul_scale", 0),
            GNodeArg(GNA_IN, "S24_Mul_shift", 0),
            GNodeArg(GNA_IN, "S24_Infos", 0)
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
    model_int8_qdqModel(128000, 1200000, 8000000, 64*1024*1024);
    GenerateTilingCode();
    return 0;
}
