from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from functools import partial
from itertools import groupby
from multiprocessing import Pool
from pathlib import Path
from timeit import timeit
from typing import TypedDict

import numpy as np
import pandas as pd
from icecream import ic

from plots import plot_data


class LaserDimensions(TypedDict):
    lx: float
    ly: float
    la: float
    sx: float
    sy: float


def get_log_files(log_dir: str) -> dict[str, str]:
    log_dir = Path(log_dir)
    grouped_log_files = groupby(log_dir.glob("**/*.log"), lambda f: f.parent.stem)
    return {f"{group} {i}": str(log_file)
            for group, log_files in grouped_log_files
            for i, log_file in enumerate(log_files, start=1)}


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


def polar_to_cartesian(r, theta):
    return r * np.cos(theta), r * np.sin(theta)


def process_log_file(log_file: str, title: str = "Log"):
    laser_lines = partial(read_log, log_file, "laser")
    position_lines = partial(read_log, log_file, "position2d")

    laser_dimensions = get_laser_dimensions(laser_lines())
    laser_data = get_laser_data(laser_lines())
    position_data = get_position_data(position_lines())
    obstacle_data = get_obstacle_data(position_data, laser_data)

    plot_data(position_data, obstacle_data, title)


def process_log_dir(log_dir: str):
    log_files = get_log_files(log_dir)
    ic(log_files)
    with Pool() as p:
        p.starmap(process_log_file, [(log_file, title) for title, log_file in log_files.items()], chunksize=3)


def main(log_dir: str):
    process_log_dir(log_dir)


if __name__ == "__main__":
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-l", "--log-dir", help="path to directory containing the log files", default="logs")
    args = vars(parser.parse_args())
    main(args["log_dir"])
