const $ = (id) => document.getElementById(id);

function porcentaje(valor) {
    if (
        valor === null ||
        valor === undefined ||
        Number.isNaN(Number(valor))
    ) {
        return "-";
    }

    return `${(Number(valor) * 100).toFixed(2)}%`;
}

function numero(valor, decimales = 3) {
    if (
        valor === null ||
        valor === undefined ||
        Number.isNaN(Number(valor))
    ) {
        return "-";
    }

    return Number(valor).toFixed(decimales);
}

function tarjeta(nombre, valor) {
    return `
        <div class="tarjeta">
            <small>${nombre}</small>
            <strong>${valor}</strong>
        </div>
    `;
}

async function obtenerJson(url) {
    const respuesta = await fetch(url);

    const datos = await respuesta.json();

    if (!respuesta.ok) {
        throw new Error(
            datos.error || "Error desconocido"
        );
    }

    return datos;
}

async function cargarHealth() {
    try {
        const datos = await obtenerJson(
            "/api/v2/health"
        );

        $("estadoSistema").textContent =
            datos.operativo
                ? "● SISTEMA OPERATIVO"
                : "● SISTEMA CON ERRORES";

        $("resultadoSistema").innerHTML = `
            <div class="grid">
                ${tarjeta(
                    "Operativo",
                    datos.operativo ? "SÍ" : "NO"
                )}
                ${tarjeta(
                    "Modelos",
                    datos.modelos.join(", ")
                )}
                ${tarjeta(
                    "Universos",
                    datos.universos.length
                )}
                ${tarjeta(
                    "Cache hits",
                    datos.cache.hits
                )}
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Componente</th>
                        <th>Estado</th>
                        <th>Detalle</th>
                    </tr>
                </thead>
                <tbody>
                    ${datos.checks.map(
                        (item) => `
                            <tr>
                                <td>${item.componente}</td>
                                <td>${item.estado}</td>
                                <td>${item.detalle}</td>
                            </tr>
                        `
                    ).join("")}
                </tbody>
            </table>
        `;
    } catch (error) {
        $("estadoSistema").textContent =
            "ERROR";

        $("resultadoSistema").innerHTML =
            `<p class="error">${error}</p>`;
    }
}

async function analizarActivo() {
    const simbolo = $("simbolo")
        .value
        .trim()
        .toUpperCase();

    const horizonte = $("horizonte").value;

    $("resultadoActivo").innerHTML =
        "Analizando...";

    try {
        const datos = await obtenerJson(
            `/api/v2/activo/${encodeURIComponent(
                simbolo
            )}?horizonte=${horizonte}`
        );

        const mercado =
            datos.motores.market_regime;

        const forecast =
            datos.motores.forecast;

        const opciones =
            datos.motores.opciones;

        const m = mercado.datos || {};

        let html = `
            <div class="grid">
                ${tarjeta(
                    "Activo",
                    datos.simbolo
                )}
                ${tarjeta(
                    "Clase",
                    datos.clase
                )}
                ${tarjeta(
                    "Precio",
                    numero(m.precio, 4)
                )}
                ${tarjeta(
                    "Régimen",
                    m.regimen_global || "-"
                )}
                ${tarjeta(
                    "Score régimen",
                    numero(
                        m.score_regimen
                    )
                )}
                ${tarjeta(
                    "Retorno 20D",
                    porcentaje(
                        m.retorno_20d
                    )
                )}
                ${tarjeta(
                    "Volatilidad 20D",
                    porcentaje(
                        m.vol20
                    )
                )}
                ${tarjeta(
                    "Drawdown",
                    porcentaje(
                        m.drawdown_actual
                    )
                )}
            </div>
        `;

        if (
            forecast &&
            forecast.estado === "OK"
        ) {
            const e =
                forecast.datos.ensemble;

            html += `
                <h3>Forecast</h3>

                <div class="grid">
                    ${tarjeta(
                        "Retorno estimado",
                        porcentaje(
                            e.retorno_estimado
                        )
                    )}
                    ${tarjeta(
                        "Precio estimado",
                        numero(
                            e.precio_estimado,
                            4
                        )
                    )}
                    ${tarjeta(
                        "Dispersión modelos",
                        porcentaje(
                            e.dispersion_modelos
                        )
                    )}
                </div>
            `;
        }

        if (
            opciones &&
            opciones.estado === "OK"
        ) {
            const d =
                opciones.datos.dealer;

            html += `
                <h3>Opciones / Dealer</h3>

                <div class="grid">
                    ${tarjeta(
                        "Contratos",
                        opciones.datos.contratos
                    )}
                    ${tarjeta(
                        "Net GEX 1%",
                        numero(
                            d.net_gex_1pct,
                            0
                        )
                    )}
                    ${tarjeta(
                        "Call Wall",
                        d.call_wall
                    )}
                    ${tarjeta(
                        "Put Wall",
                        d.put_wall
                    )}
                    ${tarjeta(
                        "Gamma Node +",
                        d.gamma_node_positivo
                    )}
                    ${tarjeta(
                        "Gamma Node -",
                        d.gamma_node_negativo
                    )}
                </div>
            `;
        }

        $("resultadoActivo").innerHTML =
            html;

    } catch (error) {
        $("resultadoActivo").innerHTML =
            `<p class="error">${error}</p>`;
    }
}

function tablaRanking(datos) {
    return `
        <table>
            <thead>
                <tr>
                    <th>Activo</th>
                    <th>Ranking</th>
                    <th>Régimen</th>
                    <th>Score</th>
                    <th>20D</th>
                    <th>60D</th>
                </tr>
            </thead>

            <tbody>
                ${datos.map(
                    (fila) => `
                        <tr>
                            <td>${fila.simbolo}</td>
                            <td>${fila.ranking}</td>
                            <td>${fila.regimen_global}</td>
                            <td>${numero(
                                fila.score_relativo
                            )}</td>
                            <td>${porcentaje(
                                fila.retorno_20d
                            )}</td>
                            <td>${porcentaje(
                                fila.retorno_60d
                            )}</td>
                        </tr>
                    `
                ).join("")}
            </tbody>
        </table>
    `;
}

async function analizarUniverso() {
    const nombre = $("universo").value;

    $("resultadoUniverso").innerHTML =
        "Analizando universo...";

    try {
        const datos = await obtenerJson(
            `/api/v2/universo/${nombre}`
        );

        $("resultadoUniverso").innerHTML =
            `
                <div class="grid">
                    ${tarjeta(
                        "Universo",
                        datos.nombre
                    )}
                    ${tarjeta(
                        "Activos",
                        datos.simbolos.length
                    )}
                    ${tarjeta(
                        "Volatilidad",
                        porcentaje(
                            datos.riesgo
                                .volatilidad_anual
                        )
                    )}
                    ${tarjeta(
                        "CVaR 95%",
                        porcentaje(
                            datos.riesgo.cvar_95
                        )
                    )}
                    ${tarjeta(
                        "Max Drawdown",
                        porcentaje(
                            datos.riesgo
                                .max_drawdown
                        )
                    )}
                </div>
                ${tablaRanking(
                    datos.ranking
                )}
            `;
    } catch (error) {
        $("resultadoUniverso").innerHTML =
            `<p class="error">${error}</p>`;
    }
}

async function cargarWatchlists() {
    const datos = await obtenerJson(
        "/api/v2/watchlists"
    );

    $("listaWatchlists").innerHTML =
        Object.keys(datos)
            .map(
                (nombre) => `
                    <button
                        class="principal"
                        onclick="
                            analizarWatchlist(
                                '${nombre}'
                            )
                        "
                    >
                        ${nombre}
                    </button>
                `
            )
            .join("");
}

async function analizarWatchlist(nombre) {
    $("resultadoWatchlist").innerHTML =
        "Analizando watchlist...";

    try {
        const datos = await obtenerJson(
            `/api/v2/watchlist/${nombre}`
        );

        $("resultadoWatchlist").innerHTML =
            `
                <div class="grid">
                    ${tarjeta(
                        "Watchlist",
                        datos.nombre
                    )}
                    ${tarjeta(
                        "Activos",
                        datos.simbolos.length
                    )}
                    ${tarjeta(
                        "Volatilidad",
                        porcentaje(
                            datos.riesgo
                                .volatilidad_anual
                        )
                    )}
                    ${tarjeta(
                        "CVaR 95%",
                        porcentaje(
                            datos.riesgo.cvar_95
                        )
                    )}
                </div>
                ${tablaRanking(
                    datos.ranking
                )}
            `;
    } catch (error) {
        $("resultadoWatchlist").innerHTML =
            `<p class="error">${error}</p>`;
    }
}

document
    .querySelectorAll(".nav")
    .forEach(
        (boton) => {
            boton.addEventListener(
                "click",
                () => {
                    document
                        .querySelectorAll(".nav")
                        .forEach(
                            (item) =>
                                item.classList.remove(
                                    "activo"
                                )
                        );

                    boton.classList.add(
                        "activo"
                    );

                    document
                        .querySelectorAll(".vista")
                        .forEach(
                            (vista) =>
                                vista.classList.add(
                                    "oculto"
                                )
                        );

                    $(
                        `vista-${boton.dataset.vista}`
                    ).classList.remove(
                        "oculto"
                    );
                }
            );
        }
    );

$("analizarActivo").addEventListener(
    "click",
    analizarActivo
);

$("analizarUniverso").addEventListener(
    "click",
    analizarUniverso
);

cargarHealth();
cargarWatchlists();
analizarActivo();