/*
 * DIAGNOSTIC VERSION - Prints input and intermediate outputs to debug divergence
 */

#include "model_int8_qdq.h"
#include "model_int8_qdqKernels.h"
#include "gaplib/fs_switch.h"
#include "measurments_utils.h"

#ifndef STACK_SIZE
#define STACK_SIZE      1024
#endif

AT_DEFAULTFLASH_EXT_ADDR_TYPE model_int8_qdq_L3_Flash = 0;

/* Inputs */
L2_MEM signed char Input_1[150528];
/* Outputs */
L2_MEM signed char Output_1[59584];

/* Intermediate outputs for debugging */
L2_MEM signed char S4_Output[450576];   /* Layer 1 output: 224x224x9 */
L2_MEM signed char S7_Output[112576];   /* Layer 2 output: 112x112x19 */
L2_MEM signed char S10_Output[56152];   /* Layer 3 output: 56x56x38 */
L2_MEM signed char S13_Output[56288];   /* Layer 4 output: 28x28x76 */

/* Copy inputs functions */
switch_fs_t input_fs;
void *Input_File_Input_1;
int Input_File_Input_1_Position;
#define EXPECTED_NUM_ITERATIONS 1

int open_inputs() {
    __FS_INIT(input_fs);
    #ifdef __EMUL__
    Input_File_Input_1 = __OPEN_READ(input_fs, "../Input_1.bin");
    #else
    Input_File_Input_1 = __OPEN_READ(input_fs, "../Input_1.bin");
    #endif
    if (!Input_File_Input_1) return 1;
    Input_File_Input_1_Position = 0;
    return 0;
}

int copy_inputs(int num_iterations) {
    int ret_Input_1 = 0;
    __SEEK(Input_File_Input_1, Input_File_Input_1_Position);
    ret_Input_1 = __READ(Input_File_Input_1, Input_1, 150528);
    if (ret_Input_1 != 150528) {
        return 0;
    }
    Input_File_Input_1_Position = 0;
    return 1;
}

void close_inputs() {
    __CLOSE(Input_File_Input_1);
    __FS_DEINIT(input_fs);
}

void write_outputs() {
    /* DIAGNOSTIC OUTPUT: Print first 20 input values */
    printf("\n=== INPUT VERIFICATION ===\n");
    printf("Input_1 first 20 bytes:\n");
    for (int i = 0; i < 20; i++) {
        printf("input[%d] = %d\n", i, (int)Input_1[i]);
    }
    
    /* DIAGNOSTIC OUTPUT: Print first 20 output values from each layer */
    printf("\n=== LAYER OUTPUTS (first 5 values from each) ===\n");
    printf("S4_Output (Layer 1): ");
    for (int i = 0; i < 5; i++) printf("%d ", (int)S4_Output[i]);
    printf("...\n");
    
    printf("S7_Output (Layer 2): ");
    for (int i = 0; i < 5; i++) printf("%d ", (int)S7_Output[i]);
    printf("...\n");
    
    printf("S10_Output (Layer 3): ");
    for (int i = 0; i < 5; i++) printf("%d ", (int)S10_Output[i]);
    printf("...\n");
    
    printf("S13_Output (Layer 4): ");
    for (int i = 0; i < 5; i++) printf("%d ", (int)S13_Output[i]);
    printf("...\n");
    
    /* FINAL OUTPUT */
    printf("\n=== FINAL OUTPUT (Output_1) first 20 values ===\n");
    printf("OUTPUT_START\n");
    for (int i = 0; i < 20; i++) {
        printf("out[%d] = %d\n", i, (int)Output_1[i]);
    }
    printf("OUTPUT_END\n");
}

void close_outputs() {
}

static void cluster(void * arg)
{
    int iteration = (int) arg;
    model_int8_qdqCNN_ConstructCluster();
    
    printf("\n=== Starting model execution ===\n");
    
    GPIO_HIGH();
    /* Call model with intermediate outputs */
    model_int8_qdqCNN(Input_1, Output_1);
    GPIO_LOW();
    
    printf("Runner completed: %d\n", iteration);
}

int main(int argc, char *argv[])
{
    printf("\n\n\t *** NNTOOL model_int8_qdq DIAGNOSTIC ***\n\n");
    printf("Entering main controller\n");

    OPEN_GPIO_MEAS();
    struct pi_device cluster_dev;
    struct pi_cluster_conf cl_conf;
    pi_cluster_conf_init(&cl_conf);
    cl_conf.cc_stack_size = STACK_SIZE;
    cl_conf.id = 0;
    cl_conf.icache_conf = PI_CLUSTER_MASTER_CORE_ICACHE_ENABLE |
                          PI_CLUSTER_ICACHE_PREFETCH_ENABLE |
                          PI_CLUSTER_ICACHE_ENABLE;

    pi_open_from_conf(&cluster_dev, (void *) &cl_conf);
    if (pi_cluster_open(&cluster_dev)) {
        printf("Cluster open failed !\n");
        return -4;
    }

    int cur_fc_freq = pi_freq_set(PI_FREQ_DOMAIN_FC, FREQ_FC*1000*1000);
    int cur_cl_freq = pi_freq_set(PI_FREQ_DOMAIN_CL, FREQ_CL*1000*1000);
    int cur_pe_freq = pi_freq_set(PI_FREQ_DOMAIN_PERIPH, FREQ_PE*1000*1000);
    if (cur_fc_freq == -1 || cur_cl_freq == -1 || cur_pe_freq == -1) {
        printf("Error changing frequency !\nTest failed...\n");
        return -4;
    }
    printf("FC Frequency = %d Hz CL Frequency = %d Hz PERIPH Frequency = %d Hz\n", 
            pi_freq_get(PI_FREQ_DOMAIN_FC), pi_freq_get(PI_FREQ_DOMAIN_CL), pi_freq_get(PI_FREQ_DOMAIN_PERIPH));

    #ifdef VOLTAGE
    pi_pmu_voltage_set(PI_PMU_VOLTAGE_DOMAIN_CHIP, VOLTAGE);
    #endif
    printf("Voltage: %dmV\n", pi_pmu_voltage_get(PI_PMU_VOLTAGE_DOMAIN_CHIP));

    printf("Constructor\n");
    int ConstructorErr = model_int8_qdqCNN_Construct();
    if (ConstructorErr) {
        printf("Graph constructor exited with error: (%s)\n", GetAtErrorName(ConstructorErr));
        return -6;
    }

    if (open_inputs()) return -7;
    if (open_outputs()) return -8;
    printf("Call cluster\n");

    struct pi_cluster_task task;
    pi_cluster_task(&task, (void (*)(void *))cluster, NULL);
    pi_cluster_task_stacks(&task, NULL, SLAVE_STACK_SIZE);

    int iteration = 0;
    while (iteration < EXPECTED_NUM_ITERATIONS) {
        if (EXPECTED_NUM_ITERATIONS > 1) printf("Iteration: %d of %d\n", iteration, EXPECTED_NUM_ITERATIONS);
        if (!copy_inputs(iteration)) return -9;

        task.arg = (void *)iteration;
        pi_cluster_send_task_to_cl(&cluster_dev, &task);

        write_outputs();
        iteration++;
    }
    
    close_inputs();
    close_outputs();
    model_int8_qdqCNN_Destruct();

    printf("Ended\n");
    return 0;
}
