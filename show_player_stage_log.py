import matplotlib.pyplot as plt

from extract_path_scans import ExtractPathScans


def ShowPlayerStageLog(filename, th0):
    path, obs = ExtractPathScans(filename, th0)

    plt.figure()
    plt.axis('equal')
    plt.grid(True)
    plt.xlabel('x (m)')
    plt.ylabel('y (m)')

    trajectory_init_color = [0, 1, 0]  # green
    trajectory_last_color = [1, 0, 0]  # red

    # drawing trajectory points (odometry)
    for i in range(len(path['x'])):
        lambda_ = i / len(path['x'])
        color = [trajectory_init_color[j] * (1 - lambda_) + trajectory_last_color[j] * lambda_ for j in range(3)]
        plt.plot(path['x'][i], path['y'][i], '.', color=color)

    sensory_init_color = [0, 1, 1]  # cyan
    sensory_last_color = [0, 0, 0]  # black

    # drawing sensor readings (laser)
    for i in range(len(obs['x'])):
        lambda_ = i / len(obs['x'])
        color = [sensory_init_color[j] * (1 - lambda_) + sensory_last_color[j] * lambda_ for j in range(3)]
        plt.plot(obs['x'][i], obs['y'][i], '.', color=color)

    plt.show()


if __name__ == '__main__':
    ShowPlayerStageLog('example.log', 0)
