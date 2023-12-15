from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from itertools import groupby
from multiprocessing import Pool
from pathlib import Path
from typing import Iterable, TypeVar, Callable

import numpy as np
import pandas as pd
from icecream import ic

from log_data import LogMetadata, LogData
from plots import plot_log_data, plot_time_comparison

T = TypeVar("T")
K = TypeVar("K")


def get_logs_metadata(log_dir: str) -> Iterable[LogMetadata]:
    """
    Returns a list of log metadata according to the following directory structure:
    log-dir/algorithm/difficulty/*.log
    """
    return (
        {
            "index": i,
            "path": str(log_file),
            "algorithm": algorithm_path.stem,
            "difficulty": difficulty_path.stem
        }
        for algorithm_path in Path(log_dir).iterdir()
        for difficulty_path in algorithm_path.iterdir()
        for i, log_file in enumerate(difficulty_path.glob("*.log"), start=1)
    )


def group_by(iterable: Iterable[T], key_function: Callable[[T], K]) -> dict[K, list[T]]:
    return {key: list(group) for key, group in groupby(iterable, key_function)}


def read_log(log_file: str, interface: str):
    with open(log_file) as f:
        yield from (line for line in f if len(splits := line.split()) > 3 and splits[3] == interface)


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


def get_log_data(log_metadata: LogMetadata) -> LogData:
    laser_data = get_laser_data(read_log(log_metadata["path"], "laser"))
    position_data = get_position_data(read_log(log_metadata["path"], "position2d"))
    obstacle_data = get_obstacle_data(position_data, laser_data)
    return {
        "metadata": log_metadata,
        "laser_data": laser_data,
        "position_data": position_data,
        "obstacle_data": obstacle_data
    }


def process_log_dir(log_dir: str):
    with Pool() as p:
        logs_data = p.map(get_log_data, get_logs_metadata(log_dir), chunksize=3)

    # for log_data in logs_data:
    #     plot_log_data(log_data)

    grouped_by_algorithm = group_by(logs_data, lambda ld: ld["metadata"]["algorithm"])
    logs_data_grouped_by_algorithm_and_difficulty = {
        algorithm: group_by(logs, lambda ld: ld["metadata"]["difficulty"])
        for algorithm, logs in grouped_by_algorithm.items()
    }

    plot_time_comparison(logs_data_grouped_by_algorithm_and_difficulty)


def main(log_dir: str):
    process_log_dir(log_dir)


if __name__ == "__main__":
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-l", "--log-dir", help="path to directory containing the log files", default="logs")
    args = vars(parser.parse_args())
    main(args["log_dir"])
