import perspective from
    "https://cdn.jsdelivr.net/npm/@perspective-dev/client@5.5.0/dist/cdn/perspective.js";

import
    "https://cdn.jsdelivr.net/npm/@perspective-dev/viewer@5.5.0/dist/cdn/perspective-viewer.js";

import
    "https://cdn.jsdelivr.net/npm/@perspective-dev/viewer-datagrid@5.5.0/dist/cdn/perspective-viewer-datagrid.js";


const worker = await perspective.worker();


const tablas = new Map();


const titulos = {
    overview: "Overview",
    market: "Market",
    portfolio: "Portfolio",
    options: "Options",
    risk: "Risk",
    system: "System",
};


function numero(
    valor,
    decimales = 2,
) {
    if (
        valor === null
        || valor === undefined
        || Number.isNaN(
            Number(valor)
        )
    ) {
        return "—";
    }

    return Number(
        valor
    ).toLocaleString(
        "es-ES",
        {
            minimumFractionDigits:
                decimales,
            maximumFractionDigits:
                decimales,
        },
    );
}


function porcentaje(
    valor,
    decimales = 2,
) {
    if (
        valor === null
        || valor === undefined
    ) {
        return "—";
    }

    return (
        numero(
            Number(valor) * 100,
            decimales,
        )
        + "%"
    );
}


function dinero(
    valor,
) {
    if (
        valor === null
        || valor === undefined
    ) {
        return "—";
    }

    const absoluto = Math.abs(
        Number(valor)
    );

    let divisor = 1;
    let sufijo = "";

    if (
        absoluto >= 1_000_000_000
    ) {
        divisor = 1_000_000_000;
        sufijo = "B";

    } else if (
        absoluto >= 1_000_000
    ) {
        divisor = 1_000_000;
        sufijo = "M";

    } else if (
        absoluto >= 1_000
    ) {
        divisor = 1_000;
        sufijo = "K";
    }

    return (
        "$"
        + numero(
            Number(valor)
            / divisor,
            2,
        )
        + sufijo
    );
}


async function obtenerJSON(
    ruta,
) {
    const respuesta = await fetch(
        ruta,
        {
            cache: "no-store",
        },
    );

    if (
        !respuesta.ok
    ) {
        throw new Error(
            `Error HTTP ${respuesta.status}`
        );
    }

    return await respuesta.json();
}


function aplicarClaseValor(
    elemento,
    valor,
) {
    elemento.classList.remove(
        "positivo",
        "negativo",
        "neutral",
    );

    if (
        valor > 0
    ) {
        elemento.classList.add(
            "positivo"
        );

    } else if (
        valor < 0
    ) {
        elemento.classList.add(
            "negativo"
        );

    } else {
        elemento.classList.add(
            "neutral"
        );
    }
}


function renderizarPesos(
    pesos,
) {
    const contenedor =
        document.getElementById(
            "lista-pesos"
        );

    contenedor.innerHTML = "";

    if (
        !pesos
        || pesos.length === 0
    ) {
        contenedor.innerHTML =
            "<div class='kpi-secundario'>Sin datos</div>";

        return;
    }

    for (
        const fila
        of pesos
    ) {
        const peso =
            Number(
                fila.peso
            );

        const linea =
            document.createElement(
                "div"
            );

        linea.className =
            "peso-linea";

        linea.innerHTML = `
            <div class="peso-ticker">
                ${fila.ticker}
            </div>

            <div class="peso-barra-fondo">
                <div
                    class="peso-barra"
                    style="width:${Math.max(
                        0,
                        Math.min(
                            100,
                            peso * 100
                        )
                    )}%"
                ></div>
            </div>

            <div class="peso-valor">
                ${porcentaje(peso)}
            </div>
        `;

        contenedor.appendChild(
            linea
        );
    }
}


async function cargarResumen() {
    const datos =
        await obtenerJSON(
            "/api/resumen"
        );

    const regimen =
        datos.regimen || {};

    const riesgo =
        datos.riesgo || {};

    const flow =
        datos.flow || {};

    const dealer =
        datos.dealer || {};

    document.getElementById(
        "kpi-regimen"
    ).textContent =
        regimen.estado || "—";

    document.getElementById(
        "kpi-regimen-score"
    ).textContent =
        (
            "Score: "
            + numero(
                regimen.score,
                3,
            )
        );


    const flowElemento =
        document.getElementById(
            "kpi-flow"
        );

    flowElemento.textContent =
        flow.estado || "—";

    aplicarClaseValor(
        flowElemento,
        Number(
            flow.balance || 0
        )
    );

    document.getElementById(
        "kpi-flow-balance"
    ).textContent =
        (
            "Balance: "
            + numero(
                flow.balance,
                3,
            )
        );


    document.getElementById(
        "kpi-gamma-flip"
    ).textContent =
        numero(
            dealer.gamma_flip,
            2,
        );

    document.getElementById(
        "kpi-spot"
    ).textContent =
        (
            "Spot: "
            + numero(
                dealer.spot,
                2,
            )
        );


    document.getElementById(
        "kpi-vol"
    ).textContent =
        porcentaje(
            riesgo.volatilidad
        );

    document.getElementById(
        "kpi-beta"
    ).textContent =
        (
            "Beta SPY: "
            + numero(
                riesgo.beta_spy,
                2,
            )
        );


    document.getElementById(
        "kpi-var"
    ).textContent =
        porcentaje(
            riesgo.var_95
        );

    document.getElementById(
        "kpi-cvar"
    ).textContent =
        (
            "CVaR: "
            + porcentaje(
                riesgo.cvar_95
            )
        );


    document.getElementById(
        "kpi-drawdown"
    ).textContent =
        porcentaje(
            riesgo.max_drawdown
        );

    document.getElementById(
        "kpi-neff"
    ).textContent =
        (
            "N efectivo: "
            + numero(
                riesgo.numero_efectivo_activos,
                2,
            )
        );


    document.getElementById(
        "overview-gex"
    ).textContent =
        dinero(
            dealer.gex
        );

    document.getElementById(
        "overview-dex"
    ).textContent =
        dinero(
            dealer.dex
        );

    document.getElementById(
        "overview-gamma-pos"
    ).textContent =
        numero(
            dealer.gamma_node_positivo,
            2,
        );

    document.getElementById(
        "overview-gamma-neg"
    ).textContent =
        numero(
            dealer.gamma_node_negativo,
            2,
        );

    document.getElementById(
        "overview-flow-gamma"
    ).textContent =
        numero(
            dealer.flow_gamma_node,
            2,
        );


    renderizarPesos(
        datos.portfolio?.pesos
        || []
    );
}


async function cargarEstado() {
    const estado =
        await obtenerJSON(
            "/api/estado"
        );

    const texto =
        document.getElementById(
            "estado-sistema"
        );

    const punto =
        document.getElementById(
            "estado-punto"
        );

    texto.textContent =
        estado.estado;

    punto.classList.remove(
        "operativo",
        "error",
    );

    if (
        estado.estado
        === "OPERATIVO"
    ) {
        punto.classList.add(
            "operativo"
        );

    } else if (
        estado.estado
        === "INCOMPLETO"
    ) {
        punto.classList.add(
            "error"
        );
    }


    document.getElementById(
        "ultima-actualizacion"
    ).textContent =
        estado.ultima_actualizacion
        || "Sin actualización";


    const contenedor =
        document.getElementById(
            "estado-datasets"
        );

    contenedor.innerHTML = "";

    for (
        const [
            nombre,
            disponible,
        ]
        of Object.entries(
            estado.datasets
        )
    ) {
        const linea =
            document.createElement(
                "div"
            );

        linea.className =
            "dataset-linea";

        linea.innerHTML = `
            <div>${nombre}</div>

            <div
                class="${
                    disponible
                    ? "dataset-ok"
                    : "dataset-error"
                }"
            >
                ${
                    disponible
                    ? "DISPONIBLE"
                    : "NO DISPONIBLE"
                }
            </div>

            <div>
                ${
                    disponible
                    ? "OK"
                    : "Archivo no encontrado"
                }
            </div>
        `;

        contenedor.appendChild(
            linea
        );
    }
}


async function cargarPerspective(
    viewerId,
    dataset,
) {
    const viewer =
        document.getElementById(
            viewerId
        );

    let datos =
        await obtenerJSON(
            `/api/datos/${dataset}`
        );

    /*
    Evitamos que Perspective conserve visualmente
    el dataset anterior cuando el nuevo está vacío.
    */
    if (
        !Array.isArray(datos)
        || datos.length === 0
    ) {
        datos = [
            {
                estado:
                    `Dataset '${dataset}' sin datos disponibles`,
            },
        ];
    }

    const tablaAnterior =
        tablas.get(
            viewerId
        );

    const tablaNueva =
        await worker.table(
            datos
        );

    await viewer.load(
        tablaNueva
    );

    await viewer.restore(
        {
            plugin: "Datagrid",
        }
    );

    tablas.set(
        viewerId,
        tablaNueva
    );

    /*
    Eliminamos la tabla anterior solamente después
    de que Perspective haya cargado la nueva.
    */
    if (
        tablaAnterior
        && tablaAnterior !== tablaNueva
    ) {
        try {
            await tablaAnterior.delete();
        } catch {
            /*
            No bloqueamos el dashboard si Perspective
            mantiene todavía alguna referencia interna.
            */
        }
    }
}


function configurarNavegacion() {

    const botones =
        document.querySelectorAll(
            ".menu-item"
        );

    for (
        const boton
        of botones
    ) {

        boton.addEventListener(
            "click",
            async () => {

                for (
                    const otro
                    of botones
                ) {
                    otro.classList.remove(
                        "activo"
                    );
                }

                boton.classList.add(
                    "activo"
                );


                const panel =
                    boton.dataset.panel;

                for (
                    const elemento
                    of document.querySelectorAll(
                        ".panel"
                    )
                ) {
                    elemento.classList.remove(
                        "activo"
                    );
                }

                document.getElementById(
                    `panel-${panel}`
                ).classList.add(
                    "activo"
                );

                document.getElementById(
                    "titulo-panel"
                ).textContent =
                    titulos[
                        panel
                    ];


                if (
                    panel === "market"
                ) {
                    await cargarPerspective(
                        "viewer-market",
                        "market_regime_v2",
                    );

                } else if (
                    panel === "portfolio"
                ) {
                    await cargarPerspective(
                        "viewer-portfolio",
                        "portfolio_v2_pesos",
                    );

                } else if (
                    panel === "options"
                ) {
                    await cargarPerspective(
                        "viewer-options",
                        "options_flow_v2",
                    );

                } else if (
                    panel === "risk"
                ) {
                    await cargarPerspective(
                        "viewer-risk",
                        "risk_contribucion",
                    );
                }
            }
        );
    }
}


function configurarSubnavegacion() {

    const botones =
        document.querySelectorAll(
            ".subnav"
        );

    for (
        const boton
        of botones
    ) {

        boton.addEventListener(
            "click",
            async () => {

                const padre =
                    boton.parentElement;

                for (
                    const otro
                    of padre.querySelectorAll(
                        ".subnav"
                    )
                ) {
                    otro.classList.remove(
                        "activo"
                    );
                }

                boton.classList.add(
                    "activo"
                );


                const dataset =
                    boton.dataset.dataset;

                const panel =
                    boton.closest(
                        ".panel"
                    );

                const viewer =
                    panel.querySelector(
                        "perspective-viewer"
                    );

                await cargarPerspective(
                    viewer.id,
                    dataset,
                );
            }
        );
    }
}


async function recargarTodo() {

    const boton =
        document.getElementById(
            "boton-recargar"
        );

    boton.disabled = true;

    boton.textContent =
        "Actualizando...";

    try {

        await Promise.all(
            [
                cargarResumen(),
                cargarEstado(),
            ]
        );

    } catch (
        error
    ) {

        console.error(
            error
        );

    } finally {

        boton.disabled = false;

        boton.textContent =
            "Actualizar";
    }
}


document.getElementById(
    "boton-recargar"
).addEventListener(
    "click",
    recargarTodo,
);


configurarNavegacion();

configurarSubnavegacion();


await recargarTodo();