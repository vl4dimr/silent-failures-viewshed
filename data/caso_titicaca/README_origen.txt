Procedencia de los ficheros del caso de campo (data/caso_titicaca/)
====================================================================

Todos proceden del deposito del estudio de intervisibilidad de la cuenca del
Titicaca (doi:10.5281/zenodo.22176260), cuyo repositorio local de trabajo es
../paper4/results/. Se copiaron sin modificar y se comprobaron byte a byte
(cmp) el 30/09/2026:

  nulo_rigido.json              identico a paper4/results/nulo_rigido.json
  nulo_rigido_n300.json         identico a paper4/results/nulo_rigido_n300.json
  nulo_rigido_sin_mascara.json  identico a paper4/results/nulo_rigido_sin_mascara.json
  nulos.json                    identico a paper4/results/nulos.json (anadido el 30/09/2026)

Que cifra sale de cada fichero
------------------------------

  z del contraste corregido (5 km)        nulo_rigido.json -> por_alcance.5000.z
  z sin enmascarar el lago (5 km)         nulo_rigido_sin_mascara.json -> por_alcance.5000.z
  z con el recorte ajustado (5 km)        nulo_rigido_n300.json -> por_alcance.5000.z
  fraccion de agua del area corregida     nulo_rigido.json -> fraccion_agua (0.2748)
  fraccion de agua del recorte ajustado   nulo_rigido_n300.json -> fraccion_agua (0.3059)
  numero de sitios del estudio de campo   nulos.json -> parametros.n_sitios (180)
  tasa de aceptacion del nulo (colocaciones aceptadas / intentos)
                                          nulo_rigido.json -> tasa_aceptacion (0.316)
                                          nulo_rigido_n300.json -> tasa_aceptacion (0.056)

Advertencias
------------

- nulo_rigido_sin_mascara.json NO contiene fraccion_agua: su densidad observada
  (0.4094) es la del raster corregido de nulo_rigido.json, asi que la fraccion
  de agua que le corresponde es la de ese fichero (27.5 %), no el 30.6 % del
  recorte ajustado (nulo_rigido_n300.json). El manuscrito anterior escribia
  «30.6 %» junto a la z sin mascara: mezclaba dos rasters.

- «244 de 360 orientaciones» NO esta en ningun fichero de resultados del
  deposito. Aparece solo como comentario en paper4/scripts/p01_terrain.py
  (lineas 35-40) y en el texto de su manuscrito: es una cifra del estudio de
  campo sin fichero que la respalde. La tasa_aceptacion de nulo_rigido_n300.json
  (0.056) mide otra cosa (colocaciones aceptadas sobre intentos, no
  orientaciones que caben). Si el texto la cita, debe hacerlo como cifra
  tomada del estudio de campo con su referencia, no como resultado auditable.

- El numero de sitios de la nube sintetica del laboratorio (32) y los pasos del
  diagnostico D2 (360 orientaciones, una por grado) no son del caso de campo:
  son las constantes N_SITIOS y PASOS_ORIENTACION de scripts/terrain_lab.py, y
  p02_calibracion.py las escribe en calibracion.json -> config.n_sitios y
  config.pasos_orientacion.
