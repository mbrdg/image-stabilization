import numpy as np
import math
import pandas as pd
from matplotlib import pyplot as plt

SMOOTHING_RADIUS = 5  # temporary


def average_filter(curve, radius):
    window_size = 2 * radius + 1
    # Define the filter
    f = np.ones(window_size) / window_size
    # Add padding to the boundaries
    curve_pad = np.lib.pad(curve, (radius, radius), "edge")
    # Apply convolution
    curve_smoothed = np.convolve(curve_pad, f, mode="same")
    # Remove padding
    curve_smoothed = curve_smoothed[radius:-radius]
    # return smoothed curve
    return curve_smoothed


def smooth(trajectory):
    smoothed_trajectory = np.copy(trajectory)
    # Filter the x, y and angle curves
    for i in range(3):
        smoothed_trajectory[:, i] = average_filter(
            trajectory[:, i], radius=SMOOTHING_RADIUS
        )

    return smoothed_trajectory


# if __name__ == "__main__":
