import numpy as np

def check_qscale_qnorm(scale, qscale, qnorm):
    approx = qscale / (2 ** qnorm)
    error_pct = abs(approx - scale) / scale * 100
    print(f"scale={scale:.10f}")
    print(f"approx={approx:.10f}  (QSCALE={qscale} >> QNORM={qnorm})")
    print(f"error={error_pct:.4f}%")

# Check each layer after gen_project by reading the generated graphinfo.h
# Or verify your targets would produce good approximations:
scales = {
    "input":   (0.01845340058207512,    76,  12),
    "conv0":   (0.009542142041027546,   78,  13),  # example - read from your graphinfo
    "conv2":   (0.003998782020062208,   66,  14),
    "conv4":   (0.000694780726917088,   91,  17),
    "conv6":   (0.00039253884460777044, 103, 18),
    "output":  (8.462232653982937e-05,  87,  20),
}
for name, (s, qs, qn) in scales.items():
    print(f"\n{name}:")
    check_qscale_qnorm(s, qs, qn)
