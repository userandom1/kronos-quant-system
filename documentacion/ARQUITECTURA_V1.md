# Arquitectura Kronos Quant System V1

## Flujo general

```text
Datos de mercado
    |
    +-- Market Regime V1
    |
    +-- Market Regime V2
    |
    +-- Comparador Multi-Activo
    |
    +-- Signals V2
            |
            v
       Portfolio V2
            |
            v
       Risk Engine V1


Cadena de opciones QQQ
        |
        +-- Limpieza
        |
        +-- Greeks
        |
        +-- Exposiciones
        |
        +-- Dealer Levels
        |
        +-- Snapshots
        |
        +-- Options Flow V2
        |
        +-- Dealer Engine V4


Todos los motores
        |
        v
     Dashboard
        |
        v
    Release V1