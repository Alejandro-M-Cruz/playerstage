import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


LOG_FILE = "example.log"
LASER_INTERFACE = "laser"
POSITION_INTERFACE = "position2d"
POSITION_FIELDS = ["time", "px", "py", "pa", "vx", "vy", "va"]
LASER_HEADER_FIELDS = ["lx", "ly", "la", "sx", "sy"]
LASER_FIELDS = ["scan_id", "min_angle", "max_angle", "resolution", "max_range", "count"]
LASER_READING = ["range", "intensity"]


def read_log(log_file: str, interface: str):
    with open(log_file) as f:
        yield from (line for line in f if len(splits := line.split()) > 3 and splits[3] == interface)


def get_laser_dimensions():
    laser_lines = read_log(LOG_FILE, LASER_INTERFACE)
    laser_dimension_names = ["lx", "ly", "la", "sx", "sy"]
    laser_dimension_values = next(laser_lines).split()[7:12]
    return {name: float(value) for name, value in zip(laser_dimension_names, laser_dimension_values)}


def get_laser_config():
    laser_lines = read_log(LOG_FILE, LASER_INTERFACE)
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


def get_laser_data():
    laser_lines = read_log(LOG_FILE, LASER_INTERFACE)
    next(laser_lines)
    laser_readings = np.genfromtxt(laser_lines, usecols=[0] + list(range(13, 735)))
    times = laser_readings[:, 0]
    ranges_and_intensities = laser_readings[:, 1:].reshape(len(times), -1, 2)
    print("Ranges and intensities shape:", ranges_and_intensities.shape)
    print("Times shape:", times.shape)
    return ranges_and_intensities


def get_position_data():
    position_data = read_log(LOG_FILE, POSITION_INTERFACE)
    next(position_data)
    position_readings = np.genfromtxt(position_data, usecols=[0, 7, 8, 9, 10, 11, 12])
    return pd.DataFrame(position_readings, columns=POSITION_FIELDS).set_index("time")


if __name__ == "__main__":
    laser_config = get_laser_config()
    laser_dimensions = get_laser_dimensions()
    laser_data = get_laser_data()
    position_data = get_position_data()

    print(laser_dimensions)
    print(laser_config)
    print(position_data.head())


