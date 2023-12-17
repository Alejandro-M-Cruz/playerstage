import os
import subprocess
import sys
import time

sys.path.insert(0, "/usr/local/lib/python2.7/site-packages")

from playerc import *


def clear_log_dir(log_dir):
    log_files = os.listdir(log_dir)
    for log_file_name in log_files:
        log_file_path = os.path.join(log_dir, log_file_name)
        if os.path.isfile(log_file_path):
            os.remove(log_file_path)


def start_player(config_file):
    return subprocess.Popen(["player", "-d", "9", "-q", config_file])


def move_robot(position2d_index):
    client = playerc_client(None, "localhost", 6665)
    client.connect()

    laser = playerc_laser(client, 0)
    laser.subscribe(PLAYERC_OPEN_MODE)

    position2d = playerc_position2d(client, position2d_index)
    position2d.subscribe(PLAYERC_OPEN_MODE)

    target_x = -8
    target_y = -7.5
    target_theta = 0

    def reached_target():
        x_distance_to_target = abs(target_x - position2d.px)
        y_distance_to_target = abs(target_y - position2d.py)
        is_still = position2d.vx == 0 and position2d.vy == 0 and position2d.va == 0
        return x_distance_to_target < 0.5 and y_distance_to_target < 0.5 and is_still

    position2d.set_cmd_pose(target_x, target_y, target_theta, 1)
    start = time.time()

    while not reached_target():
        client.read()
        if time.time() - start > 300:
            break

    laser.unsubscribe()
    position2d.unsubscribe()
    client.disconnect()


def run_simulation(config_file, position2d_index):
    player_process = start_player(config_file)
    time.sleep(2)
    move_robot(position2d_index)
    player_process.terminate()
    player_process.wait()
    time.sleep(0.5)


if __name__ == "__main__":
    clear_log_dir("/home/ic/logs")
    worlds_dir = "/home/ic/installations/player-stage/stage-2.1.1/worlds/"
    file_names = ["initial-easy.cfg", "changed-easy.cfg", "changed-medium.cfg", "changed-hard.cfg"]

    for config_file_name in file_names:
        config_file = worlds_dir + config_file_name
        for i in range(5):
            run_simulation(config_file, position2d_index=1)
        for i in range(5):
            run_simulation(config_file, position2d_index=2)
