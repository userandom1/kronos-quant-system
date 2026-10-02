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

function escapar(valor) {
    const nodo = document.createElement("span");
    nodo.textContent = valor == null ? "-" : String(valor);
    return nodo.innerHTML;
}

function tarjeta(nombre, valor) {
    return `
        <div class="tarjeta">
            <small>${escapar(nombre)}</small>
            <strong>${escapar(valor)}</strong>
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
                                <td>${escapar(item.componente)}</td>
                                <td>${escapar(item.estado)}</td>
                                <td>${escapar(item.detalle)}</td>
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
            `<p class="error">${escapar(error)}</p>`;
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

        const incidencias = Object.entries(datos.motores)
            .filter(([, motor]) => !["OK", "NO_COMPATIBLE"].includes(motor.estado))
            .map(([nombre, motor]) => `<p class="error">${escapar(nombre)}: ${escapar(motor.estado)} — ${escapar(motor.error || JSON.stringify((motor.datos || {}).errores_modelos || (motor.datos || {}).resumen_cadena || {}))}</p>`)
            .join("");
        let html = incidencias + `
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
            ["OK", "PARCIAL"].includes(forecast.estado)
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
            ["OK", "PARCIAL"].includes(opciones.estado)
        ) {
            const d =
                opciones.datos.dealer;

            html += `
                <h3>Opciones / Dealer (estimación proxy)</h3>
                <p>Walls por OI agregado. Convención: calls short, puts long. No son posiciones observadas.</p>

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
            html + '<button id="verInforme">Ver último Deep Research guardado</button><div id="informeGuardado"></div>';
        $("verInforme").addEventListener("click", () => cargarInforme(simbolo));

    } catch (error) {
        $("resultadoActivo").innerHTML =
            `<p class="error">${escapar(error)}</p>`;
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
                            <td>${escapar(fila.simbolo)}</td>
                            <td>${escapar(fila.ranking)}</td>
                            <td>${escapar(fila.regimen_global)}</td>
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
            `<p class="error">${escapar(error)}</p>`;
    }
}

async function cargarWatchlists() {
    const datos = await obtenerJson(
        "/api/v2/watchlists"
    );

    const lista = $("listaWatchlists");
    lista.replaceChildren();
    Object.keys(datos).forEach(nombre => {
        const boton = document.createElement("button");
        boton.className = "principal";
        boton.textContent = nombre;
        boton.addEventListener("click", () => analizarWatchlist(nombre));
        lista.appendChild(boton);
    });
}

async function analizarWatchlist(nombre) {
    $("resultadoWatchlist").innerHTML =
        "Analizando watchlist...";

    try {
        const datos = await obtenerJson(
            `/api/v2/watchlist/${encodeURIComponent(nombre)}`
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
            `<p class="error">${escapar(error)}</p>`;
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
cargarWatchlists().catch(error => { $("listaWatchlists").textContent = String(error); });
analizarActivo();

async function cargarInforme(simbolo) {
    const contenedor = $("informeGuardado");
    contenedor.textContent = "Leyendo investigación guardada...";
    try {
        const informe = await obtenerJson(`/api/v2/informe/${encodeURIComponent(simbolo)}`);
        const filas = informe.dealer_por_vencimiento || [];
        contenedor.innerHTML = `<h3>Deep Research ${escapar(informe.ticker)} — ${escapar(informe.estado)}</h3>
            <p>Snapshot: ${escapar((informe.procedencia || {}).inicio_utc || "No registrada")}. Datos históricos del informe.</p>
            <table><thead><tr><th>Vencimiento</th><th>GEX 1%</th><th>DEX</th><th>Call Wall</th><th>Put Wall</th><th>Gamma Flip</th></tr></thead><tbody>
            ${filas.map(f => `<tr><td>${escapar(f.vencimiento)}</td><td>${numero(f.net_gex_1pct, 0)}</td><td>${numero(f.net_dex, 0)}</td><td>${escapar(f.call_wall)}</td><td>${escapar(f.put_wall)}</td><td>${escapar(f.estado_gamma_flip)}: ${escapar((f.gamma_flips || []).join(", "))}</td></tr>`).join("")}
            </tbody></table>`;
        const detalle = document.createElement("pre");
        detalle.textContent = JSON.stringify(informe.estados, null, 2);
        contenedor.appendChild(detalle);
    } catch (error) {
        contenedor.textContent = String(error);
    }
}
