# Algoritmos VFH y ND en Player/Stage

Esta es una comparación de los algoritmos VFH (Vector Field Histogram) y ND (Nearness Diagram). Para realizarla, se han creado 4 escenarios o _worlds_ en Player/Stage. Cada uno de ellos presenta una dificultad de navegación distinta para el robot. 

<br>

## Escenarios

### easy.world
![image](https://github.com/Alejandro-M-Cruz/playerstage/assets/113340373/14a307fb-c6ef-4288-8417-1d820ab56f15)

### medium.world
![image](https://github.com/Alejandro-M-Cruz/playerstage/assets/113340373/528fe592-a1eb-4958-ab22-16c85056251d)

### hard.world
![image](https://github.com/Alejandro-M-Cruz/playerstage/assets/113340373/3f4f7689-82a9-46a6-90d9-ecc100668059)

### realistic.world
![realistic-world-with-goal](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/5a357ef5-f33c-4c21-b6c0-84ccffe92b2d)

<br>

## Configuración de los algoritmos
Para probar los algoritmos, se han utilizado, en un principio, los parámetros recomendados en la sección _Example_ de la documentación correspondiente a cada uno de ellos. 

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
Para evitar realizar las simulaciones manualmente, se hizo uso del módulo `playerc` para Python. El script `run_simulation.py`, realiza **5 pruebas** de cada algoritmo, con cada uno de los ficheros de configuración en la lista `file_names`. En este caso, se están probando ambos algoritmos con dos configuraciones distintas: 

- La configuración inicial, contenida en el fichero `initial-easy.cfg`, que utiliza el escenario fácil (`easy.world`).
- La configuración modificada, contenida en los ficheros `changed-easy.cfg`, `changed-medium.cfg` y `changed-hard.cfg`. La configuración es la misma para los tres ficheros, cambiando únicamente el escenario en que se ejecutan: `easy.world`, `medium.world` y `hard.world`, respectivamente.

Se muestra a continuación dicho script:
```python
import os
import subprocess
import sys
from time import sleep

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


def move_robot(target, position2d_index):
    client = playerc_client(None, "localhost", 6665)
    client.connect()

    laser = playerc_laser(client, 0)
    laser.subscribe(PLAYERC_OPEN_MODE)

    position2d = playerc_position2d(client, position2d_index)
    position2d.subscribe(PLAYERC_OPEN_MODE)

    target_x, target_y, target_theta = target

    def reached_target():
        x_distance_to_target = abs(target_x - position2d.px)
        y_distance_to_target = abs(target_y - position2d.py)
        is_still = position2d.vx == 0 and position2d.vy == 0 and position2d.va == 0
        return x_distance_to_target < 0.5 and y_distance_to_target < 0.5 and is_still

    position2d.set_cmd_pose(target_x, target_y, target_theta, 1)
  
    for i in range(3000):
        client.read()
        if reached_target():
            break

    laser.unsubscribe()
    position2d.unsubscribe()
    client.disconnect()


def run_simulation(config_file, position2d_index):
    player_process = start_player(config_file)
    sleep(2)
    target = (-1, 6, 0) if "realistic" in config_file else (-8, -7.5, 0)
    move_robot(target, position2d_index)
    player_process.terminate()
    player_process.wait()
    sleep(0.5)


if __name__ == "__main__":
    clear_log_dir("/home/ic/logs")
    worlds_dir = "/home/ic/installations/player-stage/stage-2.1.1/worlds/"
    file_names = [
        "initial-easy.cfg",
        "changed-easy.cfg",
        "changed-medium.cfg",
        "changed-hard.cfg",
        "changed-realistic.cfg"
    ]

    for config_file_name in file_names:
        config_file = worlds_dir + config_file_name
        for i in range(5):
            run_simulation(config_file, position2d_index=1)
        for i in range(5):
            run_simulation(config_file, position2d_index=2)

```
Las pruebas tienen una duración máxima de 5 minutos. Si alguna prueba excede los 5 minutos, se para automáticamente y se considera que no se ha alcanzado el objetivo.

<br>

## Lectura de ficheros de log y representación gráfica de los datos
El script `main.py` toma como parámetro el directorio donde se encuentran los ficheros de log, por defecto `./logs`. Los ficheros de logs deben estar organizados de la siguiente manera: `<directorio de logs>/<algoritmo>/<dificultad>/*.log`. Por ejemplo: `/home/user/logs/vfh/easy/mydata2023_12_16_12_52_10.log`. Una vez localizados los ficheros, se leen sus datos y se representan mediante gráficas, gracias a las librerías `numpy`, `pandas`, `matplotlib` y `seaborn`. Por cada fichero de log, se almacenarán dos imágenes en el directorio `plots`, con la representación gráfica de los registros contenidos en dicho fichero. La primera de las imágenes contendrá los siguientes gráficos: 

![nd - easy - 3](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/00521fa8-30ad-4b06-a4b9-e1bb60cd1dae)

La segunda imagen, contendrá una representación 3D de la trayectoria seguida, con el valor de la velocidad escalar en cada punto de la misma:

![nd - easy - 3 - 3d](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/47ee94c4-4fcc-4040-adc2-20f7ab785d95)

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

- Configuración inicial:

![vfh-initial - easy - 2](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/42c6de58-9ade-4b6e-8d49-e8ee8e46613b)
![vfh-initial - easy - 2 - 3d](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/c709dab2-5c4e-4a1a-b118-8413510c0b2e)

- Configuración modificada:

![vfh - easy - 2](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/3c09a1d0-6e18-4ad4-a7df-564912e022bf)
![vfh - easy - 2 - 3d](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/34137bff-f3b8-4271-97c4-d7b9120c96a9)


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

- Configuración inicial:

![nd-initial - easy - 5](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/909463d4-71ba-400a-9f95-3ce2d83391ae)
![nd-initial - easy - 5 - 3d](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/d2f91167-1bfc-4aee-b99f-e74ef0770b54)

- Configuración modificada:

![nd - easy - 5](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/0205c9b3-e441-4a6c-9fa0-4e2961374d1a)
![nd - easy - 5 - 3d](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/b1d62b24-f8e2-4cd2-bf1c-d65759867dd2)

<br>

## Resultados
La siguiente gráfica, titulada _Time comparison_, muestra el tiempo, en segundos, que el robot ha tardado en alcanzar el objetivo en cada escenario con cada algoritmo. 

![time_comparison](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/744fe2d5-d185-4fd8-8e80-fc0a6b19ec8c)

De nuevo, se observa como la configuración inicial del algoritmo VFH tiene, en promedio, un rendimiento significativamente peor en comparación con la configuración final. Asimismo, los cambios en la configuración del algoritmo ND parecen empeorarlo ligeramente, aunque, tal y como se mencionó anteriormente, esto se debe a la reducción de la tolerancia.


En cuanto al **algoritmo ND**, se observa un progresivo aumento del tiempo según aumenta la dificultad de los escenarios, siendo las 5 pruebas realizadas en cada escenario muy similares entre sí, tal y como se puede ver en el siguiente ejemplo:

![nd - medium - 3](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/d1173456-241f-47e4-8367-3ae2c13d1ed9)

![nd - medium - 4](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/dc185a35-05c4-4e7f-9834-8f74c42d77c0)


En las pruebas del **algoritmo VFH**, se aprecia una variación mucho mayor entre cada una, tanto en la trayectoria seguida como en el tiempo consumido. Las siguientes imágenes, correspondientes al escenario fácil (_easy.world_), lo ejemplifican:

![vfh - easy - 4](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/3f027ea6-5b6f-4b2d-b2fb-ab188ecdaed7)

![vfh - easy - 5](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/bcc680b8-e984-45fe-8977-a1d3394bfc8b)

Por otra parte, ninguna de las 5 pruebas de este algoritmo fue capaz de alcanzar el objetivo en el escenario difícil, _hard.world_. Todas ellas fueron detenidas a los 5 minutos, aunque algunas muestran un mayor progreso que otras, como se puede ver a continuación:

![vfh - hard - 1](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/aea06720-c151-45f7-93b2-4bdb1ac0763c)

![vfh - hard - 2](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/3c5428e1-94da-419b-bf74-ded025cb4f89)


## Conclusión
Finalmente, se puede concluir que, al menos con los datos obtenidos en esta comparación, el algoritmo ND tiene un rendimiento muy superior al obtenido con el algoritmo VFH. Tanto es así, que en las 15 pruebas realizadas con cada uno de ellos, solo en una el algoritmo VFH ha dado mejor resultado. Es el caso de la cuarta prueba en el escenario fácil, que se muestra a continuación:

![vfh - easy - 4](https://github.com/Alejandro-M-Cruz/vfh-vs-nd-playerstage/assets/113340373/07d40146-92f9-4467-8c33-0cfc5d8b3bd5)

Aún así, esta prueba ha sido la excepción, puesto que en el resto de pruebas para este mismo escenario, el algoritmo ND ha completado la ruta en menor tiempo.

Estas diferencias de tiempo se deben a que, mientras que el algoritmo ND mantiene el robot en movimiento en todo momento y sortea los obstáculos progresivamente, girando mientras avanza, el algoritmo VFH determina trayectorias más rectas y, al toparse con un obstáculo, detiene el robot y lo hace rotar sobre sí mismo hasta encontrar una nueva trayectoria, repitiendo sucesivamente esta secuencia. Asimismo, el algoritmo VFH tiende a estancarse ante la presencia de varios obstáculos alrededor del robot.
