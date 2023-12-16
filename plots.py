from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from log_data import LogData

sns.set_theme(style="ticks")


def plot_time_comparison(groups: dict[str, dict[str, Iterable[LogData]]]):
    fig, ax = plt.subplots(figsize=(16, 10))
    fig.suptitle("Time comparison", fontsize=28)

    times_taken = [
        [(t := log["position_data"]["time"].to_numpy())[-1] - t[0] for log in logs]
        for difficulties in groups.values() for logs in difficulties.values()
    ]
    labels = [f"{a} - {d}" for a, difficulties in groups.items() for d in difficulties.keys()]
    times_taken_df = pd.DataFrame(np.array(times_taken).T, columns=labels)

    sns.swarmplot(times_taken_df, size=16)
    plt.setp(ax.get_xticklabels(), fontsize=16)
    ax.yaxis.grid(True)
    plt.show()


def plot_log_data(log_data: LogData):
    metadata = log_data["metadata"]
    title = f"{metadata['algorithm']} - {metadata['difficulty']} - {metadata['index']}"
    position_data = log_data["position_data"]
    obstacle_data = log_data["obstacle_data"]
    time = position_data["time"].to_numpy()
    px = position_data["px"].to_numpy()
    py = position_data["py"].to_numpy()
    vx = position_data["vx"].to_numpy()
    vy = position_data["vy"].to_numpy()
    target_x = -6
    target_y = -7.5
    distances_to_target = np.sqrt((px - target_x) ** 2 + (py - target_y) ** 2)
    scalar_speeds = np.sqrt(vx ** 2 + vy ** 2)
    obs_x = np.stack(obstacle_data["obs_x"].values).flatten()
    obs_y = np.stack(obstacle_data["obs_y"].values).flatten()

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(title, fontsize=28)
    plt.subplots_adjust(top=0.85, wspace=0.5, hspace=0.5)

    ax1.set_title("Distance to target")
    ax1.plot(position_data["time"], distances_to_target)
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Distance to target (m)")

    ax2.set_title("Scalar speed vs distance to target")
    ax2.plot(distances_to_target, scalar_speeds)
    ax2.set_xlabel("Distance to target (m)")
    ax2.set_ylabel("Scalar speed (m/s)")
    ax2.invert_xaxis()

    ax3.set_title("Path and obstacles")
    ax3.scatter(position_data["px"], position_data["py"], c=time, marker=".")
    ax3.scatter(obs_x, obs_y, c="black", marker=".", s=0.1)
    ax3.text(-12, -4, f"{time[-1] - time[0]:.2f} seconds")
    ax3.set_xlabel("x (m)")
    ax3.set_ylabel("y (m)")
    ax3.axis("equal")

    ax4.remove()
    ax4 = fig.add_subplot(2, 2, 4, projection="3d")
    ax4.set_title("Path with scalar speed 3D visualization")
    ax4.scatter3D(px, py, scalar_speeds, c=time, marker=".")
    ax4.set_xlabel("x (m)")
    ax4.set_ylabel("y (m)")
    ax4.set_zlabel("Scalar speed (m/s)")

    plt.show()
