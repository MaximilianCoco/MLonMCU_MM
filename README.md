# ML on MCU project
This is Group 23's codes from the "Machine Learning on Microcontrollers FS2026" course project at ETH Zurich.
We have organized our projects code into its four mayor components which are the model itself, code for the MCU deployment on STMU5 and GAP9 as well as our scripts for our live demo.

**Important:** This repository is solely a collection of codes. These were never designed to run after simply pulling the code.
If you are interested in running the codes on your local machine make sure to update all paths used in the scripts.

Furthermore the training data was not attached into this repo, since all sources are pubicly avaliable, reducing the size of this repo by about 60GB.

## Model and data
Training data mainly consisted of the "M&Ms Dataset for "TinyGLASS: Real-Time Self-Supervised In-Sensor Anomaly Detection", which is publicly avaliable and can be found here: 
https://zenodo.org/records/19186667
Further testing was done on the official MVTec AD 2 dataset, which can be accessed through this link:
https://www.mvtec.com/research-teaching/datasets/mvtec-ad-2

While designing the model the focus lied on the first dataset, further testing on the MVTec MV2 dataset was done, altough performance for these dropped significantly as the problems complexity increases. 
The model is inspired by the tinyGLASS model, replacing the large ResNet-18 backbone by a convolutional one, while still doing unsupervized learning. In detail the model maps an image into a latent representation and learns "prototypes" of good looking M&Ms. After learning we transform any input into latent space and compare its euclidian distance to the prototypes. If it is close enough we consider it to be a normal M&M, otherwise we detect it as an anomaly.
Note that knowlege distillation was attempted on the original tinyGLASSes representation after the adapter, however it ultimately was unsuccessful to capture enough information.
To further downsize our model structured prunning and 16- as well as 8-bit quantizations were applied.
On the M&M dataset the model seems promising tho, reaching AUROC scores of up to 0.96 and image accuracies up to 0.88.

## STMU5
Here we configured the MCU in accordance with the lecture, it runs the 8bit quantized model. The most imprtant file is the app_x_cube_ai.c file, where the handling of the model's in and outputs happen. The final version is found in the test_final version. We uploaded two versions for the sake of completeness - we both worked at the same time on it and not all features made it into the final version.

## GAP9
Working with GAP9 has proven to be quite difficult because the nntool doesn't seem to operate in an intuitive way. Various attempts were made in order to get the nntool to produce an output that corresponds to our model. 

First we wanted to directly use model model_int8_qdq analog to the U5, where it worked flawlessly, but the modelInfos.h file showed that for that approach we get quantization and dequantization layers that make no sense. The nntool forces the asymmetric quantization and dequantization layers into a symmetric form even though it doesn't even need to because they are anyway external, when the final implementation has int8 outputs and inputs, and then it proceeded to ruin all internal values as well even though they would have been symmetric to begin with. 

Second we tried to feed a model that has pre-stripped dequantization and quantization layers to avoid this. This resulted in direct errors that were not resolvable. I don't think this is possible to feed a direct int8 to int8 model, but we don't know for sure.

Third we tried to feed our original pruned but non-quantized float32 model. It didn't like that either because it wanted to recalibrate itself with data.

Forth and last we redid the first approach but brute force the values with the network.c values from U5 identified each layer and forced the corresponding values onto the nntool. This worked and the mdoelInfos.h inside the brute force directory seems to be correct. The brute_force_node_values.py seems to produce completely incorrect and incoherent results though when actually trying to run the inference. 
We believe there is some issue with the format or a wrong value somewhere or some reason brute forcing the values created a wrong system setup that was not producing correct values because we don't understand the GAP9 hardware well enough to see how the values are utilized. 

## Live demo
In here the entire flow for the representation can be found. If you are just interested in the results from the live demo just check out the results folder, there you can find the images which were classified on the STMU5 MCU. 
The demo is designed such that one only needs to execute the demo.bat file. It was designed such that one can send his partner an image through Whatsapp, then the script fetches these and processes the latest ones, after which it goes through the MM test data and analyzes those after a short preprocessing step(cropping, trying to fix lighting). Note that lighting conditions have mayor effects on performance.

