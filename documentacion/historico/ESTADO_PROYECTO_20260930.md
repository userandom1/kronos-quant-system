ESTADO_PROYECTO.md
Quant Platform — Estado actual
Última actualización:
30 de septiembre de 2026
El código real, Git y los tests prevalecen si existe alguna discrepancia.
Visión
El proyecto comenzó como un sistema centrado en Kronos y QQQ.
Actualmente es una plataforma Quant multi-activo orientada a:
Market Intelligence
Forecasting
Options
Greeks
Dealer Positioning
Options Flow
Portfolio
Risk
Scenario Analysis
Deep Research
Dashboard
Kronos ya no es la identidad del proyecto, sino un modelo dentro del Forecast Engine.
Ruta
D:\02_Herramientas\kronos
Python:
3.12.9
Entorno:
D:\02_Herramientas\kronos\.venv
GPU conocida:
NVIDIA GTX 1080 Ti
11 GB VRAM
PyTorch 2.6.0+cu126
CUDA disponible
Git
Remoto:
https://github.com/userandom1/kronos-quant-system.git
Upstream Kronos:
https://github.com/shiyu-coder/Kronos.git
Ramas conocidas:
kronos-quant-v1
quant-platform-v2
master
Tags:
v1.0.0
v2.0.0
V1
Estado:
TERMINADA / ESTABLE
Rama:
kronos-quant-v1
Comando:
python -m motor_sistema.release_v1
Dashboard:
python -m motor_sistema.release_v1 --dashboard
Incluye:
- Market Engine
- Signals
- Forecasting
- Portfolio
- Risk
- Options
- Greeks
- Options Flow
- Dealer Engine
- Scenario Engine
- Dashboard
V2
Estado:
OPERATIVA
Rama:
quant-platform-v2
Introduce:
- arquitectura multi-activo;
- capabilities;
- proveedores abstractos;
- Market Engine universal;
- Forecast Engine;
- Options Engine;
- Portfolio;
- Risk;
- API;
- Dashboard;
- Deep Research;
- visualización avanzada.
Activos
EQUITY
ETF
INDEX
FUTURE
FOREX
CRYPTO
BOND
COMMODITY
OPTION
UNKNOWN
Datos
Proveedor principal:
yfinance
Capacidades:
- OHLCV;
- históricos;
- intradía;
- metadata;
- vencimientos;
- option chains;
- normalización;
- retries;
- fallback;
- cache.
Limitación principal:
dependencia alta de yfinance
Market Engine
Incluye:
- retornos;
- tendencia;
- momentum;
- volatilidad;
- drawdown;
- beta;
- correlación;
- régimen.
Regímenes conocidos:
RISK_ON_FUERTE
RISK_ON
NEUTRAL
Forecast Engine
Modelos:
Drift
Momentum
Kronos
Ensemble
Horizontes:
5D
20D
60D
Métricas usadas:
RMSE
MAE
Directional Accuracy
Information Coefficient
R²
Sharpe
Maximum Drawdown
Options Engine
Variables principales:
tipo_opcion
strike
vencimiento
DTE
bid
ask
mid
IV
volumen
Open Interest
moneyness
Greeks:
Delta
Gamma
Theta
Vega
Vanna
Charm
Dealer Engine
Calcula proxies de:
Net GEX
Net DEX
Net Vanna
Net Charm
Gamma Flip
Positive Gamma Node
Negative Gamma Node
Call Wall
Put Wall
Importante:
los resultados son proxies y no posiciones reales observadas
Problema conocido de expiraciones
Los Walls agregados pueden quedar dominados por Open Interest lejano.
Pendiente:
GEX por expiración
DEX por expiración
Walls por expiración
Gamma Flip por expiración
Deep Research
Archivos conocidos:
motor_mercado/deep_research_activo.py
motor_sistema/deep_research.py
pruebas/probar_deep_research.py
Comando:
python -m motor_sistema.deep_research TICKER
Pipeline aproximado:
Activo
↓
Datos
↓
Market
↓
Forecast
↓
Regime
↓
Options
↓
Greeks
↓
Dealer
↓
Gráficas
↓
Scenario Engine
↓
Resumen
Gráficas
Archivo conocido:
motor_opciones/graficas_avanzadas.py
2D:
Delta
Gamma
Theta
Vega
Vanna
Charm
GEX
DEX
Open Interest
3D:
IV Surface
Delta Surface
Gamma Surface
Theta Surface
Vega Surface
Vanna Surface
Charm Surface
Scenario Engine
Archivo:
motor_opciones/escenarios_opciones.py
Genera:
Spot × IV × P&L
Spot × Tiempo × P&L
P&L al vencimiento
Theta decay
Delta comparison
Contratos:
ITM
ATM
OTM
Último Deep Research conocido
SPY
Régimen: RISK_ON
Score: 0.5398459019217334
Net GEX: 760,883,603
Net DEX: -73,012,561,279
Call Wall: 785
Put Wall: 525
QQQ
Régimen: RISK_ON_FUERTE
Score: 0.6775196409231291
Net GEX: -4,541,960,257
Net DEX: -63,033,999,834
Call Wall: 760
Put Wall: 730
IWM
Régimen: NEUTRAL
Score: -0.1587458719225783
Net GEX: 4,347,922,239
Net DEX: -23,586,007,448
Call Wall: 285
Put Wall: 275
XLK
Régimen: RISK_ON_FUERTE
Score: 0.795408868657833
Net GEX: -35,037,524
Net DEX: -3,857,081,900
Call Wall: 150
Put Wall: 135
SMH
Régimen: RISK_ON
Score: 0.4865568509743947
Net GEX: -375,858,918
Net DEX: -7,207,038,909
Call Wall: 700
Put Wall: 455
Estos datos son snapshots históricos y no deben tratarse como datos actuales.
Portfolio
Métodos conocidos:
Equal Weight
Inverse Volatility
Minimum Variance
Signal Tilted
Maximum Sharpe
Risk Engine
Métricas:
Volatilidad anual
Downside Volatility
VaR
CVaR
Maximum Drawdown
Beta
HHI
Número efectivo de activos
Contribución al riesgo
Stress tests:
Liquidity Crisis
Tech Crash
Risk-Off
Rates Up
Inflation Shock
Dashboard
Existe Dashboard V1 y V2.
Problema actual:
el backend es más avanzado que la interfaz
Watchlist actual propuesta para opciones
SPY
QQQ
IWM
XLK
SMH
NVDA
AAPL
MSFT
META
AMZN
TLT
GLD
HYG
SPX
VIX
Núcleo actual de Deep Research:
SPY
QQQ
IWM
XLK
SMH
Caso práctico de opciones
Se estudió un paper trade de:
QQQ 30-OCT-2026 722C
Snapshot conocido:
Delta ≈ 0.692946
Gamma ≈ 0.006618
Theta/día ≈ -0.311769
Vega ≈ 0.796807
IV ≈ 0.233177
Mid ≈ 34.105
Breakeven ≈ 756.105
No tratar este snapshot como cotización actual.
Fortalezas
1. Arquitectura modular.
2. Multi-activo.
3. Deep Research.
4. Options Analytics.
5. Greeks.
6. Dealer Engine.
7. Scenario Engine.
8. Visualización 3D.
9. Portfolio.
10. Risk.
Limitaciones
1. Dependencia de yfinance.
2. Dealer positioning basado en proxies.
3. Options Flow aproximado.
4. Black-Scholes europeo en parte del análisis.
5. Walls agregados por múltiples expiraciones.
6. Forecasts necesitan validación constante.
7. Dashboard todavía incompleto.
8. Falta mejor síntesis de resultados.
Estado conceptual
Quant Platform
├── Data
├── Assets
├── Market
├── Forecast
├── Options
│   ├── Greeks
│   ├── Dealer
│   ├── Flow
│   └── Scenarios
├── Portfolio
├── Risk
├── Deep Research
├── API
└── Dashboard
El objetivo actual es mejorar utilidad y robustez, no añadir módulos sin necesidad.