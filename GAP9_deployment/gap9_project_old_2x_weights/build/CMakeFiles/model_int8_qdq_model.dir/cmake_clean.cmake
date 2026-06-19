file(REMOVE_RECURSE
  "."
  "BUILD_MODEL/Genmodel_int8_qdq"
  "BUILD_MODEL/model_int8_qdqKernels.c"
  "BUILD_MODEL/model_int8_qdqKernels.h"
  "CMakeFiles/model_int8_qdq_model"
  "Expression_Kernels.c"
  "model.c"
)

# Per-language clean rules from dependency scanning.
foreach(lang )
  include(CMakeFiles/model_int8_qdq_model.dir/cmake_clean_${lang}.cmake OPTIONAL)
endforeach()
