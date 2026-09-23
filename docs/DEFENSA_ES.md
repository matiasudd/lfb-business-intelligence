# Guia de defensa individual

## Preguntas que ambos deben poder responder

1. Que decision apoya el proyecto? Priorizar zonas para revision operativa; no
   demostrar que una estacion trabaja mal ni decidir automaticamente sus recursos.
2. Que representa una fila? La movilizacion de un vehiculo. Un incidente puede
   tener varias filas validas y no debemos deduplicar por IncidentNumber.
3. Que mide el KPI? P90 del tiempo desde movilizacion hasta llegada, en minutos.
   No incluye la espera desde la llamada ni equivale a la primera llegada.
4. Por que P90? Hace visible la cola de tiempos largos que una mediana oculta.
   Lo acompanamos de volumen, mediana y calidad para no interpretarlo aislado.
5. Por que no imputamos el objetivo? Inventaria tiempos y alteraria el percentil.
6. Por que no eliminamos todos los outliers? Un tiempo largo puede ser real.
   Revisamos consistencia y mostramos sensibilidad antes de decidir.
7. Por que una correlacion alta total-viaje no prueba una causa? El viaje forma
   parte aritmetica del total; no es evidencia causal ni un predictor valido
   disponible al despachar.
8. Como repetiria alguien el trabajo? Instalando requirements, descargando las
   fuentes, comprobando manifest y ejecutando el notebook de principio a fin.
9. Que limita comparar boroughs? Mezcla de incidentes, distancias y disponibilidad
   no observadas; multiples vehiculos por incidente; no ajuste causal.
10. Que cambia en C2? Modelos con variables conocidas al despacho, baseline,
    validacion temporal, evaluacion de errores y respuesta al feedback de C1.

## Ensayo

Cada integrante debe ejecutar el notebook y explicar un grafico y una decision
de limpieza elegidos por el otro. Contrasten cifras con outputs/summary.json y
outputs/audit.json. Registren solo las revisiones realmente hechas en PROCESS_LOG.
La defensa es individual y no permite asistencia de IA en vivo.
