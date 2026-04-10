import numpy as np

cnt = 1e7
eps = 0.1 + (1.0 - 0.1) * np.exp(
    -1e-6 * cnt
)
print(eps)