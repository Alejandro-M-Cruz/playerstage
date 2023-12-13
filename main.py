from functools import partial
from typing import TypedDict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


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
    obs_x = flatten(obstacle_data["obs_x"].values)
    obs_y = flatten(obstacle_data["obs_y"].values)
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


def plot_speed_and_distance_to_target(position_data, distance_to_target):
    fig, (ax1, ax2) = plt.subplots(2, 1)
    ax1.plot(position_data["time"], distance_to_target)
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Distance to target (m)")
    ax2.plot(distance_to_target, get_scalar_speed(position_data))
    ax2.set_xlabel("Distance to target (m)")
    ax2.set_ylabel("Scalar speed (m/s)")
    ax2.invert_xaxis()
    plt.subplots_adjust(hspace=0.5)
    plt.show()


def plot_3d_path(position_data, title="3D path"):
    axes = plt.axes(projection="3d")
    scalar_velocities = np.sqrt(get_scalar_speed(position_data))
    axes.scatter3D(position_data["px"], position_data["py"], scalar_velocities, c=position_data["time"], marker=".")
    axes.set_title(title)
    axes.set_xlabel("x (m)")
    axes.set_ylabel("y (m)")
    axes.set_zlabel("Scalar speed (m/s)")
    plt.show()


def flatten(sequence):
    return np.stack(sequence).flatten()


def get_scalar_speed(position_data):
    return np.sqrt(position_data["vx"] ** 2 + position_data["vy"] ** 2)


if __name__ == "__main__":
    laser_lines = partial(read_log, "example.log", "laser")
    position_lines = partial(read_log, "example.log", "position2d")

    laser_dimensions = get_laser_dimensions(laser_lines())
    laser_data = get_laser_data(laser_lines())
    position_data = get_position_data(position_lines())
    obstacle_data = get_obstacle_data(position_data, laser_data)

    plot_path_and_obstacles(position_data, obstacle_data)

    distance_to_target = get_distance_to_target(position_data, -6, -7.5)
    plot_speed_and_distance_to_target(position_data, distance_to_target)

    plot_3d_path(position_data)
