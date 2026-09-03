# Arquitectura v0.1

## Flujo
Problema -> Orquestador -> Skill -> Motor -> Evidencia -> Razonamiento IA -> Solución -> Verificación -> Memoria.

## Componentes iniciales
- Orquestador: decide qué capacidad ejecutar.
- Skills: procedimientos reutilizables para resolver clases de problemas.
- Motores: herramientas externas/locales que producen evidencia o ejecutan acciones.
- Verificación: comprueba que la solución funciona.
- Memoria: conserva soluciones y aprendizajes reutilizables.

## Regla de crecimiento
No construir capacidades por anticipación. Una nueva skill nace de una necesidad real y debe demostrar ahorro de tiempo.

## Restricción
Prioridad: local-first, bajo costo, mínima infraestructura y mantenimiento reducido.
