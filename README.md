# Algoritmos VFH y ND en Player/Stage

Esta es una comparación de los algoritmos VFH (Vector Field Histogram) y ND (Nearness Diagram). Para realizarla, se han creado los 3 escenarios o _worlds_ en Player/Stage. Cada uno de ellos presenta una dificultad de navegación distinta para el robot. 

## Escenarios

### easy.world


### medium.world


### hard.world

<br>

## Configuración de los algoritmos
Para probar los algoritmos, se han utilizado, en un principio, los parámetros recomendados en la sección _Example_ de cada uno de ellos. 

En el caso del algoritmo VFH:

```
driver
(
  name "vfh"
  requires ["position:1" "laser:0"]
  provides ["position:0"]
  safety_dist 0.10
  distance_epsilon 0.3
  angle_epsilon 5
)
```
Para el algoritmo ND:
```
driver
(
  name "nd"
  provides ["position2d:1"]
  requires ["output:::position2d:0" "input:::position2d:0" "laser:0" "sonar:0"]

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






