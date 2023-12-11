import numpy as np
import re


def ExtractPathScans(filename, th0):
    rangerName = 'laser'
    positionName = 'position2d'

    obs = {'x': [], 'y': []}
    path = {'time': [], 'x': [], 'y': [], 'th': [], 'vx': [], 'vy': [], 'vth': []}

    try:
        fP = open(filename, 'r')
    except FileNotFoundError:
        print(f'GetObstacles: ERROR file not found {filename}')
        return path, obs

    # First ranger header
    rangerLine, pos = NextTokenLine(fP, rangerName)

    # Ranger configuration
    rangerLine, pos = NextTokenLine(fP, rangerName)

    rangerConf = list(map(float, re.findall(r"[-+]?\d*\.\d+|\d+", rangerLine[pos+len(rangerName)+1:])))

    minAngle = rangerConf[4]
    maxAngle = rangerConf[5]
    maxDist = rangerConf[7]

    # First position header
    positionLine, pos = NextTokenLine(fP, positionName)

    finish = False
    while not finish:
        # Next position
        positionLine, pos = NextTokenLine(fP, positionName)

        if positionLine:
            positionData = list(map(float, re.findall(r"[-+]?\d*\.\d+|\d+", positionLine[0:pos-1])))
            path['time'].append(positionData[0])
            positionData = list(map(float, re.findall(r"[-+]?\d*\.\d+|\d+", positionLine[pos+len(positionName)+1:])))
            path['x'].append(positionData[3])
            path['y'].append(positionData[4])
            path['th'].append(positionData[5])
            path['vx'].append(positionData[6])
            path['vy'].append(positionData[7])
            path['vth'].append(positionData[8])

            # Next scan
            rangerLine, pos = NextTokenLine(fP, rangerName)

            if rangerLine:
                rangerData = list(map(float, re.findall(r"[-+]?\d*\.\d+|\d+", rangerLine[pos+len(rangerName)+1:])))
                nData = rangerData[8]
                rangerData = rangerData[9::2]
                rangerData = [value if value < maxDist else np.nan for value in rangerData]

                angles = np.linspace(minAngle, maxAngle, int(nData))

                xo = np.multiply(rangerData, np.cos(np.add(angles, path['th'][-1])))
                yo = np.multiply(rangerData, np.sin(np.add(angles, path['th'][-1])))

                obs['x'].append(np.add(xo, path['x'][-1]))
                obs['y'].append(np.add(yo, path['y'][-1]))
            else:
                finish = True
        else:
            finish = True

    for i in range(len(obs['x'])):
        r = np.array(obs['x'][i])
        theta = np.array(obs['y'][i])
        obs['x'][i] = r * np.cos(theta)
        obs['y'][i] = r * np.sin(theta)

        r = np.array(path['x'][i])
        theta = np.array(path['y'][i])
        path['x'][i] = r * np.cos(theta)
        path['y'][i] = r * np.sin(theta)

    return path, obs

def NextTokenLine(fP, token):
    for line in fP:
        pos = line.find(token)
        if pos != -1:
            return line, pos
    return None, None


