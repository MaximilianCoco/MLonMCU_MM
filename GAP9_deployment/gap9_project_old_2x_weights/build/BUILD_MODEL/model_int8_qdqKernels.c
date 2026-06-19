#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wmaybe-uninitialized"
#include "model_int8_qdqKernels.h"
#ifdef __EMUL__
unsigned int __L3_Read, __L3_Write, __L2_Read, __L2_Write;
#endif
L1_CL_MEM AT_L1_POINTER model_int8_qdq_L1_Memory;
L2_MEM AT_L2_POINTER model_int8_qdq_L2_Memory;
L2_MEM AT_L2_POINTER model_int8_qdq_L2_Memory_Dyn;
static AT_DEFAULTFLASH_FS_T DefaultFlash;
void  S4__net_net_0_Conv(
		signed char * __restrict__ In,
		signed char * __restrict__ Filter,
		int * __restrict__ Bias,
		signed char * __restrict__ Out,
		unsigned char * __restrict__ Scale,
		signed char * __restrict__ ScaleN,
		signed char * __restrict__ Infos)

{
	/* Shared L1: 112060 bytes, L2 buffer: 0 bytes */
	/* Local variables used by this kernel */
	AT_L2_EVENT _DmaR_Evt1, *DmaR_Evt1 = &_DmaR_Evt1;
	AT_L2_EVENT _DmaR_Evt3, *DmaR_Evt3 = &_DmaR_Evt3;
	AT_L2_EVENT _DmaR_Evt2, *DmaR_Evt2 = &_DmaR_Evt2;
	AT_L2_EVENT _DmaW_Evt1, *DmaW_Evt1 = &_DmaW_Evt1;
	KerSetBias_SQ8_T S_KerArg0, *KerArg0 = &S_KerArg0;
	KerConv_SQ8_T S_KerArg1, *KerArg1 = &S_KerArg1;
	KerConvLinReduct_SQ8_T S_KerArg2, *KerArg2 = &S_KerArg2;

	/* Iteration space related variables */
	int D1Ind, D1Ind_Total=0, D1Ind_Last, D1Ind_NextLast;
	int T0Ind, T0Ind_Total=0, T0Ind_Last, T0Ind_NextLast;
	int D0Ind, D0Ind_Last;
	/* User kernel arguments related variables */
	unsigned int _N_In;
	unsigned int _SN_In;
	unsigned int _LN_In;
	unsigned int _N_Filter;
	unsigned int _SN_Filter;
	unsigned int _C_Out;
	unsigned int _SP_Out, _SC_Out;
	unsigned int _LP_Out, _LC_Out;
	/*============================= Ker Arg Iter Spaces =========================================
	User Kernel Iteration Space:
		[D1 Dim: Init: 9, Tiled: 2][Tile0 Dim: 25][D0 Dim: Init: 3, Tiled: 1]
	Ker Arg: In, Tiled Space: Tile0
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 25 logical tiles, 25 physical tiles
			@ 0 (Total Size: 150528 )[D0, [0 x 150528, 150528]][Tile0, 25:[224x10, 23:224x11, 224x9], 1]
		KerArgItSpace (User Kernel Iter Order):
			[Tile0, 25:[224x9], 1][D0, [0 x 150528, 150528]]
		Tile0: [0, 6720, 2240], Tile1: [1792, 7392, 2464], Tile2; [3808, 7392, 2464]
	Ker Arg: Bias, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 2 logical tiles, 1 physical tiles
			@ 14784 (Total Size: 36 )[D1, [1 x 32, 4]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 32, 4]]
		Tile0: [0, 36, 36], Tile1: [0, 36, 36], Tile2; [0, 36, 36]
	Ker Arg: Scale, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 2 logical tiles, 1 physical tiles
			@ 14820 (Total Size: 9 )[D1, [1 x 8, 1]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 8, 1]]
		Tile0: [0, 9, 9], Tile1: [0, 9, 9], Tile2; [0, 9, 9]
	Ker Arg: ScaleN, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 2 logical tiles, 1 physical tiles
			@ 14832 (Total Size: 9 )[D1, [1 x 8, 1]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 8, 1]]
		Tile0: [0, 9, 9], Tile1: [0, 9, 9], Tile2; [0, 9, 9]
	Ker Arg: Filter, Tiled Space: D1
		Min Pipe Depth: 0, Max Pipe Depth: 1
		KerArgItSpace: 2 logical tiles, 2 physical tiles
			@ 14844 (Total Size: 243 )[D1, [1 x 216, 27]][D0, [0 x 216, 216]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 216, 27]][D0, [0 x 216, 216]]
		Tile0: [0, 216, 216], Tile1: [216, 27, 27], Tile2; [0, 216, 216]
	Ker Arg: Out, Tiled Space: Tile0
		Min Pipe Depth: -1, Max Pipe Depth: 1
		KerArgItSpace: 50 logical tiles, 50 physical tiles
			@ 15276 (Total Size: 451584 )[D1, [1 x 401408, 50176]][Tile0, 25:[224x9, 23:224x9, 224x8], 1]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 401408, 50176]][Tile0, 25:[224x9, 23:224x9, 224x8], 1]
		Tile0: [0, 16128, 2016], Tile1: [2016, 16128, 2016], Tile2; [4032, 16128, 2016]
	Ker Arg: ConvOut, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 50 logical tiles, 1 physical tiles
			@ 47532 (Total Size: 1806336 )[D1, [1 x 1605632, 200704]][Tile0, 25:[224x9, 23:224x9, 224x8], 4]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 1605632, 200704]][Tile0, 25:[224x9, 23:224x9, 224x8], 4]
		Tile0: [0, 64512, 8064], Tile1: [0, 64512, 8064], Tile2; [0, 64512, 8064]
	Ker Arg: Infos, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 25 logical tiles, 1 physical tiles
			@ 112044 (Total Size: 16 )[Tile0, 25:[16x1, 23:16x1, 16x1], 1]
		KerArgItSpace (User Kernel Iter Order):
			[Tile0, 25:[16x1, 23:16x1, 16x1], 1]
		Tile0: [0, 16, 16], Tile1: [0, 16, 16], Tile2; [0, 16, 16]
	======================== End Ker Arg Iter Spaces =========================================*/
	/*=========================== Call Kernel, Invariant assignment =====================*/
	KerArg0->Out = (int * __restrict__) (model_int8_qdq_L1_Memory+47532);
	KerArg0->W = (unsigned short int) (224);
	KerArg1->W = (unsigned short int) (224);
	KerArg1->UsedW = (unsigned short int) (224);
	KerArg1->InFeatures = (unsigned short int) (3);
	KerArg1->TotalInFeatures = (unsigned short int) (3);
	KerArg1->Out = (int * __restrict__) (model_int8_qdq_L1_Memory+47532);
	KerArg1->ExplPad = (unsigned char) (0);
	KerArg2->In = (int *__restrict__) (model_int8_qdq_L1_Memory+47532);
	KerArg2->W = (unsigned short int) (224);
	KerArg2->Infos = (signed char *__restrict__) (model_int8_qdq_L1_Memory+112044);
	KerArg2->Extra = (void *) (0);
	/*================================= Read Tiles Prolog ===============================*/
	_C_Out=0; _SC_Out=16128; _LC_Out=2016;
	_SP_Out=0;
	AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) In+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+0+0), 6720, 50176, 2240, 0, DmaR_Evt1);
	_N_In=0;
	AT_L2_COPY(0, ((AT_L2_EXT_ADDR_TYPE) Filter+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+14844+0), 216, 0, DmaR_Evt2);
	_N_Filter=0;
	AT_L2_COPY(0, ((AT_L2_EXT_ADDR_TYPE) Bias+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+14784), 36, 0, DmaR_Evt3);
	AT_L2_COPY_MERGED(0, ((AT_L2_EXT_ADDR_TYPE) Infos+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+112044), 16, 0, 0);
	AT_L2_COPY_MERGED(0, ((AT_L2_EXT_ADDR_TYPE) Scale+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+14820), 9, 0, 0);
	AT_L2_COPY_MERGED(0, ((AT_L2_EXT_ADDR_TYPE) ScaleN+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+14832), 9, 0, 0);
	AT_L2_WAIT(0, DmaR_Evt3); /* Wait previous DMA read ScaleN */
	/*============================= End Read Tiles Prolog ===============================*/
	for (D1Ind=0; D1Ind<2; D1Ind++, D1Ind_Total++) { /* Iteration on D1 */
		int D1Ind_Last = (D1Ind==1), D1Ind_NextLast = ((D1Ind+1)==1);
		/*================================= Prepare Tiles ===================================*/
		_SN_Filter = 0;
		if (!(D1Ind_Last)) {
			_N_Filter = _N_Filter + (216); _SN_Filter = ((1)?27:216); 
		}
		/*============================= End Prepare Tiles ===================================*/
		/*================================= Read Tiles ======================================*/
		AT_L2_WAIT(0, DmaR_Evt2); /* Wait previous DMA read Filter */
		if (_SN_Filter) {
			AT_L2_COPY(0, ((AT_L2_EXT_ADDR_TYPE) Filter+_N_Filter), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+14844+216*((D1Ind_Total+1)%2)),
					1*(_SN_Filter), 0, DmaR_Evt2);
		}
		/*============================= End Read Tiles ======================================*/
		for (T0Ind=0; T0Ind<25; T0Ind++, T0Ind_Total++) { /* Iteration on Tile0 */
			int T0Ind_Last = (T0Ind==24), T0Ind_NextLast = ((T0Ind+1)==24);
			/*================================= Prepare Tiles ===================================*/
			_SN_In = 0;
			if (!(T0Ind_Last)) {
				_N_In = _N_In + (2016-(224*(T0Ind==0))); _LN_In = ((T0Ind_NextLast)?2016:2464); _SN_In = (3*_LN_In); 
			} else if (!(D1Ind_Last)) {
				_N_In = _N_In + (-48160); _LN_In = (2240); _SN_In = (3*_LN_In); 
			}
			/*============================= End Prepare Tiles ===================================*/
			/*================================= Read Tiles ======================================*/
			AT_L2_WAIT(0, DmaR_Evt1); /* Wait previous DMA read In */
			if (_SN_In) {
				AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) In+_N_In), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+0+7392*((T0Ind_Total+1)%2)),
						1*(_SN_In), 50176, _LN_In, 0, DmaR_Evt1);
			}
			/*============================= End Read Tiles ======================================*/
			/*====================== Call Kernel LOC_D0_PROLOG =========================*/
			KerArg0->H = (unsigned short int) (T0Ind_Last?8:9);
			KerArg0->Feat = (unsigned short int) ((D1Ind_Last)?1:8);
			KerArg0->Bias = (void * __restrict__) (model_int8_qdq_L1_Memory+14784+((D1Ind)*32));
			KerArg0->NormBias = (unsigned char) (((char *)(model_int8_qdq_L1_Memory+112044))[8]);
			AT_FORK(gap_ncore(), (void *) KerParSetBiasB32_SQ8, (void *) KerArg0);
			__CALL(KerParSetBiasB32_SQ8, KerArg0);
			{ /* Single iteration on D0 */
				int D0Ind_Last = 1;
				/*====================== Call Kernel LOC_D0 =========================*/
				KerArg1->In = (signed char * __restrict__) (model_int8_qdq_L1_Memory+0+7392*((T0Ind_Total)%2));
				KerArg1->H = (unsigned short int) (((T0Ind_Last)?9:11)-1*(T0Ind==0));
				KerArg1->UsedH = (unsigned short int) (((T0Ind_Last)?9:11)-1*(T0Ind==0));
				KerArg1->OutFeatures = (unsigned short int) ((D1Ind_Last)?1:8);
				KerArg1->Filter = (signed char * __restrict__) (model_int8_qdq_L1_Memory+14844+216*((D1Ind_Total)%2));
				KerArg1->Pad = (v4u) ((v4u){1,1,1*(T0Ind==0),1*(T0Ind_Last)});
				AT_FORK(gap_ncore(), (void *) KerParConv3x3Stride1_SQ8, (void *) KerArg1);
				__CALL(KerParConv3x3Stride1_SQ8, KerArg1);
			} /* End iteration on D0 */
			/*====================== Call Kernel LOC_D0_EPILOG =========================*/
			KerArg2->Out = (void *__restrict__) (model_int8_qdq_L1_Memory+15276+16128*((T0Ind_Total)%2));
			KerArg2->Feat = (unsigned short int) ((D1Ind_Last)?1:8);
			KerArg2->H = (unsigned short int) (T0Ind_Last?8:9);
			KerArg2->Scale = (unsigned char *__restrict__) (model_int8_qdq_L1_Memory+14820+((D1Ind)*8));
			KerArg2->ScaleN = (unsigned char *__restrict__) (model_int8_qdq_L1_Memory+14832+((D1Ind)*8));
			AT_FORK(gap_ncore(), (void *) KerParReduct_CC_SQ8, (void *) KerArg2);
			__CALL(KerParReduct_CC_SQ8, KerArg2);
			/*================================= Write Tiles =====================================*/
			if (_SP_Out) AT_L2_WAIT(0, DmaW_Evt1); /* Wait previous DMA write Out */
			AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) Out+_C_Out), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+15276+16128*((T0Ind_Total)%2)),
					_SC_Out, 50176, _LC_Out, 1, DmaW_Evt1);
			/*============================= End Write Tiles =====================================*/
			/*================================= Update Arg Pipeline =============================*/
			_SP_Out = _SC_Out;_LP_Out = _LC_Out;
			/*============================= End Update Arg Pipeline =============================*/
			/*================================= Prepare Tiles ===================================*/
			_SC_Out = 0;
			if (!(T0Ind_Last)) {
				_C_Out = _C_Out + (2016); _LC_Out = ((T0Ind_NextLast)?1792:2016); _SC_Out = (((D1Ind_Last)?1:8)*_LC_Out); 
			} else if (!(D1Ind_Last)) {
				_C_Out = _C_Out + (401408)+(-48384); _LC_Out = (2016); _SC_Out = (((1)?1:8)*_LC_Out); 
			}
			/*============================= End Prepare Tiles ===================================*/
		} /* End iteration on Tile0 */
		/*================================= Update Arg Pipeline =============================*/
		/*============================= End Update Arg Pipeline =============================*/
	} /* End iteration on D1 */
	/*================================ Write Tiles Epilog ===============================*/
	AT_L2_WAIT(0, DmaW_Evt1); /* Wait previous DMA write Out */
	/*============================ End Write Tiles Epilog ===============================*/
}
void  S7__net_net_2_Conv(
		signed char * __restrict__ In,
		signed char * __restrict__ Filter,
		int * __restrict__ Bias,
		signed char * __restrict__ Out,
		unsigned char * __restrict__ Scale,
		signed char * __restrict__ ScaleN,
		signed char * __restrict__ Infos)

{
	/* Shared L1: 104868 bytes, L2 buffer: 0 bytes */
	/* Local variables used by this kernel */
	AT_L2_EVENT _DmaW_Evt1, *DmaW_Evt1 = &_DmaW_Evt1;
	AT_L2_EVENT _DmaR_Evt3, *DmaR_Evt3 = &_DmaR_Evt3;
	AT_L2_EVENT _DmaR_Evt2, *DmaR_Evt2 = &_DmaR_Evt2;
	AT_L2_EVENT _DmaR_Evt1, *DmaR_Evt1 = &_DmaR_Evt1;
	KerSetBias_SQ8_T S_KerArg0, *KerArg0 = &S_KerArg0;
	KerConv_SQ8_T S_KerArg1, *KerArg1 = &S_KerArg1;
	KerConvLinReduct_SQ8_T S_KerArg2, *KerArg2 = &S_KerArg2;

	/* Iteration space related variables */
	int D1Ind, D1Ind_Total=0, D1Ind_Last, D1Ind_NextLast;
	int T0Ind, T0Ind_Total=0, T0Ind_Last, T0Ind_NextLast;
	int D0Ind, D0Ind_Total=0, D0Ind_Last, D0Ind_NextLast;
	/* User kernel arguments related variables */
	unsigned int _C_Out;
	unsigned int _SP_Out, _SC_Out;
	unsigned int _LP_Out, _LC_Out;
	unsigned int _N_Filter;
	unsigned int _SN_Filter;
	unsigned int _LN_Filter;
	unsigned int _N_In;
	unsigned int _SN_In;
	unsigned int _LN_In;
	/*============================= Ker Arg Iter Spaces =========================================
	User Kernel Iteration Space:
		[D1 Dim: Init: 19, Tiled: 2][Tile0 Dim: 16][D0 Dim: Init: 9, Tiled: 3]
	Ker Arg: Out, Tiled Space: Tile0
		Min Pipe Depth: -1, Max Pipe Depth: 1
		KerArgItSpace: 32 logical tiles, 32 physical tiles
			@ 29588 (Total Size: 238336 )[D1, [1 x 200704, 37632]][Tile0, 16:[112x7, 14:112x7, 112x7], 1]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 200704, 37632]][Tile0, 16:[112x7, 14:112x7, 112x7], 1]
		Tile0: [0, 12544, 784], Tile1: [784, 12544, 784], Tile2; [1568, 12544, 784]
	Ker Arg: Bias, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 2 logical tiles, 1 physical tiles
			@ 26880 (Total Size: 76 )[D1, [1 x 64, 12]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 64, 12]]
		Tile0: [0, 76, 76], Tile1: [0, 76, 76], Tile2; [0, 76, 76]
	Ker Arg: Scale, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 2 logical tiles, 1 physical tiles
			@ 26956 (Total Size: 19 )[D1, [1 x 16, 3]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 16, 3]]
		Tile0: [0, 19, 19], Tile1: [0, 19, 19], Tile2; [0, 19, 19]
	Ker Arg: ScaleN, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 2 logical tiles, 1 physical tiles
			@ 26976 (Total Size: 19 )[D1, [1 x 16, 3]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 16, 3]]
		Tile0: [0, 19, 19], Tile1: [0, 19, 19], Tile2; [0, 19, 19]
	Ker Arg: Filter, Tiled Space: D1
		Min Pipe Depth: 0, Max Pipe Depth: 1
		KerArgItSpace: 6 logical tiles, 2 physical tiles
			@ 26996 (Total Size: 1539 )[D1, [1 x 1296, 243]][D0, [2 x 576, 144]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 1296, 243]][D0, [2 x 576, 144]]
		Tile0: [0, 1296, 81], Tile1: [1296, 243, 81], Tile2; [0, 1296, 81]
	Ker Arg: In, Tiled Space: Tile0
		Min Pipe Depth: 0, Max Pipe Depth: 1
		KerArgItSpace: 48 logical tiles, 48 physical tiles
			@ 0 (Total Size: 451584 )[D0, [2 x 200704, 50176]][Tile0, 16:[224x14, 14:224x15, 224x15], 1]
		KerArgItSpace (User Kernel Iter Order):
			[Tile0, 16:[224x14, 1:224x15, 224x15], 1][D0, [2 x 200704, 50176]]
		Tile0: [0, 12544, 3136], Tile1: [200704, 12544, 3136], Tile2; [401408, 3136, 3136]
	Ker Arg: ConvOut, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 32 logical tiles, 1 physical tiles
			@ 54676 (Total Size: 953344 )[D1, [1 x 802816, 150528]][Tile0, 16:[112x7, 14:112x7, 112x7], 4]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 802816, 150528]][Tile0, 16:[112x7, 14:112x7, 112x7], 4]
		Tile0: [0, 50176, 3136], Tile1: [0, 50176, 3136], Tile2; [0, 50176, 3136]
	Ker Arg: Infos, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 16 logical tiles, 1 physical tiles
			@ 104852 (Total Size: 16 )[Tile0, 16:[16x1, 14:16x1, 16x1], 1]
		KerArgItSpace (User Kernel Iter Order):
			[Tile0, 16:[16x1, 14:16x1, 16x1], 1]
		Tile0: [0, 16, 16], Tile1: [0, 16, 16], Tile2; [0, 16, 16]
	======================== End Ker Arg Iter Spaces =========================================*/
	/*=========================== Call Kernel, Invariant assignment =====================*/
	KerArg0->Out = (int * __restrict__) (model_int8_qdq_L1_Memory+54676);
	KerArg0->W = (unsigned short int) (112);
	KerArg0->H = (unsigned short int) (7);
	KerArg1->W = (unsigned short int) (224);
	KerArg1->UsedW = (unsigned short int) (224);
	KerArg1->TotalInFeatures = (unsigned short int) (9);
	KerArg1->Out = (int * __restrict__) (model_int8_qdq_L1_Memory+54676);
	KerArg1->ExplPad = (unsigned char) (0);
	KerArg2->In = (int *__restrict__) (model_int8_qdq_L1_Memory+54676);
	KerArg2->W = (unsigned short int) (112);
	KerArg2->H = (unsigned short int) (7);
	KerArg2->Infos = (signed char *__restrict__) (model_int8_qdq_L1_Memory+104852);
	KerArg2->Extra = (void *) (0);
	/*================================= Read Tiles Prolog ===============================*/
	AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) In+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+0+0), 12544, 50176, 3136, 0, DmaR_Evt1);
	_N_In=0;
	_C_Out=0; _SC_Out=12544; _LC_Out=784;
	_SP_Out=0;
	AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) Filter+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+26996+0), 1296, 81, 81, 0, DmaR_Evt2);
	_N_Filter=0;
	AT_L2_COPY(0, ((AT_L2_EXT_ADDR_TYPE) Bias+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+26880), 76, 0, DmaR_Evt3);
	AT_L2_COPY_MERGED(0, ((AT_L2_EXT_ADDR_TYPE) Scale+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+26956), 19, 0, 0);
	AT_L2_COPY_MERGED(0, ((AT_L2_EXT_ADDR_TYPE) ScaleN+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+26976), 19, 0, 0);
	AT_L2_COPY_MERGED(0, ((AT_L2_EXT_ADDR_TYPE) Infos+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+104852), 16, 0, 0);
	AT_L2_WAIT(0, DmaR_Evt3); /* Wait previous DMA read Infos */
	/*============================= End Read Tiles Prolog ===============================*/
	for (D1Ind=0; D1Ind<2; D1Ind++, D1Ind_Total++) { /* Iteration on D1 */
		int D1Ind_Last = (D1Ind==1), D1Ind_NextLast = ((D1Ind+1)==1);
		/*================================= Prepare Tiles ===================================*/
		_SN_Filter = 0;
		if (!(D1Ind_Last)) {
			_N_Filter = _N_Filter + (1296); _LN_Filter = (81); _SN_Filter = ((1)?243:1296); 
		}
		/*============================= End Prepare Tiles ===================================*/
		/*================================= Read Tiles ======================================*/
		AT_L2_WAIT(0, DmaR_Evt2); /* Wait previous DMA read Filter */
		if (_SN_Filter) {
			AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) Filter+_N_Filter), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+26996+1296*((D1Ind_Total+1)%2)),
					1*(_SN_Filter), 81, _LN_Filter, 0, DmaR_Evt2);
		}
		/*============================= End Read Tiles ======================================*/
		for (T0Ind=0; T0Ind<16; T0Ind++, T0Ind_Total++) { /* Iteration on Tile0 */
			int T0Ind_Last = (T0Ind==15), T0Ind_NextLast = ((T0Ind+1)==15);
			/*====================== Call Kernel LOC_D0_PROLOG =========================*/
			KerArg0->Feat = (unsigned short int) ((D1Ind_Last)?3:16);
			KerArg0->Bias = (void * __restrict__) (model_int8_qdq_L1_Memory+26880+((D1Ind)*64));
			KerArg0->NormBias = (unsigned char) (((char *)(model_int8_qdq_L1_Memory+104852))[8]);
			AT_FORK(gap_ncore(), (void *) KerParSetBiasB32_SQ8, (void *) KerArg0);
			__CALL(KerParSetBiasB32_SQ8, KerArg0);
			for (D0Ind=0; D0Ind<3; D0Ind++, D0Ind_Total++) { /* Iteration on D0 */
				int D0Ind_Last = (D0Ind==2), D0Ind_NextLast = ((D0Ind+1)==2);
				/*================================= Prepare Tiles ===================================*/
				_SN_In = 0;
				if (!(D0Ind_Last)) {
					_N_In = _N_In + (200704); _LN_In = ((T0Ind_Last)?3360:(3360-224*(T0Ind==0))); _SN_In = (((D0Ind_NextLast)?1:4)*_LN_In); 
				} else if (!(T0Ind_Last)) {
					_N_In = _N_In + (3136-(224*(T0Ind==0)))+(-401408); _LN_In = ((T0Ind_NextLast)?3360:3360); _SN_In = (4*_LN_In); 
				} else if (!(D1Ind_Last)) {
					_N_In = _N_In + (-46816)+(-401408); _LN_In = (3136); _SN_In = (4*_LN_In); 
				}
				/*============================= End Prepare Tiles ===================================*/
				/*================================= Read Tiles ======================================*/
				AT_L2_WAIT(0, DmaR_Evt1); /* Wait previous DMA read In */
				if (_SN_In) {
					AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) In+_N_In), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+0+13440*((D0Ind_Total+1)%2)),
							1*(_SN_In), 50176, _LN_In, 0, DmaR_Evt1);
				}
				/*============================= End Read Tiles ======================================*/
				/*====================== Call Kernel LOC_D0 =========================*/
				KerArg1->In = (signed char * __restrict__) (model_int8_qdq_L1_Memory+0+13440*((D0Ind_Total)%2));
				KerArg1->H = (unsigned short int) (15-1*(T0Ind==0)-0*(T0Ind_Last));
				KerArg1->UsedH = (unsigned short int) (15-1*(T0Ind==0)-0*(T0Ind_Last));
				KerArg1->InFeatures = (unsigned short int) ((D0Ind_Last)?1:4);
				KerArg1->OutFeatures = (unsigned short int) ((D1Ind_Last)?3:16);
				KerArg1->Filter = (signed char * __restrict__) (model_int8_qdq_L1_Memory+26996+((D0Ind)*36)+1296*((D1Ind_Total)%2));
				KerArg1->Pad = (v4u) ((v4u){1,0,1*(T0Ind==0),0*(T0Ind_Last)});
				AT_FORK(gap_ncore(), (void *) KerParConv3x3Stride2_SQ8, (void *) KerArg1);
				__CALL(KerParConv3x3Stride2_SQ8, KerArg1);
				/*================================= Update Arg Pipeline =============================*/
				/*============================= End Update Arg Pipeline =============================*/
			} /* End iteration on D0 */
			/*====================== Call Kernel LOC_D0_EPILOG =========================*/
			KerArg2->Out = (void *__restrict__) (model_int8_qdq_L1_Memory+29588+12544*((T0Ind_Total)%2));
			KerArg2->Feat = (unsigned short int) ((D1Ind_Last)?3:16);
			KerArg2->Scale = (unsigned char *__restrict__) (model_int8_qdq_L1_Memory+26956+((D1Ind)*16));
			KerArg2->ScaleN = (unsigned char *__restrict__) (model_int8_qdq_L1_Memory+26976+((D1Ind)*16));
			AT_FORK(gap_ncore(), (void *) KerParReduct_CC_SQ8, (void *) KerArg2);
			__CALL(KerParReduct_CC_SQ8, KerArg2);
			/*================================= Write Tiles =====================================*/
			if (_SP_Out) AT_L2_WAIT(0, DmaW_Evt1); /* Wait previous DMA write Out */
			AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) Out+_C_Out), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+29588+12544*((T0Ind_Total)%2)),
					_SC_Out, 12544, _LC_Out, 1, DmaW_Evt1);
			/*============================= End Write Tiles =====================================*/
			/*================================= Update Arg Pipeline =============================*/
			_SP_Out = _SC_Out;_LP_Out = _LC_Out;
			/*============================= End Update Arg Pipeline =============================*/
			/*================================= Prepare Tiles ===================================*/
			_SC_Out = 0;
			if (!(T0Ind_Last)) {
				_C_Out = _C_Out + (784); _LC_Out = (784); _SC_Out = (((D1Ind_Last)?3:16)*_LC_Out); 
			} else if (!(D1Ind_Last)) {
				_C_Out = _C_Out + (200704)+(-11760); _LC_Out = (784); _SC_Out = (((1)?3:16)*_LC_Out); 
			}
			/*============================= End Prepare Tiles ===================================*/
		} /* End iteration on Tile0 */
		/*================================= Update Arg Pipeline =============================*/
		/*============================= End Update Arg Pipeline =============================*/
	} /* End iteration on D1 */
	/*================================ Write Tiles Epilog ===============================*/
	AT_L2_WAIT(0, DmaW_Evt1); /* Wait previous DMA write Out */
	/*============================ End Write Tiles Epilog ===============================*/
}
void  S10__net_net_4_Conv(
		signed char * __restrict__ In,
		signed char * __restrict__ Filter,
		int * __restrict__ Bias,
		signed char * __restrict__ Out,
		unsigned char * __restrict__ Scale,
		signed char * __restrict__ ScaleN,
		signed char * __restrict__ Infos)

{
	/* Shared L1: 107912 bytes, L2 buffer: 0 bytes */
	/* Local variables used by this kernel */
	AT_L2_EVENT _DmaW_Evt1, *DmaW_Evt1 = &_DmaW_Evt1;
	AT_L2_EVENT _DmaR_Evt3, *DmaR_Evt3 = &_DmaR_Evt3;
	AT_L2_EVENT _DmaR_Evt2, *DmaR_Evt2 = &_DmaR_Evt2;
	AT_L2_EVENT _DmaR_Evt1, *DmaR_Evt1 = &_DmaR_Evt1;
	KerSetBias_SQ8_T S_KerArg0, *KerArg0 = &S_KerArg0;
	KerConv_SQ8_T S_KerArg1, *KerArg1 = &S_KerArg1;
	KerConvLinReduct_SQ8_T S_KerArg2, *KerArg2 = &S_KerArg2;

	/* Iteration space related variables */
	int D1Ind, D1Ind_Total=0, D1Ind_Last, D1Ind_NextLast;
	int T0Ind, T0Ind_Total=0, T0Ind_Last, T0Ind_NextLast;
	int D0Ind, D0Ind_Total=0, D0Ind_Last, D0Ind_NextLast;
	/* User kernel arguments related variables */
	unsigned int _C_Out;
	unsigned int _SP_Out, _SC_Out;
	unsigned int _LP_Out, _LC_Out;
	unsigned int _N_Filter;
	unsigned int _SN_Filter;
	unsigned int _LN_Filter;
	unsigned int _N_In;
	unsigned int _SN_In;
	unsigned int _LN_In;
	/*============================= Ker Arg Iter Spaces =========================================
	User Kernel Iteration Space:
		[D1 Dim: Init: 38, Tiled: 2][Tile0 Dim: 6][D0 Dim: Init: 19, Tiled: 5]
	Ker Arg: Out, Tiled Space: Tile0
		Min Pipe Depth: -1, Max Pipe Depth: 1
		KerArgItSpace: 12 logical tiles, 12 physical tiles
			@ 27256 (Total Size: 119168 )[D1, [1 x 75264, 43904]][Tile0, 6:[56x10, 4:56x10, 56x6], 1]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 75264, 43904]][Tile0, 6:[56x10, 4:56x10, 56x6], 1]
		Tile0: [0, 13440, 560], Tile1: [560, 13440, 560], Tile2; [1120, 13440, 560]
	Ker Arg: Bias, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 2 logical tiles, 1 physical tiles
			@ 18816 (Total Size: 152 )[D1, [1 x 96, 56]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 96, 56]]
		Tile0: [0, 152, 152], Tile1: [0, 152, 152], Tile2; [0, 152, 152]
	Ker Arg: Scale, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 2 logical tiles, 1 physical tiles
			@ 18968 (Total Size: 38 )[D1, [1 x 24, 14]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 24, 14]]
		Tile0: [0, 38, 38], Tile1: [0, 38, 38], Tile2; [0, 38, 38]
	Ker Arg: ScaleN, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 2 logical tiles, 1 physical tiles
			@ 19008 (Total Size: 38 )[D1, [1 x 24, 14]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 24, 14]]
		Tile0: [0, 38, 38], Tile1: [0, 38, 38], Tile2; [0, 38, 38]
	Ker Arg: Filter, Tiled Space: D1
		Min Pipe Depth: 0, Max Pipe Depth: 1
		KerArgItSpace: 10 logical tiles, 2 physical tiles
			@ 19048 (Total Size: 6498 )[D1, [1 x 4104, 2394]][D0, [4 x 864, 648]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 4104, 2394]][D0, [4 x 864, 648]]
		Tile0: [0, 4104, 171], Tile1: [4104, 2394, 171], Tile2; [0, 4104, 171]
	Ker Arg: In, Tiled Space: Tile0
		Min Pipe Depth: 0, Max Pipe Depth: 1
		KerArgItSpace: 30 logical tiles, 30 physical tiles
			@ 0 (Total Size: 238336 )[D0, [4 x 50176, 37632]][Tile0, 6:[112x20, 4:112x21, 112x13], 1]
		KerArgItSpace (User Kernel Iter Order):
			[Tile0, 6:[112x20, 3:112x21, 112x13], 1][D0, [4 x 50176, 37632]]
		Tile0: [0, 8960, 2240], Tile1: [50176, 8960, 2240], Tile2; [100352, 8960, 2240]
	Ker Arg: ConvOut, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 12 logical tiles, 1 physical tiles
			@ 54136 (Total Size: 476672 )[D1, [1 x 301056, 175616]][Tile0, 6:[56x10, 4:56x10, 56x6], 4]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 301056, 175616]][Tile0, 6:[56x10, 4:56x10, 56x6], 4]
		Tile0: [0, 53760, 2240], Tile1: [0, 53760, 2240], Tile2; [0, 53760, 2240]
	Ker Arg: Infos, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 6 logical tiles, 1 physical tiles
			@ 107896 (Total Size: 16 )[Tile0, 6:[16x1, 4:16x1, 16x1], 1]
		KerArgItSpace (User Kernel Iter Order):
			[Tile0, 6:[16x1, 4:16x1, 16x1], 1]
		Tile0: [0, 16, 16], Tile1: [0, 16, 16], Tile2; [0, 16, 16]
	======================== End Ker Arg Iter Spaces =========================================*/
	/*=========================== Call Kernel, Invariant assignment =====================*/
	KerArg0->Out = (int * __restrict__) (model_int8_qdq_L1_Memory+54136);
	KerArg0->W = (unsigned short int) (56);
	KerArg1->W = (unsigned short int) (112);
	KerArg1->UsedW = (unsigned short int) (112);
	KerArg1->TotalInFeatures = (unsigned short int) (19);
	KerArg1->Out = (int * __restrict__) (model_int8_qdq_L1_Memory+54136);
	KerArg1->ExplPad = (unsigned char) (0);
	KerArg2->In = (int *__restrict__) (model_int8_qdq_L1_Memory+54136);
	KerArg2->W = (unsigned short int) (56);
	KerArg2->Infos = (signed char *__restrict__) (model_int8_qdq_L1_Memory+107896);
	KerArg2->Extra = (void *) (0);
	/*================================= Read Tiles Prolog ===============================*/
	AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) In+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+0+0), 8960, 12544, 2240, 0, DmaR_Evt1);
	_N_In=0;
	_C_Out=0; _SC_Out=13440; _LC_Out=560;
	_SP_Out=0;
	AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) Filter+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+19048+0), 4104, 171, 171, 0, DmaR_Evt2);
	_N_Filter=0;
	AT_L2_COPY(0, ((AT_L2_EXT_ADDR_TYPE) Bias+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+18816), 152, 0, DmaR_Evt3);
	AT_L2_COPY_MERGED(0, ((AT_L2_EXT_ADDR_TYPE) Scale+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+18968), 38, 0, 0);
	AT_L2_COPY_MERGED(0, ((AT_L2_EXT_ADDR_TYPE) ScaleN+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+19008), 38, 0, 0);
	AT_L2_COPY_MERGED(0, ((AT_L2_EXT_ADDR_TYPE) Infos+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+107896), 16, 0, 0);
	AT_L2_WAIT(0, DmaR_Evt3); /* Wait previous DMA read Infos */
	/*============================= End Read Tiles Prolog ===============================*/
	for (D1Ind=0; D1Ind<2; D1Ind++, D1Ind_Total++) { /* Iteration on D1 */
		int D1Ind_Last = (D1Ind==1), D1Ind_NextLast = ((D1Ind+1)==1);
		/*================================= Prepare Tiles ===================================*/
		_SN_Filter = 0;
		if (!(D1Ind_Last)) {
			_N_Filter = _N_Filter + (4104); _LN_Filter = (171); _SN_Filter = ((1)?2394:4104); 
		}
		/*============================= End Prepare Tiles ===================================*/
		/*================================= Read Tiles ======================================*/
		AT_L2_WAIT(0, DmaR_Evt2); /* Wait previous DMA read Filter */
		if (_SN_Filter) {
			AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) Filter+_N_Filter), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+19048+4104*((D1Ind_Total+1)%2)),
					1*(_SN_Filter), 171, _LN_Filter, 0, DmaR_Evt2);
		}
		/*============================= End Read Tiles ======================================*/
		for (T0Ind=0; T0Ind<6; T0Ind++, T0Ind_Total++) { /* Iteration on Tile0 */
			int T0Ind_Last = (T0Ind==5), T0Ind_NextLast = ((T0Ind+1)==5);
			/*====================== Call Kernel LOC_D0_PROLOG =========================*/
			KerArg0->H = (unsigned short int) (T0Ind_Last?6:10);
			KerArg0->Feat = (unsigned short int) ((D1Ind_Last)?14:24);
			KerArg0->Bias = (void * __restrict__) (model_int8_qdq_L1_Memory+18816+((D1Ind)*96));
			KerArg0->NormBias = (unsigned char) (((char *)(model_int8_qdq_L1_Memory+107896))[8]);
			AT_FORK(gap_ncore(), (void *) KerParSetBiasB32_SQ8, (void *) KerArg0);
			__CALL(KerParSetBiasB32_SQ8, KerArg0);
			for (D0Ind=0; D0Ind<5; D0Ind++, D0Ind_Total++) { /* Iteration on D0 */
				int D0Ind_Last = (D0Ind==4), D0Ind_NextLast = ((D0Ind+1)==4);
				/*================================= Prepare Tiles ===================================*/
				_SN_In = 0;
				if (!(D0Ind_Last)) {
					_N_In = _N_In + (50176); _LN_In = ((T0Ind_Last)?1456:(2352-112*(T0Ind==0))); _SN_In = (((D0Ind_NextLast)?3:4)*_LN_In); 
				} else if (!(T0Ind_Last)) {
					_N_In = _N_In + (2240-(112*(T0Ind==0)))+(-200704); _LN_In = ((T0Ind_NextLast)?1456:2352); _SN_In = (4*_LN_In); 
				} else if (!(D1Ind_Last)) {
					_N_In = _N_In + (-11088)+(-200704); _LN_In = (2240); _SN_In = (4*_LN_In); 
				}
				/*============================= End Prepare Tiles ===================================*/
				/*================================= Read Tiles ======================================*/
				AT_L2_WAIT(0, DmaR_Evt1); /* Wait previous DMA read In */
				if (_SN_In) {
					AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) In+_N_In), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+0+9408*((D0Ind_Total+1)%2)),
							1*(_SN_In), 12544, _LN_In, 0, DmaR_Evt1);
				}
				/*============================= End Read Tiles ======================================*/
				/*====================== Call Kernel LOC_D0 =========================*/
				KerArg1->In = (signed char * __restrict__) (model_int8_qdq_L1_Memory+0+9408*((D0Ind_Total)%2));
				KerArg1->H = (unsigned short int) (((T0Ind_Last)?13:21)-1*(T0Ind==0));
				KerArg1->UsedH = (unsigned short int) (((T0Ind_Last)?13:21)-1*(T0Ind==0));
				KerArg1->InFeatures = (unsigned short int) ((D0Ind_Last)?3:4);
				KerArg1->OutFeatures = (unsigned short int) ((D1Ind_Last)?14:24);
				KerArg1->Filter = (signed char * __restrict__) (model_int8_qdq_L1_Memory+19048+((D0Ind)*36)+4104*((D1Ind_Total)%2));
				KerArg1->Pad = (v4u) ((v4u){1,0,1*(T0Ind==0),0*(T0Ind_Last)});
				AT_FORK(gap_ncore(), (void *) KerParConv3x3Stride2_SQ8, (void *) KerArg1);
				__CALL(KerParConv3x3Stride2_SQ8, KerArg1);
				/*================================= Update Arg Pipeline =============================*/
				/*============================= End Update Arg Pipeline =============================*/
			} /* End iteration on D0 */
			/*====================== Call Kernel LOC_D0_EPILOG =========================*/
			KerArg2->Out = (void *__restrict__) (model_int8_qdq_L1_Memory+27256+13440*((T0Ind_Total)%2));
			KerArg2->Feat = (unsigned short int) ((D1Ind_Last)?14:24);
			KerArg2->H = (unsigned short int) (T0Ind_Last?6:10);
			KerArg2->Scale = (unsigned char *__restrict__) (model_int8_qdq_L1_Memory+18968+((D1Ind)*24));
			KerArg2->ScaleN = (unsigned char *__restrict__) (model_int8_qdq_L1_Memory+19008+((D1Ind)*24));
			AT_FORK(gap_ncore(), (void *) KerParReduct_CC_SQ8, (void *) KerArg2);
			__CALL(KerParReduct_CC_SQ8, KerArg2);
			/*================================= Write Tiles =====================================*/
			if (_SP_Out) AT_L2_WAIT(0, DmaW_Evt1); /* Wait previous DMA write Out */
			AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) Out+_C_Out), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+27256+13440*((T0Ind_Total)%2)),
					_SC_Out, 3136, _LC_Out, 1, DmaW_Evt1);
			/*============================= End Write Tiles =====================================*/
			/*================================= Update Arg Pipeline =============================*/
			_SP_Out = _SC_Out;_LP_Out = _LC_Out;
			/*============================= End Update Arg Pipeline =============================*/
			/*================================= Prepare Tiles ===================================*/
			_SC_Out = 0;
			if (!(T0Ind_Last)) {
				_C_Out = _C_Out + (560); _LC_Out = ((T0Ind_NextLast)?336:560); _SC_Out = (((D1Ind_Last)?14:24)*_LC_Out); 
			} else if (!(D1Ind_Last)) {
				_C_Out = _C_Out + (75264)+(-2800); _LC_Out = (560); _SC_Out = (((1)?14:24)*_LC_Out); 
			}
			/*============================= End Prepare Tiles ===================================*/
		} /* End iteration on Tile0 */
		/*================================= Update Arg Pipeline =============================*/
		/*============================= End Update Arg Pipeline =============================*/
	} /* End iteration on D1 */
	/*================================ Write Tiles Epilog ===============================*/
	AT_L2_WAIT(0, DmaW_Evt1); /* Wait previous DMA write Out */
	/*============================ End Write Tiles Epilog ===============================*/
}
void  S13__net_net_6_Conv(
		signed char * __restrict__ In,
		signed char * __restrict__ Filter,
		int * __restrict__ Bias,
		signed char * __restrict__ Out,
		unsigned char * __restrict__ Scale,
		signed char * __restrict__ ScaleN,
		signed char * __restrict__ Infos)

{
	/* Shared L1: 113848 bytes, L2 buffer: 0 bytes */
	/* Local variables used by this kernel */
	AT_L2_EVENT _DmaW_Evt1, *DmaW_Evt1 = &_DmaW_Evt1;
	AT_L2_EVENT _DmaR_Evt3, *DmaR_Evt3 = &_DmaR_Evt3;
	AT_L2_EVENT _DmaR_Evt2, *DmaR_Evt2 = &_DmaR_Evt2;
	AT_L2_EVENT _DmaR_Evt1, *DmaR_Evt1 = &_DmaR_Evt1;
	KerSetBias_SQ8_T S_KerArg0, *KerArg0 = &S_KerArg0;
	KerConv_SQ8_T S_KerArg1, *KerArg1 = &S_KerArg1;
	KerConvLinReduct_SQ8_T S_KerArg2, *KerArg2 = &S_KerArg2;

	/* Iteration space related variables */
	int D1Ind, D1Ind_Total=0, D1Ind_Last, D1Ind_NextLast;
	int T0Ind, T0Ind_Total=0, T0Ind_Last, T0Ind_NextLast;
	int D0Ind, D0Ind_Total=0, D0Ind_Last, D0Ind_NextLast;
	/* User kernel arguments related variables */
	unsigned int _C_Out;
	unsigned int _SP_Out, _SC_Out;
	unsigned int _LP_Out, _LC_Out;
	unsigned int _N_Filter;
	unsigned int _SN_Filter;
	unsigned int _LN_Filter;
	unsigned int _N_In;
	unsigned int _SN_In;
	unsigned int _LN_In;
	/*============================= Ker Arg Iter Spaces =========================================
	User Kernel Iteration Space:
		[D1 Dim: Init: 76, Tiled: 2][Tile0 Dim: 3][D0 Dim: Init: 38, Tiled: 5]
	Ker Arg: Out, Tiled Space: Tile0
		Min Pipe Depth: -1, Max Pipe Depth: 1
		KerArgItSpace: 6 logical tiles, 6 physical tiles
			@ 46632 (Total Size: 59584 )[D1, [1 x 31360, 28224]][Tile0, 3:[28x10, 1:28x10, 28x8], 1]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 31360, 28224]][Tile0, 3:[28x10, 1:28x10, 28x8], 1]
		Tile0: [0, 11200, 280], Tile1: [280, 11200, 280], Tile2; [560, 8960, 224]
	Ker Arg: Bias, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 2 logical tiles, 1 physical tiles
			@ 18816 (Total Size: 304 )[D1, [1 x 160, 144]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 160, 144]]
		Tile0: [0, 304, 304], Tile1: [0, 304, 304], Tile2; [0, 304, 304]
	Ker Arg: Scale, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 2 logical tiles, 1 physical tiles
			@ 19120 (Total Size: 76 )[D1, [1 x 40, 36]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 40, 36]]
		Tile0: [0, 76, 76], Tile1: [0, 76, 76], Tile2; [0, 76, 76]
	Ker Arg: ScaleN, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 2 logical tiles, 1 physical tiles
			@ 19196 (Total Size: 76 )[D1, [1 x 40, 36]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 40, 36]]
		Tile0: [0, 76, 76], Tile1: [0, 76, 76], Tile2; [0, 76, 76]
	Ker Arg: Filter, Tiled Space: D1
		Min Pipe Depth: 0, Max Pipe Depth: 1
		KerArgItSpace: 10 logical tiles, 2 physical tiles
			@ 19272 (Total Size: 25992 )[D1, [1 x 13680, 12312]][D0, [4 x 2880, 2160]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 13680, 12312]][D0, [4 x 2880, 2160]]
		Tile0: [0, 13680, 342], Tile1: [13680, 12312, 342], Tile2; [0, 13680, 342]
	Ker Arg: In, Tiled Space: Tile0
		Min Pipe Depth: 0, Max Pipe Depth: 1
		KerArgItSpace: 15 logical tiles, 15 physical tiles
			@ 0 (Total Size: 119168 )[D0, [4 x 25088, 18816]][Tile0, 3:[56x20, 1:56x21, 56x17], 1]
		KerArgItSpace (User Kernel Iter Order):
			[Tile0, 3:[56x20, 3:56x21, 56x17], 1][D0, [4 x 25088, 18816]]
		Tile0: [0, 8960, 1120], Tile1: [25088, 8960, 1120], Tile2; [50176, 8960, 1120]
	Ker Arg: ConvOut, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 6 logical tiles, 1 physical tiles
			@ 69032 (Total Size: 238336 )[D1, [1 x 125440, 112896]][Tile0, 3:[28x10, 1:28x10, 28x8], 4]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 125440, 112896]][Tile0, 3:[28x10, 1:28x10, 28x8], 4]
		Tile0: [0, 44800, 1120], Tile1: [0, 44800, 1120], Tile2; [0, 44800, 1120]
	Ker Arg: Infos, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 3 logical tiles, 1 physical tiles
			@ 113832 (Total Size: 16 )[Tile0, 3:[16x1, 1:16x1, 16x1], 1]
		KerArgItSpace (User Kernel Iter Order):
			[Tile0, 3:[16x1, 1:16x1, 16x1], 1]
		Tile0: [0, 16, 16], Tile1: [0, 16, 16], Tile2; [0, 16, 16]
	======================== End Ker Arg Iter Spaces =========================================*/
	/*=========================== Call Kernel, Invariant assignment =====================*/
	KerArg0->Out = (int * __restrict__) (model_int8_qdq_L1_Memory+69032);
	KerArg0->W = (unsigned short int) (28);
	KerArg1->W = (unsigned short int) (56);
	KerArg1->UsedW = (unsigned short int) (56);
	KerArg1->TotalInFeatures = (unsigned short int) (38);
	KerArg1->Out = (int * __restrict__) (model_int8_qdq_L1_Memory+69032);
	KerArg1->ExplPad = (unsigned char) (0);
	KerArg2->In = (int *__restrict__) (model_int8_qdq_L1_Memory+69032);
	KerArg2->W = (unsigned short int) (28);
	KerArg2->Infos = (signed char *__restrict__) (model_int8_qdq_L1_Memory+113832);
	KerArg2->Extra = (void *) (0);
	/*================================= Read Tiles Prolog ===============================*/
	AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) In+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+0+0), 8960, 3136, 1120, 0, DmaR_Evt1);
	_N_In=0;
	_C_Out=0; _SC_Out=11200; _LC_Out=280;
	_SP_Out=0;
	AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) Filter+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+19272+0), 13680, 342, 342, 0, DmaR_Evt2);
	_N_Filter=0;
	AT_L2_COPY(0, ((AT_L2_EXT_ADDR_TYPE) Bias+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+18816), 304, 0, DmaR_Evt3);
	AT_L2_COPY_MERGED(0, ((AT_L2_EXT_ADDR_TYPE) Scale+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+19120), 76, 0, 0);
	AT_L2_COPY_MERGED(0, ((AT_L2_EXT_ADDR_TYPE) ScaleN+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+19196), 76, 0, 0);
	AT_L2_COPY_MERGED(0, ((AT_L2_EXT_ADDR_TYPE) Infos+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+113832), 16, 0, 0);
	AT_L2_WAIT(0, DmaR_Evt3); /* Wait previous DMA read Infos */
	/*============================= End Read Tiles Prolog ===============================*/
	for (D1Ind=0; D1Ind<2; D1Ind++, D1Ind_Total++) { /* Iteration on D1 */
		int D1Ind_Last = (D1Ind==1), D1Ind_NextLast = ((D1Ind+1)==1);
		/*================================= Prepare Tiles ===================================*/
		_SN_Filter = 0;
		if (!(D1Ind_Last)) {
			_N_Filter = _N_Filter + (13680); _LN_Filter = (342); _SN_Filter = ((1)?12312:13680); 
		}
		/*============================= End Prepare Tiles ===================================*/
		/*================================= Read Tiles ======================================*/
		AT_L2_WAIT(0, DmaR_Evt2); /* Wait previous DMA read Filter */
		if (_SN_Filter) {
			AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) Filter+_N_Filter), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+19272+13680*((D1Ind_Total+1)%2)),
					1*(_SN_Filter), 342, _LN_Filter, 0, DmaR_Evt2);
		}
		/*============================= End Read Tiles ======================================*/
		for (T0Ind=0; T0Ind<3; T0Ind++, T0Ind_Total++) { /* Iteration on Tile0 */
			int T0Ind_Last = (T0Ind==2), T0Ind_NextLast = ((T0Ind+1)==2);
			/*====================== Call Kernel LOC_D0_PROLOG =========================*/
			KerArg0->H = (unsigned short int) (T0Ind_Last?8:10);
			KerArg0->Feat = (unsigned short int) ((D1Ind_Last)?36:40);
			KerArg0->Bias = (void * __restrict__) (model_int8_qdq_L1_Memory+18816+((D1Ind)*160));
			KerArg0->NormBias = (unsigned char) (((char *)(model_int8_qdq_L1_Memory+113832))[8]);
			AT_FORK(gap_ncore(), (void *) KerParSetBiasB32_SQ8, (void *) KerArg0);
			__CALL(KerParSetBiasB32_SQ8, KerArg0);
			for (D0Ind=0; D0Ind<5; D0Ind++, D0Ind_Total++) { /* Iteration on D0 */
				int D0Ind_Last = (D0Ind==4), D0Ind_NextLast = ((D0Ind+1)==4);
				/*================================= Prepare Tiles ===================================*/
				_SN_In = 0;
				if (!(D0Ind_Last)) {
					_N_In = _N_In + (25088); _LN_In = ((T0Ind_Last)?952:(1176-56*(T0Ind==0))); _SN_In = (((D0Ind_NextLast)?6:8)*_LN_In); 
				} else if (!(T0Ind_Last)) {
					_N_In = _N_In + (1120-(56*(T0Ind==0)))+(-100352); _LN_In = ((T0Ind_NextLast)?952:1176); _SN_In = (8*_LN_In); 
				} else if (!(D1Ind_Last)) {
					_N_In = _N_In + (-2184)+(-100352); _LN_In = (1120); _SN_In = (8*_LN_In); 
				}
				/*============================= End Prepare Tiles ===================================*/
				/*================================= Read Tiles ======================================*/
				AT_L2_WAIT(0, DmaR_Evt1); /* Wait previous DMA read In */
				if (_SN_In) {
					AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) In+_N_In), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+0+9408*((D0Ind_Total+1)%2)),
							1*(_SN_In), 3136, _LN_In, 0, DmaR_Evt1);
				}
				/*============================= End Read Tiles ======================================*/
				/*====================== Call Kernel LOC_D0 =========================*/
				KerArg1->In = (signed char * __restrict__) (model_int8_qdq_L1_Memory+0+9408*((D0Ind_Total)%2));
				KerArg1->H = (unsigned short int) (((T0Ind_Last)?17:21)-1*(T0Ind==0));
				KerArg1->UsedH = (unsigned short int) (((T0Ind_Last)?17:21)-1*(T0Ind==0));
				KerArg1->InFeatures = (unsigned short int) ((D0Ind_Last)?6:8);
				KerArg1->OutFeatures = (unsigned short int) ((D1Ind_Last)?36:40);
				KerArg1->Filter = (signed char * __restrict__) (model_int8_qdq_L1_Memory+19272+((D0Ind)*72)+13680*((D1Ind_Total)%2));
				KerArg1->Pad = (v4u) ((v4u){1,0,1*(T0Ind==0),0*(T0Ind_Last)});
				AT_FORK(gap_ncore(), (void *) KerParConv3x3Stride2_SQ8, (void *) KerArg1);
				__CALL(KerParConv3x3Stride2_SQ8, KerArg1);
				/*================================= Update Arg Pipeline =============================*/
				/*============================= End Update Arg Pipeline =============================*/
			} /* End iteration on D0 */
			/*====================== Call Kernel LOC_D0_EPILOG =========================*/
			KerArg2->Out = (void *__restrict__) (model_int8_qdq_L1_Memory+46632+11200*((T0Ind_Total)%2));
			KerArg2->Feat = (unsigned short int) ((D1Ind_Last)?36:40);
			KerArg2->H = (unsigned short int) (T0Ind_Last?8:10);
			KerArg2->Scale = (unsigned char *__restrict__) (model_int8_qdq_L1_Memory+19120+((D1Ind)*40));
			KerArg2->ScaleN = (unsigned char *__restrict__) (model_int8_qdq_L1_Memory+19196+((D1Ind)*40));
			AT_FORK(gap_ncore(), (void *) KerParReduct_CC_SQ8, (void *) KerArg2);
			__CALL(KerParReduct_CC_SQ8, KerArg2);
			/*================================= Write Tiles =====================================*/
			if (_SP_Out) AT_L2_WAIT(0, DmaW_Evt1); /* Wait previous DMA write Out */
			AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) Out+_C_Out), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+46632+11200*((T0Ind_Total)%2)),
					_SC_Out, 784, _LC_Out, 1, DmaW_Evt1);
			/*============================= End Write Tiles =====================================*/
			/*================================= Update Arg Pipeline =============================*/
			_SP_Out = _SC_Out;_LP_Out = _LC_Out;
			/*============================= End Update Arg Pipeline =============================*/
			/*================================= Prepare Tiles ===================================*/
			_SC_Out = 0;
			if (!(T0Ind_Last)) {
				_C_Out = _C_Out + (280); _LC_Out = ((T0Ind_NextLast)?224:280); _SC_Out = (((D1Ind_Last)?36:40)*_LC_Out); 
			} else if (!(D1Ind_Last)) {
				_C_Out = _C_Out + (31360)+(-560); _LC_Out = (280); _SC_Out = (((1)?36:40)*_LC_Out); 
			}
			/*============================= End Prepare Tiles ===================================*/
		} /* End iteration on Tile0 */
		/*================================= Update Arg Pipeline =============================*/
		/*============================= End Update Arg Pipeline =============================*/
	} /* End iteration on D1 */
	/*================================ Write Tiles Epilog ===============================*/
	AT_L2_WAIT(0, DmaW_Evt1); /* Wait previous DMA write Out */
	/*============================ End Write Tiles Epilog ===============================*/
}
void  S16__net_net_8_Conv(
		signed char * __restrict__ In,
		signed char * __restrict__ Filter,
		int * __restrict__ Bias,
		signed char * __restrict__ Out,
		unsigned char * __restrict__ Scale,
		signed char * __restrict__ ScaleN,
		signed char * __restrict__ Infos)

{
	/* Shared L1: 114328 bytes, L2 buffer: 0 bytes */
	/* Local variables used by this kernel */
	AT_L2_EVENT _DmaR_Evt1, *DmaR_Evt1 = &_DmaR_Evt1;
	AT_L2_EVENT _DmaR_Evt3, *DmaR_Evt3 = &_DmaR_Evt3;
	AT_L2_EVENT _DmaR_Evt2, *DmaR_Evt2 = &_DmaR_Evt2;
	AT_L2_EVENT _DmaW_Evt1, *DmaW_Evt1 = &_DmaW_Evt1;
	KerSetBias_SQ8_T S_KerArg0, *KerArg0 = &S_KerArg0;
	KerConv_SQ8_T S_KerArg1, *KerArg1 = &S_KerArg1;
	KerConvLinReduct_SQ8_T S_KerArg2, *KerArg2 = &S_KerArg2;

	/* Iteration space related variables */
	int D1Ind, D1Ind_Total=0, D1Ind_Last, D1Ind_NextLast;
	int T0Ind, T0Ind_Total=0, T0Ind_Last, T0Ind_NextLast;
	int D0Ind, D0Ind_Total=0, D0Ind_Last, D0Ind_NextLast;
	/* User kernel arguments related variables */
	unsigned int _N_In;
	unsigned int _SN_In;
	unsigned int _LN_In;
	unsigned int _N_Filter;
	unsigned int _SN_Filter;
	unsigned int _LN_Filter;
	unsigned int _C_Out;
	unsigned int _SP_Out, _SC_Out;
	unsigned int _LP_Out, _LC_Out;
	/*============================= Ker Arg Iter Spaces =========================================
	User Kernel Iteration Space:
		[D1 Dim: Init: 76, Tiled: 2][Tile0 Dim: 4][D0 Dim: Init: 76, Tiled: 4]
	Ker Arg: In, Tiled Space: Tile0
		Min Pipe Depth: 0, Max Pipe Depth: 1
		KerArgItSpace: 16 logical tiles, 16 physical tiles
			@ 0 (Total Size: 59584 )[D0, [3 x 18816, 3136]][Tile0, 4:[28x8, 2:28x9, 28x8], 1]
		KerArgItSpace (User Kernel Iter Order):
			[Tile0, 4:[28x8, 2:28x9, 28x8], 1][D0, [3 x 18816, 3136]]
		Tile0: [0, 5376, 224], Tile1: [18816, 5376, 224], Tile2; [37632, 5376, 224]
	Ker Arg: Bias, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 2 logical tiles, 1 physical tiles
			@ 12096 (Total Size: 304 )[D1, [1 x 160, 144]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 160, 144]]
		Tile0: [0, 304, 304], Tile1: [0, 304, 304], Tile2; [0, 304, 304]
	Ker Arg: Scale, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 2 logical tiles, 1 physical tiles
			@ 12400 (Total Size: 76 )[D1, [1 x 40, 36]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 40, 36]]
		Tile0: [0, 76, 76], Tile1: [0, 76, 76], Tile2; [0, 76, 76]
	Ker Arg: ScaleN, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 2 logical tiles, 1 physical tiles
			@ 12476 (Total Size: 76 )[D1, [1 x 40, 36]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 40, 36]]
		Tile0: [0, 76, 76], Tile1: [0, 76, 76], Tile2; [0, 76, 76]
	Ker Arg: Filter, Tiled Space: D1
		Min Pipe Depth: 0, Max Pipe Depth: 1
		KerArgItSpace: 8 logical tiles, 2 physical tiles
			@ 12552 (Total Size: 51984 )[D1, [1 x 27360, 24624]][D0, [3 x 8640, 1440]]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 27360, 24624]][D0, [3 x 8640, 1440]]
		Tile0: [0, 27360, 684], Tile1: [27360, 24624, 684], Tile2; [0, 27360, 684]
	Ker Arg: Out, Tiled Space: Tile0
		Min Pipe Depth: -1, Max Pipe Depth: 1
		KerArgItSpace: 8 logical tiles, 8 physical tiles
			@ 67272 (Total Size: 59584 )[D1, [1 x 31360, 28224]][Tile0, 4:[28x7, 2:28x7, 28x7], 1]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 31360, 28224]][Tile0, 4:[28x7, 2:28x7, 28x7], 1]
		Tile0: [0, 7840, 196], Tile1: [196, 7840, 196], Tile2; [392, 7840, 196]
	Ker Arg: ConvOut, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 8 logical tiles, 1 physical tiles
			@ 82952 (Total Size: 238336 )[D1, [1 x 125440, 112896]][Tile0, 4:[28x7, 2:28x7, 28x7], 4]
		KerArgItSpace (User Kernel Iter Order):
			[D1, [1 x 125440, 112896]][Tile0, 4:[28x7, 2:28x7, 28x7], 4]
		Tile0: [0, 31360, 784], Tile1: [0, 31360, 784], Tile2; [0, 31360, 784]
	Ker Arg: Infos, Tiled Space: Buffer
		Min Pipe Depth: 0, Max Pipe Depth: 0
		KerArgItSpace: 4 logical tiles, 1 physical tiles
			@ 114312 (Total Size: 16 )[Tile0, 4:[16x1, 2:16x1, 16x1], 1]
		KerArgItSpace (User Kernel Iter Order):
			[Tile0, 4:[16x1, 2:16x1, 16x1], 1]
		Tile0: [0, 16, 16], Tile1: [0, 16, 16], Tile2; [0, 16, 16]
	======================== End Ker Arg Iter Spaces =========================================*/
	/*=========================== Call Kernel, Invariant assignment =====================*/
	KerArg0->Out = (int * __restrict__) (model_int8_qdq_L1_Memory+82952);
	KerArg0->W = (unsigned short int) (28);
	KerArg0->H = (unsigned short int) (7);
	KerArg1->W = (unsigned short int) (28);
	KerArg1->UsedW = (unsigned short int) (28);
	KerArg1->TotalInFeatures = (unsigned short int) (76);
	KerArg1->Out = (int * __restrict__) (model_int8_qdq_L1_Memory+82952);
	KerArg1->ExplPad = (unsigned char) (0);
	KerArg2->In = (int *__restrict__) (model_int8_qdq_L1_Memory+82952);
	KerArg2->W = (unsigned short int) (28);
	KerArg2->H = (unsigned short int) (7);
	KerArg2->Infos = (signed char *__restrict__) (model_int8_qdq_L1_Memory+114312);
	KerArg2->Extra = (void *) (0);
	/*================================= Read Tiles Prolog ===============================*/
	AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) In+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+0+0), 5376, 784, 224, 0, DmaR_Evt1);
	_N_In=0;
	_C_Out=0; _SC_Out=7840; _LC_Out=196;
	_SP_Out=0;
	AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) Filter+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+12552+0), 27360, 684, 684, 0, DmaR_Evt2);
	_N_Filter=0;
	AT_L2_COPY(0, ((AT_L2_EXT_ADDR_TYPE) Bias+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+12096), 304, 0, DmaR_Evt3);
	AT_L2_COPY_MERGED(0, ((AT_L2_EXT_ADDR_TYPE) Scale+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+12400), 76, 0, 0);
	AT_L2_COPY_MERGED(0, ((AT_L2_EXT_ADDR_TYPE) ScaleN+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+12476), 76, 0, 0);
	AT_L2_COPY_MERGED(0, ((AT_L2_EXT_ADDR_TYPE) Infos+0), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+114312), 16, 0, 0);
	AT_L2_WAIT(0, DmaR_Evt3); /* Wait previous DMA read Infos */
	/*============================= End Read Tiles Prolog ===============================*/
	for (D1Ind=0; D1Ind<2; D1Ind++, D1Ind_Total++) { /* Iteration on D1 */
		int D1Ind_Last = (D1Ind==1), D1Ind_NextLast = ((D1Ind+1)==1);
		/*================================= Prepare Tiles ===================================*/
		_SN_Filter = 0;
		if (!(D1Ind_Last)) {
			_N_Filter = _N_Filter + (27360); _LN_Filter = (684); _SN_Filter = ((1)?24624:27360); 
		}
		/*============================= End Prepare Tiles ===================================*/
		/*================================= Read Tiles ======================================*/
		AT_L2_WAIT(0, DmaR_Evt2); /* Wait previous DMA read Filter */
		if (_SN_Filter) {
			AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) Filter+_N_Filter), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+12552+27360*((D1Ind_Total+1)%2)),
					1*(_SN_Filter), 684, _LN_Filter, 0, DmaR_Evt2);
		}
		/*============================= End Read Tiles ======================================*/
		for (T0Ind=0; T0Ind<4; T0Ind++, T0Ind_Total++) { /* Iteration on Tile0 */
			int T0Ind_Last = (T0Ind==3), T0Ind_NextLast = ((T0Ind+1)==3);
			/*====================== Call Kernel LOC_D0_PROLOG =========================*/
			KerArg0->Feat = (unsigned short int) ((D1Ind_Last)?36:40);
			KerArg0->Bias = (void * __restrict__) (model_int8_qdq_L1_Memory+12096+((D1Ind)*160));
			KerArg0->NormBias = (unsigned char) (((char *)(model_int8_qdq_L1_Memory+114312))[8]);
			AT_FORK(gap_ncore(), (void *) KerParSetBiasB32_SQ8, (void *) KerArg0);
			__CALL(KerParSetBiasB32_SQ8, KerArg0);
			for (D0Ind=0; D0Ind<4; D0Ind++, D0Ind_Total++) { /* Iteration on D0 */
				int D0Ind_Last = (D0Ind==3), D0Ind_NextLast = ((D0Ind+1)==3);
				/*================================= Prepare Tiles ===================================*/
				_SN_In = 0;
				if (!(D0Ind_Last)) {
					_N_In = _N_In + (18816); _LN_In = ((T0Ind_Last)?224:(252-28*(T0Ind==0))); _SN_In = (((D0Ind_NextLast)?4:24)*_LN_In); 
				} else if (!(T0Ind_Last)) {
					_N_In = _N_In + (196-(28*(T0Ind==0)))+(-56448); _LN_In = ((T0Ind_NextLast)?224:252); _SN_In = (24*_LN_In); 
				} else if (!(D1Ind_Last)) {
					_N_In = _N_In + (-560)+(-56448); _LN_In = (224); _SN_In = (24*_LN_In); 
				}
				/*============================= End Prepare Tiles ===================================*/
				/*================================= Read Tiles ======================================*/
				AT_L2_WAIT(0, DmaR_Evt1); /* Wait previous DMA read In */
				if (_SN_In) {
					AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) In+_N_In), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+0+6048*((D0Ind_Total+1)%2)),
							1*(_SN_In), 784, _LN_In, 0, DmaR_Evt1);
				}
				/*============================= End Read Tiles ======================================*/
				/*====================== Call Kernel LOC_D0 =========================*/
				KerArg1->In = (signed char * __restrict__) (model_int8_qdq_L1_Memory+0+6048*((D0Ind_Total)%2));
				KerArg1->H = (unsigned short int) (9-1*(T0Ind==0)-1*(T0Ind_Last));
				KerArg1->UsedH = (unsigned short int) (9-1*(T0Ind==0)-1*(T0Ind_Last));
				KerArg1->InFeatures = (unsigned short int) ((D0Ind_Last)?4:24);
				KerArg1->OutFeatures = (unsigned short int) ((D1Ind_Last)?36:40);
				KerArg1->Filter = (signed char * __restrict__) (model_int8_qdq_L1_Memory+12552+((D0Ind)*216)+27360*((D1Ind_Total)%2));
				KerArg1->Pad = (v4u) ((v4u){1,1,1*(T0Ind==0),1*(T0Ind_Last)});
				AT_FORK(gap_ncore(), (void *) KerParConv3x3Stride1_SQ8, (void *) KerArg1);
				__CALL(KerParConv3x3Stride1_SQ8, KerArg1);
				/*================================= Update Arg Pipeline =============================*/
				/*============================= End Update Arg Pipeline =============================*/
			} /* End iteration on D0 */
			/*====================== Call Kernel LOC_D0_EPILOG =========================*/
			KerArg2->Out = (void *__restrict__) (model_int8_qdq_L1_Memory+67272+7840*((T0Ind_Total)%2));
			KerArg2->Feat = (unsigned short int) ((D1Ind_Last)?36:40);
			KerArg2->Scale = (unsigned char *__restrict__) (model_int8_qdq_L1_Memory+12400+((D1Ind)*40));
			KerArg2->ScaleN = (unsigned char *__restrict__) (model_int8_qdq_L1_Memory+12476+((D1Ind)*40));
			AT_FORK(gap_ncore(), (void *) KerParReduct_CC_SQ8, (void *) KerArg2);
			__CALL(KerParReduct_CC_SQ8, KerArg2);
			/*================================= Write Tiles =====================================*/
			if (_SP_Out) AT_L2_WAIT(0, DmaW_Evt1); /* Wait previous DMA write Out */
			AT_L2_COPY2D(0, ((AT_L2_EXT_ADDR_TYPE) Out+_C_Out), ((AT_L2_INT_ADDR_TYPE) model_int8_qdq_L1_Memory+67272+7840*((T0Ind_Total)%2)),
					_SC_Out, 784, _LC_Out, 1, DmaW_Evt1);
			/*============================= End Write Tiles =====================================*/
			/*================================= Update Arg Pipeline =============================*/
			_SP_Out = _SC_Out;_LP_Out = _LC_Out;
			/*============================= End Update Arg Pipeline =============================*/
			/*================================= Prepare Tiles ===================================*/
			_SC_Out = 0;
			if (!(T0Ind_Last)) {
				_C_Out = _C_Out + (196); _LC_Out = (196); _SC_Out = (((D1Ind_Last)?36:40)*_LC_Out); 
			} else if (!(D1Ind_Last)) {
				_C_Out = _C_Out + (31360)+(-588); _LC_Out = (196); _SC_Out = (((1)?36:40)*_LC_Out); 
			}
			/*============================= End Prepare Tiles ===================================*/
		} /* End iteration on Tile0 */
		/*================================= Update Arg Pipeline =============================*/
		/*============================= End Update Arg Pipeline =============================*/
	} /* End iteration on D1 */
	/*================================ Write Tiles Epilog ===============================*/
	AT_L2_WAIT(0, DmaW_Evt1); /* Wait previous DMA write Out */
	/*============================ End Write Tiles Epilog ===============================*/
}
#pragma GCC diagnostic pop
int  model_int8_qdqCNN_Construct()

{
	int Error;

	AT_DEFAULTFLASH_FS_CONF_T DefaultFlashConf;
	AT_DEFAULTFLASH_FS_CONF_INIT(&DefaultFlashConf, AT_MEM_L3_DEFAULTFLASH, 0);
	AT_DEFAULTFLASH_FS_OPEN(&DefaultFlash, &DefaultFlashConf, 0, "model_int8_qdq_L3_Flash_Const.dat", &Error);
	if (Error) return AT_FLASH_OPEN_ERROR;

	model_int8_qdq_L2_Memory = (AT_L2_POINTER) AT_L2_ALLOC(0, 87660);
	if (model_int8_qdq_L2_Memory == 0) return AT_L2_OPEN_ERROR;
	model_int8_qdq_L2_Memory_Dyn = (AT_L2_POINTER) AT_L2_ALLOC(0, 689920);
	if (model_int8_qdq_L2_Memory_Dyn == 0) return AT_L2_OPEN_ERROR;
	model_int8_qdq_L1_Memory = (AT_L1_POINTER) AT_L1_ALLOC(0, 114328);
	if (model_int8_qdq_L1_Memory == 0) return AT_L1_OPEN_ERROR;
	AT_DEFAULTFLASH_FS_FC_EVENT _UchanHF1, *UchanHF1 = &_UchanHF1;
	/* Static Moving _net_net_0_conv_weights, size 243 from DefaultFlash at 86624 to (size 243) L2 at 86624..86866 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 86624), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 86624), 243, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving Constant_net_0_bias_quantized, size 36 from DefaultFlash at 87480 to (size 36) L2 at 87480..87515 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87480), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87480), 36, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving S4_Mul_scale, size 9 from DefaultFlash at 87636 to (size 9) L2 at 87636..87644 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87636), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87636), 9, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving S4_Mul_shift, size 9 from DefaultFlash at 87648 to (size 9) L2 at 87648..87656 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87648), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87648), 9, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving S4_Infos, size 16 from DefaultFlash at 87556 to (size 16) L2 at 87556..87571 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87556), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87556), 16, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving _net_net_2_conv_weights, size 1539 from DefaultFlash at 84476 to (size 1539) L2 at 84476..86014 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 84476), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 84476), 1539, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving Constant_net_2_bias_quantized, size 76 from DefaultFlash at 87020 to (size 76) L2 at 87020..87095 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87020), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87020), 76, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving S7_Mul_scale, size 19 from DefaultFlash at 87516 to (size 19) L2 at 87516..87534 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87516), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87516), 19, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving S7_Mul_shift, size 19 from DefaultFlash at 87536 to (size 19) L2 at 87536..87554 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87536), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87536), 19, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving S7_Infos, size 16 from DefaultFlash at 87572 to (size 16) L2 at 87572..87587 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87572), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87572), 16, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving _net_net_4_conv_weights, size 6498 from DefaultFlash at 77976 to (size 6498) L2 at 77976..84473 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 77976), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 77976), 6498, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving Constant_net_4_bias_quantized, size 152 from DefaultFlash at 86868 to (size 152) L2 at 86868..87019 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 86868), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 86868), 152, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving S10_Mul_scale, size 38 from DefaultFlash at 87400 to (size 38) L2 at 87400..87437 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87400), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87400), 38, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving S10_Mul_shift, size 38 from DefaultFlash at 87440 to (size 38) L2 at 87440..87477 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87440), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87440), 38, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving S10_Infos, size 16 from DefaultFlash at 87588 to (size 16) L2 at 87588..87603 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87588), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87588), 16, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving _net_net_6_conv_weights, size 25992 from DefaultFlash at 51984 to (size 25992) L2 at 51984..77975 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 51984), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 51984), 25992, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving Constant_net_6_bias_quantized, size 304 from DefaultFlash at 86016 to (size 304) L2 at 86016..86319 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 86016), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 86016), 304, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving S13_Mul_scale, size 76 from DefaultFlash at 87096 to (size 76) L2 at 87096..87171 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87096), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87096), 76, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving S13_Mul_shift, size 76 from DefaultFlash at 87172 to (size 76) L2 at 87172..87247 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87172), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87172), 76, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving S13_Infos, size 16 from DefaultFlash at 87604 to (size 16) L2 at 87604..87619 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87604), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87604), 16, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving _net_net_8_conv_weights, size 51984 from DefaultFlash at 0 to (size 51984) L2 at 0..51983 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 0), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 0), 51984, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving Constant_net_8_bias_quantized, size 304 from DefaultFlash at 86320 to (size 304) L2 at 86320..86623 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 86320), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 86320), 304, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving S16_Mul_scale, size 76 from DefaultFlash at 87248 to (size 76) L2 at 87248..87323 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87248), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87248), 76, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving S16_Mul_shift, size 76 from DefaultFlash at 87324 to (size 76) L2 at 87324..87399 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87324), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87324), 76, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	/* Static Moving S16_Infos, size 16 from DefaultFlash at 87620 to (size 16) L2 at 87620..87635 */
	AT_DEFAULTFLASH_FS_FC_COPY(&DefaultFlash, ((AT_DEFAULTFLASH_FS_EXT_ADDR_TYPE) model_int8_qdq_L3_Flash + 87620), ((AT_DEFAULTFLASH_FS_INT_ADDR_TYPE) model_int8_qdq_L2_Memory + 87620), 16, 0, UchanHF1);
	AT_DEFAULTFLASH_FS_FC_WAIT(&DefaultFlash, UchanHF1);
	return AT_NO_ERROR;
}
void model_int8_qdqCNN_ConstructCluster()

{
}
int  model_int8_qdqCNN_Destruct()

{
	AT_L2_FREE(0, model_int8_qdq_L2_Memory_Dyn, 689920);
	AT_L2_FREE(0, model_int8_qdq_L2_Memory, 87660);
	AT_L1_FREE(0, model_int8_qdq_L1_Memory, 114328);
	AT_DEFAULTFLASH_FS_CLOSE(&DefaultFlash);
	return 0;
}
int model_int8_qdqCNN_Memory(AT_MEM_TYPE Which)

{
	switch (Which) {
		case AT_L1_MEM:     return 114328; /* L1 Memory */
		case AT_L2_MEM:     return 87660; /* L2 Memory, permanent */
		case AT_L2_DYN_MEM: return 689920; /* L2 Memory, dynamic */
		case AT_L3_MEM:     return 0; /* L3 Memory, permanent */
		case AT_L3_DYN_MEM: return 0; /* L3 Memory, dynamic */
		default:            return 0;
	}
}
unsigned int AT_GraphPerf[6];
unsigned int AT_GraphPerf_CNN_Total = 0;
unsigned int AT_GraphOperInfosNames[6] = {
	12192768,
	19305216,
	20377728,
	20377728,
	40755456,
	0,
};
char *AT_GraphNodeNames[6] = {
	"S4__net_net_0_Conv",
	"S7__net_net_2_Conv",
	"S10__net_net_4_Conv",
	"S13__net_net_6_Conv",
	"S16__net_net_8_Conv",
	"IO_Wait",
};
int  model_int8_qdqCNN(
		signed char * __restrict__ Input_1,
		signed char * __restrict__ Output_1)

{
	unsigned int Start_IO;
	AT_GraphPerf_CNN_Total = gap_cl_readhwtimer();
	AT_GraphPerf[0] = gap_cl_readhwtimer();
	AT_GraphPerf[5] = 0;
	S4__net_net_0_Conv(
		((signed char * __restrict__) Input_1), /* In */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory+86624)), /* Filter */
		((signed int * __restrict__) (model_int8_qdq_L2_Memory+87480)), /* Bias */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory_Dyn+238336)), /* Out */
		((unsigned char * __restrict__) (model_int8_qdq_L2_Memory+87636)), /* Scale */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory+87648)), /* ScaleN */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory+87556)) /* Infos */
	);
	AT_GraphPerf[0] = gap_cl_readhwtimer() - AT_GraphPerf[0];
	AT_GraphPerf[1] = gap_cl_readhwtimer();
	S7__net_net_2_Conv(
		((signed char * __restrict__) (model_int8_qdq_L2_Memory_Dyn+238336)), /* In */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory+84476)), /* Filter */
		((signed int * __restrict__) (model_int8_qdq_L2_Memory+87020)), /* Bias */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory_Dyn+0)), /* Out */
		((unsigned char * __restrict__) (model_int8_qdq_L2_Memory+87516)), /* Scale */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory+87536)), /* ScaleN */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory+87572)) /* Infos */
	);
	AT_GraphPerf[1] = gap_cl_readhwtimer() - AT_GraphPerf[1];
	AT_GraphPerf[2] = gap_cl_readhwtimer();
	S10__net_net_4_Conv(
		((signed char * __restrict__) (model_int8_qdq_L2_Memory_Dyn+0)), /* In */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory+77976)), /* Filter */
		((signed int * __restrict__) (model_int8_qdq_L2_Memory+86868)), /* Bias */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory_Dyn+238336)), /* Out */
		((unsigned char * __restrict__) (model_int8_qdq_L2_Memory+87400)), /* Scale */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory+87440)), /* ScaleN */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory+87588)) /* Infos */
	);
	AT_GraphPerf[2] = gap_cl_readhwtimer() - AT_GraphPerf[2];
	AT_GraphPerf[3] = gap_cl_readhwtimer();
	S13__net_net_6_Conv(
		((signed char * __restrict__) (model_int8_qdq_L2_Memory_Dyn+238336)), /* In */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory+51984)), /* Filter */
		((signed int * __restrict__) (model_int8_qdq_L2_Memory+86016)), /* Bias */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory_Dyn+0)), /* Out */
		((unsigned char * __restrict__) (model_int8_qdq_L2_Memory+87096)), /* Scale */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory+87172)), /* ScaleN */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory+87604)) /* Infos */
	);
	AT_GraphPerf[3] = gap_cl_readhwtimer() - AT_GraphPerf[3];
	AT_GraphPerf[4] = gap_cl_readhwtimer();
	S16__net_net_8_Conv(
		((signed char * __restrict__) (model_int8_qdq_L2_Memory_Dyn+0)), /* In */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory+0)), /* Filter */
		((signed int * __restrict__) (model_int8_qdq_L2_Memory+86320)), /* Bias */
		((signed char * __restrict__) Output_1), /* Out */
		((unsigned char * __restrict__) (model_int8_qdq_L2_Memory+87248)), /* Scale */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory+87324)), /* ScaleN */
		((signed char * __restrict__) (model_int8_qdq_L2_Memory+87620)) /* Infos */
	);
	AT_GraphPerf[4] = gap_cl_readhwtimer() - AT_GraphPerf[4];
	AT_GraphPerf_CNN_Total = gap_cl_readhwtimer() - AT_GraphPerf_CNN_Total;
	return 0;
}
