from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from log_data import LogData

sns.set_theme(style="ticks")


def plot_time_comparison(groups: dict[str, dict[str, Iterable[LogData]]]):
    fig, ax = plt.subplots(figsize=(16, 11))
    fig.suptitle("Time comparison", fontsize=28)

    times_taken = [
        [(t := log["position_data"]["time"].to_numpy())[-1] - t[0] for log in logs]
        for difficulties in groups.values() for logs in difficulties.values()
    ]
    labels = [f"{a} - {d}" for a, difficulties in groups.items() for d in difficulties.keys()]
    times_taken_df = pd.DataFrame(np.array(times_taken).T, columns=labels)

    sns.swarmplot(times_taken_df, size=14)
    plt.setp(ax.get_xticklabels(), fontsize=12)
    ax.yaxis.grid(True)
    ax.set_ylabel("Time taken (s)", fontsize=24, labelpad=16)
    plt.savefig("plots/time_comparison.png")
    plt.close(fig)


def plot_log_data(log_data: LogData):
    metadata = log_data["metadata"]
    title = f"{metadata['algorithm']} - {metadata['difficulty']} - {metadata['index']}"
    position_data = log_data["position_data"]
    obstacle_data = log_data["obstacle_data"]
    time = position_data["time"].to_numpy()
    px = position_data["px"].to_numpy()
    py = position_data["py"].to_numpy()
    scalar_speed = position_data["scalar_speed"].to_numpy()
    obs_x = np.stack(obstacle_data["obs_x"].values).flatten()
    obs_y = np.stack(obstacle_data["obs_y"].values).flatten()

    fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(16, 18))
    ax6.remove()
    fig.suptitle(title, fontsize=28)
    plt.subplots_adjust(wspace=0.3, hspace=0.4, left=0.1, right=0.9, top=0.9, bottom=0.05)

    ax1.set_title("Path and obstacles")
    ax1.scatter(px, py, c=time, marker=".")
    ax1.scatter(obs_x, obs_y, c="black", marker=".", s=0.1)
    ax1.text(-12, -4, f"{time[-1] - time[0]:.2f} seconds")
    ax1.set_xlabel("x (m)")
    ax1.set_ylabel("y (m)")
    ax1.axis("equal")

    ax2.set_title("Distance to target")
    ax2.plot(time, position_data["distance_to_target"].to_numpy(), linewidth=1)
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Distance to target (m)")

    ax3.set_title("Speed")
    ax3.plot(time, scalar_speed, linewidth=0.5)
    ax3.set_xlabel("Time (s)")
    ax3.set_ylabel("Speed (m/s)")

    ax4.set_title("Acceleration")
    ax4.plot(time, position_data["a"], linewidth=0.5)
    ax4.set_xlabel("Time (s)")
    ax4.set_ylabel("Acceleration (m/s^2)")

    ax5.set_title("Distance to nearest obstacle")
    ax5.plot(time, obstacle_data["distance_to_nearest_obstacle"], linewidth=1)
    ax5.set_xlabel("Time (s)")
    ax5.set_ylabel("Distance to nearest obstacle (m)")

    plt.savefig(f"plots/{title}.png")
    plt.close(fig)

    fig = plt.figure(figsize=(10, 9))
    fig.suptitle(title)

    ax3d = fig.add_subplot(1, 1, 1, projection="3d")
    ax3d.set_title("Path with speed 3D visualization")
    ax3d.scatter3D(px, py, scalar_speed, c=time, marker=".")
    ax3d.set_xlabel("x (m)")
    ax3d.set_ylabel("y (m)", labelpad=14)
    ax3d.set_zlabel("Speed (m/s)", labelpad=25)
    ax3d.tick_params(axis="z", pad=10)
    ax3d.view_init(30, -90)

    plt.savefig(f"plots/{title} - 3d.png")
    plt.close(fig)
