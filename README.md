# Kronos Quant System — V1

![Versión](https://img.shields.io/badge/versión-v1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.12+-green)
![Estado](https://img.shields.io/badge/estado-estable-success)
![Quant](https://img.shields.io/badge/Quant-Research-purple)
![Opciones](https://img.shields.io/badge/Options-Analytics-orange)

Plataforma personal de **investigación cuantitativa, análisis de mercado, opciones, posicionamiento dealer, portfolio y riesgo** desarrollada en Python.

La V1 representa la primera versión completa y estable del sistema, construida principalmente alrededor de **QQQ y un universo multi-activo de referencia**, con integración de señales, modelos, opciones, riesgo, portfolio y visualización.

---

## Vista previa

### Dashboard V1

![Dashboard V1](docs/images/dashboard-v1.png)

### Deep Research V1

![Deep Research V1](docs/images/deep-research-v1.png)

### Delta Call — Superficie 3D

![Delta Call 3D](docs/images/delta-call-superficie3d.png)

### Gamma Call — Superficie 3D

![Gamma Call 3D](docs/images/gamma-call-superficie3d.png)

### Vanna Call — Superficie 3D

![Vanna Call 3D](docs/images/vanna-por-punto-IV-call-3d.png)

---

## Objetivo

El objetivo de Kronos Quant System es centralizar en una única plataforma distintas capas de análisis cuantitativo:

- Régimen de mercado
- Señales cuantitativas
- Forecasting
- Volatilidad
- Opciones
- Greeks
- Options Flow
- Dealer positioning
- Gamma Exposure
- Delta Exposure
- Vanna
- Charm
- Portfolio optimization
- Risk management
- Stress testing
- Visualización 2D y 3D

La plataforma está diseñada principalmente como herramienta de:

- investigación;
- experimentación;
- aprendizaje;
- análisis cuantitativo;
- desarrollo de estrategias.

---

# Arquitectura

```mermaid
flowchart TD

    DATA[Datos de mercado] --> MARKET[Motor de Mercado]
    DATA --> OPTIONS[Motor de Opciones]

    MARKET --> SIGNALS[Señales]
    MARKET --> FORECAST[Forecasting]
    MARKET --> REGIME[Régimen de Mercado]

    OPTIONS --> GREEKS[Greeks]
    OPTIONS --> FLOW[Options Flow]
    OPTIONS --> DEALER[Dealer Engine]

    GREEKS --> DEALER
    FLOW --> DEALER

    SIGNALS --> PORTFOLIO[Portfolio Engine]
    REGIME --> PORTFOLIO

    PORTFOLIO --> RISK[Risk Engine]

    FORECAST --> SYSTEM[Motor del Sistema]
    DEALER --> SYSTEM
    RISK --> SYSTEM

    SYSTEM --> DASHBOARD[Dashboard]