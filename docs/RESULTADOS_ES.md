# Resultados para estudiar la C1

Estos resultados provienen del notebook ejecutado y de outputs/summary.json,
outputs/audit.json y las tablas por zona y hora. No son mediciones de todo el
universo real de emergencias ni prueban causalidad.

## Cifras principales

- Archivo original 2021-2024: 727.857 filas y 24 columnas.
- Duplicados exactos eliminados en el archivo: 3.922.
- Periodo seleccionado 2023-2024 despues de deduplicar: 384.643 filas.
- Filas excluidas del KPI por ID de movilizacion conflictivo: 16.
- Poblacion elegible: 384.627 movilizaciones; 248.225 IDs de incidente distintos.
- Mediana: 5,65 minutos. P90: 9,20 minutos. Media: 6,0281 minutos.
- 1.288 filas elegibles no tienen borough identificado: permanecen como Unknown.

## Interpretacion

Entre zonas identificadas, Hillingdon presenta el P90 mas alto: 10,67 minutos,
con 12.195 movilizaciones elegibles. La hora agrupada con mayor P90 es 11:00 GMT,
con 10,03 minutos. Estas diferencias justifican estudiar contexto y mezcla de
incidentes, no concluir que una estacion funciona mal.

La regla exploratoria encuentra 19 boroughs candidatos con persistencia minima
de tres meses y 15 con seis meses, sobre enero de 2023 a noviembre de 2024. Cambiar
el minimo mensual entre 50, 100 y 200 filas no cambia esos conteos en este archivo.
Una regla que marca muchas zonas sirve como primera criba, no como prioridad final.

## Limites que deben explicar

Falta el 31 de diciembre de 2024: no decir que hay dos anos completos ni confundir
ausencia de registros con cero emergencias. Todos los registros son Initial y
ningun tiempo supera 20 minutos. La metodologia oficial consultada documenta
exclusiones de tiempos mayores en calculos publicados; el filtro exacto del CSV
no quedo confirmado. No se puede inferir la cola no observada.

El KPI mide movilizacion a llegada de cada vehiculo. No incluye tiempo previo de
llamada, no equivale al primer vehiculo en llegar y no mide exclusivamente incendios.
Las correlaciones de tiempo total con sus componentes incluyen una relacion
aritmetica. Para C2 esos componentes realizados producirian fuga de informacion.

Fuentes: docs/SOURCES.md y tablas calculadas del repositorio.
