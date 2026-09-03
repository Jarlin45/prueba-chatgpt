# Prueba end-to-end v0.1

## Objetivo
Comprobar que el flujo Problema -> Orquestador -> Skill -> Motor -> Diagnóstico funciona.

## Caso PASS
Entrada:
- authenticated=true
- app_installed=true
- repository_visible=true
- writable=true

Resultado esperado: ningún hallazgo.

## Caso FAIL
Entrada:
- authenticated=true
- app_installed=false
- repository_visible=false
- writable=false

Resultado esperado: hallazgo de acceso incompleto con gravedad medium.

## Nota
La ejecución Python debe hacerse en un entorno de ejecución del repositorio (local/CI). La conexión GitHub usada por ChatGPT permite validar y modificar los archivos, pero no sustituye al runtime Python del proyecto.
