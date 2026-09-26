# Kronos Quant System

[![Version](https://img.shields.io/badge/version-v2.0.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.12+-green.svg)]()
[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Multi-Asset](https://img.shields.io/badge/coverage-multi--asset-purple.svg)]()
[![License](https://img.shields.io/badge/license-private-lightgrey.svg)]()

A professional **multi-asset quantitative research and market intelligence platform** built on top of Kronos as a forecasting tool, extended into a broader system for:

- **Market regime analysis**
- **Forecasting**
- **Options and dealer positioning analysis**
- **Portfolio construction**
- **Risk analytics**
- **Deep research workflows**
- **Interactive dashboarding**

> Kronos is used here as **one tool inside the system**, not as the full product itself.

---

## Preview

### Dashboard V2
![Dashboard V2](docs/images/dashboard-v2.png)

### Deep Research
![Deep Research](docs/images/deep-research-qqq.png)

### Options 2D / 3D Analytics
![Options 3D](docs/images/options-3d.png)

---

## What this project does

Kronos Quant System is designed to analyze **any major asset class** instead of remaining limited to a single ETF or ticker.

It supports research and monitoring across:

- **ETFs**
- **Stocks**
- **Indexes**
- **Futures**
- **Forex**
- **Crypto**
- **Options-capable assets**

Core goal:

> Build a practical quantitative platform that helps analyze market context, forecast possible scenarios, inspect options structure, evaluate dealer positioning, construct portfolios, and run asset-level deep research.

---

## Core Modules

### 1. Market Engine
- Universal asset analysis
- Market regime classification
- Relative strength comparison
- Composite signals
- Forecast engine
- Cross-asset analysis

### 2. Options Engine
- Options chain analysis
- Greeks analysis
- Options flow analysis
- Dealer positioning
- Call wall / put wall
- Gamma exposure / Delta exposure / Vanna / Charm
- 2D and 3D visualizations

### 3. Portfolio Engine
- Portfolio construction
- Universal optimizer
- Signal-tilted allocations
- Portfolio metrics
- Correlations
- Rebalancing logic

### 4. Risk Engine
- VaR / CVaR
- Drawdown analysis
- Stress testing
- Risk decomposition
- Position and portfolio risk views

### 5. System / Orchestration Layer
- Release workflows
- Universal orchestration
- Watchlists
- API endpoints
- Dashboard integration
- Deep research execution

---

## Project Structure

```text
kronos/
├── configuracion/
├── core/
│   ├── activos/
│   ├── datos/
│   └── modelos/
├── dashboard/
├── dashboard_v2/
├── herramientas/
├── motor_mercado/
├── motor_opciones/
├── motor_portfolio/
├── motor_riesgo/
├── motor_sistema/
├── motor_validacion/
├── pruebas/
├── resultados/
└── docs/
    └── images/
