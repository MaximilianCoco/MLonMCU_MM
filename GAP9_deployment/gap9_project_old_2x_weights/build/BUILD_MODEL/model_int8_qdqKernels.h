#ifndef __MODEL_INT8_QDQKERNEL_H__
#define __MODEL_INT8_QDQKERNEL_H__

#include "AutoTilerLibTypes.h"
#include "at_api.h"
#include "model_int8_qdq.h"
#include "CNN_BasicKernels_SQ8.h"
#include "CNN_BasicKernels.h"
#include "Expression_Kernels.h"
#define _model_int8_qdq_L1_Memory_SIZE 114328
#define _model_int8_qdq_L2_Memory_SIZE 87660
#define _model_int8_qdq_L2_Memory_Dyn_SIZE 689920
extern char *model_int8_qdq_L1_Memory; /* Size given for generation: 115712 bytes, used: 114328 bytes */
extern char *model_int8_qdq_L2_Memory; /* Size used for generation (static): 87660 bytes */
extern char *model_int8_qdq_L2_Memory_Dyn; /* Size used for generation (dynamic): 689920 bytes */
extern void S4__net_net_0_Conv(
		signed char * __restrict__ In,
		signed char * __restrict__ Filter,
		int * __restrict__ Bias,
		signed char * __restrict__ Out,
		unsigned char * __restrict__ Scale,
		signed char * __restrict__ ScaleN,
		signed char * __restrict__ Infos);
extern void S7__net_net_2_Conv(
		signed char * __restrict__ In,
		signed char * __restrict__ Filter,
		int * __restrict__ Bias,
		signed char * __restrict__ Out,
		unsigned char * __restrict__ Scale,
		signed char * __restrict__ ScaleN,
		signed char * __restrict__ Infos);
extern void S10__net_net_4_Conv(
		signed char * __restrict__ In,
		signed char * __restrict__ Filter,
		int * __restrict__ Bias,
		signed char * __restrict__ Out,
		unsigned char * __restrict__ Scale,
		signed char * __restrict__ ScaleN,
		signed char * __restrict__ Infos);
extern void S13__net_net_6_Conv(
		signed char * __restrict__ In,
		signed char * __restrict__ Filter,
		int * __restrict__ Bias,
		signed char * __restrict__ Out,
		unsigned char * __restrict__ Scale,
		signed char * __restrict__ ScaleN,
		signed char * __restrict__ Infos);
extern void S16__net_net_8_Conv(
		signed char * __restrict__ In,
		signed char * __restrict__ Filter,
		int * __restrict__ Bias,
		signed char * __restrict__ Out,
		unsigned char * __restrict__ Scale,
		signed char * __restrict__ ScaleN,
		signed char * __restrict__ Infos);
extern int model_int8_qdqCNN_Construct();
extern void model_int8_qdqCNN_ConstructCluster();
extern int model_int8_qdqCNN_Destruct();
extern int model_int8_qdqCNN_Memory(AT_MEM_TYPE Which);
extern int model_int8_qdqCNN(
		signed char * __restrict__ Input_1,
		signed char * __restrict__ Output_1);
extern unsigned int AT_GraphPerf[6];
extern unsigned int AT_GraphPerf_CNN_Total;
extern char * AT_GraphNodeNames[6];
extern unsigned int AT_GraphOperInfosNames[6];
#endif
