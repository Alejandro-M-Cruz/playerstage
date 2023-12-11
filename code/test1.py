import sys

sys.path.insert(0, "/usr/local/lib/python2.7/site-packages")


from playerc import *


client = playerc_client(None, "localhost", 6665)
client.connect()

sonar = playerc_sonar(client, 0)
sonar.unsubscribe()

laser = playerc_laser(client, 0)
laser.subscribe(PLAYER_OPEN_MODE)

position2d = playerc_position2d(client, 2)
position2d.subscribe(PLAYER_OPEN_MODE)

target_x = -4
target_y = -7
target_theta = 0

position2d.set_cmd_pose(target_x, target_y, target_theta, 0)

for attr in dir(laser):
    print(attr)

while True:
    for range_l in laser.ranges:
	print(range_l)

    print(laser.ranges)
    print(position2d.px, position2d.py)
    if abs(position2d.px - target_x) < 0.5 and abs(position2d.py - target_y) < 0.5:
       break
    client.read()

laser.unsubscribe()
position2d.unsubscribe()
client.disconnect()

