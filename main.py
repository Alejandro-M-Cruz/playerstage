from functools import partial
from typing import TypedDict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from icecream import ic


class LaserDimensions(TypedDict):
    lx: float
    ly: float
    la: float
    sx: float
    sy: float


def read_log(log_file: str, interface: str):
    with open(log_file) as f:
        yield from (line for line in f if len(splits := line.split()) > 3 and splits[3] == interface)


def get_laser_dimensions(laser_lines) -> LaserDimensions:
    laser_dimension_names = ["lx", "ly", "la", "sx", "sy"]
    laser_dimension_values = next(laser_lines).split()[7:12]
    return {name: float(value) for name, value in zip(laser_dimension_names, laser_dimension_values)}


def get_laser_data(laser_lines):
    next(laser_lines)
    laser_readings = np.genfromtxt(laser_lines, usecols=[0] + list(range(7, 735)))
    metadata = laser_readings[:, :7]
    ranges = laser_readings[:, 7::2]
    intensities = laser_readings[:, 8::2]
    laser_data = pd.DataFrame(
        ([*m, r, i] for m, r, i in zip(metadata, ranges, intensities)),
        columns=["time", "scan_id", "min_angle", "max_angle", "resolution", "max_range", "count",
                 "ranges", "intensities"]
    ).astype({"scan_id": "int64", "count": "int64"})
    max_range = laser_data.loc[0, "max_range"]
    laser_data["ranges"] = laser_data["ranges"].apply(lambda r: np.where(r >= max_range, np.nan, r))
    return laser_data


def get_position_data(position_lines):
    next(position_lines)
    position_readings = np.genfromtxt(position_lines, usecols=[0, 7, 8, 9, 10, 11, 12])
    position_fields = ["time", "px", "py", "pa", "vx", "vy", "va"]
    return pd.DataFrame(position_readings, columns=position_fields)


def get_obstacle_data(position_data, laser_data):
    laser_reading = laser_data.loc[0]
    laser_angles = np.linspace(laser_reading["min_angle"], laser_reading["max_angle"],
                               laser_reading["count"])
    pa = position_data["pa"].to_numpy()
    angles = pa.repeat(len(laser_angles)).reshape((-1, len(laser_angles))) + laser_angles
    ranges = np.stack(laser_data["ranges"].values)
    obs_relative_x, obs_relative_y = polar_to_cartesian(ranges, angles)
    row_size = obs_relative_x.shape[1]
    obs_x = position_data["px"].to_numpy().repeat(row_size).reshape(-1, row_size) + obs_relative_x
    obs_y = position_data["py"].to_numpy().repeat(row_size).reshape(-1, row_size) + obs_relative_y
    return pd.DataFrame(
        ([t, x, y] for t, x, y in zip(laser_data["time"], obs_x, obs_y)),
        columns=["time", "obs_x", "obs_y"]
    )


def plot_path_and_obstacles(position_data, obstacle_data, title: str = "Path"):
    time = position_data["time"].to_numpy()
    plt.scatter(position_data["px"], position_data["py"], c=time, marker=".")
    obs_x = np.stack(obstacle_data["obs_x"].values).flatten()
    obs_y = np.stack(obstacle_data["obs_y"].values).flatten()
    plt.scatter(obs_x, obs_y, c="black", marker=".", s=0.1)
    plt.title(title)
    plt.text(-12, -4, f"{time[-1] - time[0]:.2f} seconds")
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    plt.axis("equal")
    plt.show()


def polar_to_cartesian(r, theta):
    return r * np.cos(theta), r * np.sin(theta)


def get_distance_to_target(position_data, target_x, target_y):
    return np.sqrt((position_data["px"] - target_x) ** 2 + (position_data["py"] - target_y) ** 2)


def plot_distance_to_target(time, distance_to_target):
    plt.plot(time, distance_to_target)
    plt.title("Distance to Target")
    plt.xlabel("Time (s)")
    plt.ylabel("Distance (m)")
    plt.show()


if __name__ == "__main__":
    laser_lines = partial(read_log, "example.log", "laser")
    position_lines = partial(read_log, "example.log", "position2d")

    laser_dimensions = get_laser_dimensions(laser_lines())
    laser_data = get_laser_data(laser_lines())
    position_data = get_position_data(position_lines())
    obstacle_data = get_obstacle_data(position_data, laser_data)

    plot_path_and_obstacles(position_data, obstacle_data)

    distance_to_target = get_distance_to_target(position_data, -6, -7.5)
    plot_distance_to_target(position_data["time"], distance_to_target)