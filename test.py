import numpy as np

# Assuming arr is your original 1D numpy array
arr = np.array([1, 2, 3, 4, 5])

# Reshape each item into a list of itself of size 24
result = arr.repeat(24).reshape((-1, 24))

print(result)