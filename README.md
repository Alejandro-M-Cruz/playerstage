# Algoritmos VFH y ND en Player/Stage

Esta es una comparación de los algoritmos VFH (Vector Field Histogram) y ND (Nearness Diagram). Para realizarla, se han creado los 3 escenarios o _worlds_ en Player/Stage. Cada uno de ellos presenta una dificultad de navegación distinta para el robot. 

<br>

## Escenarios

### easy.world
![image](https://github.com/Alejandro-M-Cruz/playerstage/assets/113340373/14a307fb-c6ef-4288-8417-1d820ab56f15)

### medium.world
![image](https://github.com/Alejandro-M-Cruz/playerstage/assets/113340373/e6033d44-2434-48f6-af5e-1bfabbbe750a)

### hard.world
![image](https://github.com/Alejandro-M-Cruz/playerstage/assets/113340373/82d14890-7401-495c-b4ec-acc38ef5cfc3)

<br>

## Configuración de los algoritmos
Para probar los algoritmos, se han utilizado, en un principio, los parámetros recomendados en la sección _Example_ de cada uno de ellos. 

En el caso del algoritmo [VFH](https://playerstage.sourceforge.net/doc/Player-2.0.0/player/group__driver__vfh.html):

```cfg
driver
(
  name "vfh"
  requires ["position:0" "laser:0"]
  provides ["position:1"]
  safety_dist 0.10
  distance_epsilon 0.3
  angle_epsilon 5
)
```

Para el algoritmo [ND](https://playerstage.sourceforge.net/doc/Player-2.0.0/player/group__driver__nd.html):

```cfg
driver
(
  name "nd"
  requires ["output:::position2d:0" "input:::position2d:0" "laser:0" "sonar:0"]
  provides ["position2d:2"]

  max_speed [0.3 30.0]
  min_speed [0.1 10.0]
  goal_tol [0.3 15.0]
  wait_on_stall 1

  rotate_stuck_time 5.0
  translate_stuck_time 5.0
  translate_stuck_dist 0.15
  translate_stuck_angle 10.0

  avoid_dist 0.4
  safety_dist 0.0

  laser_buffer 1
  sonar_buffer 1
)
```

Para poder procesar los datos de posición y las lecturas del láser del robot, mediante ficheros de log, se ha configurado el driver [writelog](https://playerstage.sourceforge.net/doc/Player-2.0.0/player/group__driver__writelog.html) de la siguiente manera:


```cfg
# Log data from laser:0 and position2d:0 to "/home/ic/logs/mydata_YYYY_MM_DD_HH_MM_SS.log"
driver(
  name "writelog"
  log_directory "/home/ic/logs"
  basename "mydata"
  requires ["laser:0" "position2d:0"]
  provides ["log:0"]
  alwayson 1
  autorecord 1
)
``` 

<br>

## Ejecución de las simulaciones 
Para evitar realizar las simulaciones manualmente, se hizo uso del módulo `playerc` para Python. El script `run_simulation.py`, realiza 5 pruebas de cada algoritmo con cada uno de los ficheros de configuración en la lista `file_names`. En este caso, se están probando ambos algoritmos con dos configuraciones distintas: 

- La configuración inicial, contenida en el fichero `initial-easy.cfg`, que utiliza el escenario fácil (`easy.world`).
- La configuración modificada, contenida en los ficheros `changed-easy.cfg`, `changed-medium.cfg` y `changed-hard.cfg`. La configuración es la misma para los tres ficheros, cambiando únicamente el escenario en que se ejecutan: `easy.world`, `medium.world` y `hard.world`, respectivamente.

Se muestra a continuación dicho script:
```python
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

```

<br>

## Lectura de ficheros de log y representación gráfica de los datos
El script `main.py` toma como parámetro el directorio donde se encuentran los ficheros de log, por defecto `./logs`. Los ficheros de logs deben estar organizados de la siguiente manera: `<directorio de logs>/<algoritmo>/<dificultad>/*.log`. Por ejemplo: `/home/user/logs/vfh/easy/mydata2023_12_16_12_52_10.log`. Una vez localizados los ficheros, se leen sus datos y se representan mediante gráficas, gracias a las librerías `numpy`, `pandas`, `matplotlib` y `seaborn`. Por cada fichero de log, se almacenará una imagen en el directorio `plots`, con la representación gráfica de los datos de dicho fichero. 

![vfh - easy - 3](https://github.com/Alejandro-M-Cruz/playerstage/assets/113340373/62f48df8-6b22-495d-a056-fcf1b089a858)

<br>

## Modificaciones en la configuración de los algoritmos
Tras realizar las lecturas con los parámetros de configuración inicial, es posible apreciar algunas posibles mejoras. En primer lugar, la tolerancia utilizada al determinar si el robot ha alcanzado su objetivo es considerablemente alta en ambos algoritmos, 0.3 metros para ser exactos. Esto hace que el robot determine que ha alcanzado la meta demasiado pronto. Es por ello que el valor de dicha tolerancia se ha reemplazado por 0.1. Lo mismo ocurre con la tolerancia del ángulo objetivo. 

Además de esto, en el algoritmo VFH, se ha modificado la velocidad máxima, que por defecto es de 0.2 m/s, a 0.3 m/s, consiguiendo una reducción significativa del tiempo que el robot tarda en llegar al objetivo. Se muestra a continuación la configuración final del driver correspondiente:

```cfg
driver
(
  name "vfh"
  requires ["position:0" "laser:0"]
  provides ["position:1"]
  safety_dist 0.10
  distance_epsilon 0.1
  angle_epsilon 5
  max_speed 0.3
)
```

Como se puede observar en el siguiente ejemplo, estas modificaciones mejoran considerablemente el rendimiento del algoritmo.



Por último, se ha cambiado la configuración del algoritmo ND, para que este solo utilice el sensor láser y no el ultrasónico. Este cambio tiene el objetivo de lograr una comparacón más uniforme con el primer algoritmo, dado que VFH solo puede utilizar uno de los dos sensores, el láser en este caso. La configuración final para este algoritmo es la siguiente:

```cfg
driver
(
  name "nd"
  requires ["output:::position2d:0" "input:::position2d:0" "laser:0"]
  provides ["position2d:2"]

  max_speed [0.3 30.0]
  min_speed [0.1 10.0]
  goal_tol [0.1 5.0]
  wait_on_stall 1

  rotate_stuck_time 5.0
  translate_stuck_time 5.0
  translate_stuck_dist 0.15
  translate_stuck_angle 10.0

  avoid_dist 0.4
  safety_dist 0.0

  laser_buffer 1
)
```

A pesar de que, al realizar este cambio, en las gráficas se muestra un ligero incremento del tiempo tomado para alcanzar el objetivo, esto se debe a la reducción de la tolerancia, que hace que el robot tenga que quedar más cerca del objetivo antes de determinar que lo ha alcanzado, por lo que en realidad el rendimiento del algoritmo no se ha visto afectado de manera significativa.



