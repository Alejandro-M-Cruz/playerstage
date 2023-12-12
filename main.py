from functools import partial
from typing import TypedDict, Generator

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


class LaserConfig(TypedDict):
    scan_id: int
    min_angle: float
    max_angle: float
    resolution: float
    max_range: float
    count: int


def read_log(log_file: str, interface: str):
    with open(log_file) as f:
        yield from (line for line in f if len(splits := line.split()) > 3 and splits[3] == interface)


def get_laser_dimensions(laser_lines) -> LaserDimensions:
    laser_dimension_names = ["lx", "ly", "la", "sx", "sy"]
    laser_dimension_values = next(laser_lines).split()[7:12]
    return {name: float(value) for name, value in zip(laser_dimension_names, laser_dimension_values)}


def get_laser_config(laser_lines) -> LaserConfig:
    next(laser_lines)
    laser_config_values = next(laser_lines).split()[7:13]
    return {
        "scan_id": int(laser_config_values[0]),
        "min_angle": float(laser_config_values[1]),
        "max_angle": float(laser_config_values[2]),
        "resolution": float(laser_config_values[3]),
        "max_range": float(laser_config_values[4]),
        "count": int(laser_config_values[5])
    }


def get_laser_data(laser_lines):
    next(laser_lines)
    laser_readings = np.genfromtxt(laser_lines, usecols=[0] + list(range(13, 735)))
    times = laser_readings[:, 0]
    ranges_and_intensities = laser_readings[:, 1:].reshape(len(times), -1, 2)
    return ranges_and_intensities


def get_position_data(position_lines):
    next(position_lines)
    position_readings = np.genfromtxt(position_lines, usecols=[0, 7, 8, 9, 10, 11, 12])
    position_fields = ["time", "px", "py", "pa", "vx", "vy", "va"]
    return pd.DataFrame(position_readings, columns=position_fields).set_index("time")


def get_obstacle_positions(position_data, laser_data):
    laser_angles = np.linspace(laser_config["min_angle"], laser_config["max_angle"],
                               laser_config["count"])
    ranges = laser_data[:, :, 0]
    intensities = laser_data[:, :, 1]
    angles = position_data["pa"].to_numpy()[:, None] + laser_angles
    obs_relative_x, obs_relative_y = polar_to_cartesian(ranges, angles)
    return position_data["px"] + obs_relative_x, position_data["py"] + obs_relative_y


def plot_path_and_obstacles(px, py, obs_x, obs_y, duration_seconds, title: str = "Path"):
    plt.scatter(px, py, c=np.arange(len(px)), marker=".")
    plt.scatter(obs_x, obs_y, c="black", marker=".")
    plt.title(title)
    plt.text(-12, -4, f"{duration_seconds:.2f} seconds")
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    plt.axis("equal")
    plt.show()


def polar_to_cartesian(r, theta):
    return r * np.cos(theta), r * np.sin(theta)


if __name__ == "__main__":
    laser_lines = partial(read_log, "example.log", "laser")
    position_lines = partial(read_log, "example.log", "position2d")

    laser_dimensions = get_laser_dimensions(laser_lines())
    laser_config = get_laser_config(laser_lines())
    laser_data = get_laser_data(laser_lines())
    position_data = get_position_data(position_lines())
    # obs_x, obs_y = get_obstacle_positions(position_data, laser_data)
    obs_x, obs_y = [], []
    movement_duration = position_data.index[-1] - position_data.index[0]

    plot_path_and_obstacles(position_data["px"], position_data["py"],
                            obs_x, obs_y,
                            movement_duration)
