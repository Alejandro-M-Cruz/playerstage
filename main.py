import numpy as np


LOG_FILE = "example.log"
LASER_INTERFACE = "laser"
POSITION_INTERFACE = "position2d"


def read_log(log_file: str, interface: str):
    with open(log_file) as f:
        yield from (line for line in f if len(splits := line.split()) > 3 and splits[3] == interface)


if __name__ == "__main__":
    laser_data = read_log(LOG_FILE, LASER_INTERFACE)
    position_data = read_log(LOG_FILE, POSITION_INTERFACE)
    laser_header = next(laser_data)
    position_header = next(position_data)
    laser_readings = np.genfromtxt(laser_data, usecols=range(4, 735))
    positions = np.genfromtxt(position_data, usecols=range(3, 14))
    print(laser_readings.shape)
