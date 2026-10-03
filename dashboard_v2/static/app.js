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

function avisoMotor(nombre, motor) {
    if (["OK", "NO_COMPATIBLE"].includes(motor.estado)) {
        return "";
    }

    const etiquetas = {
        opciones: "Opciones",
        forecast: "Forecast",
        market_regime: "Mercado",
    };
    const etiqueta = etiquetas[nombre] || nombre;
    const parcial = motor.estado === "PARCIAL";
    const datos = motor.datos || {};
    const calidad = (datos.resumen_cadena || {}).calidad;
    let titulo = `${etiqueta}: ${parcial ? "análisis parcial" : "análisis no disponible"}`;
    let mensaje = motor.error || "No se ha podido completar este análisis.";
    let detalles = "";

    if (parcial && nombre === "opciones" && calidad) {
        titulo = "Opciones filtradas por calidad";
        mensaje = `${calidad.contratos_validos} de ${calidad.contratos_entrada} contratos utilizados; ${calidad.contratos_rechazados} excluidos por calidad.`;
        const motivos = {
            dato_no_finito: "Datos numéricos ausentes o inválidos",
            strike_invalido: "Strike inválido",
            cotizacion_invalida: "Cotización inválida",
            mercado_cruzado: "Bid superior al ask",
            spread_excesivo: "Spread demasiado amplio",
            iv_invalida: "Volatilidad implícita inválida",
            dte_no_positivo: "Sin tiempo positivo hasta el vencimiento",
            oi_negativo: "Open Interest negativo",
            tipo_invalido: "Tipo de opción inválido",
            vencimiento_invalido: "Vencimiento inválido",
            duplicado: "Contrato duplicado",
        };
        const filas = Object.entries(calidad.motivos || {})
            .filter(([, cantidad]) => Number(cantidad) > 0)
            .map(([motivo, cantidad]) => `<li>${escapar(motivos[motivo] || motivo.replaceAll("_", " "))}: ${escapar(cantidad)}</li>`);
        detalles = `<details><summary>Ver motivos de exclusión</summary>
            <ul>${filas.join("")}</ul>
            <p>Un contrato puede tener varios motivos de exclusión.</p>
            ${calidad.actualidad_cotizacion === "NO_VERIFICADA" ? "<p>La antigüedad de las cotizaciones no está verificada.</p>" : ""}
            </details>`;
    } else if (parcial) {
        mensaje = motor.error || "Se muestran los resultados disponibles; parte del análisis no pudo completarse.";
        const errores = Object.entries(datos.errores_modelos || {});
        if (errores.length) {
            detalles = `<details><summary>Ver modelos no disponibles</summary><ul>
                ${errores.map(([modelo, error]) => `<li>${escapar(modelo)}: ${escapar(error)}</li>`).join("")}
                </ul></details>`;
        }
    }

    return `<div class="aviso-motor ${parcial ? "aviso-calidad" : "aviso-error"}" role="${parcial ? "status" : "alert"}">
        <strong>${escapar(titulo)}</strong><p>${escapar(mensaje)}</p>${detalles}
        </div>`;
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
            .map(([nombre, motor]) => avisoMotor(nombre, motor))
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

function vistaMovimientoEsperado(informe) {
    const filas = informe.expected_move_por_vencimiento || [];
    if (!filas.length) {
        return `<h3>Expected Move por vencimiento</h3><p>${escapar(informe.error_expected_move || "Este informe no contiene estimaciones. Genera un nuevo Deep Research para este activo.")}</p>`;
    }
    const primeroValido = filas.findIndex(f => f.estado === "OK");
    return `<h3>Expected Move por vencimiento</h3>
        <p>Estimaciones centradas en el spot del snapshot. No son límites garantizados ni probabilidades calibradas.</p>
        ${informe.procedencia_expected_move ? "<p>Recalculado con la cadena histórica guardada; las cotizaciones originales no se han actualizado.</p>" : ""}
        ${filas.map((f, i) => {
            const valido = f.estado === "OK";
            const encabezado = `${f.vencimiento}${f.dte == null ? "" : ` · ${numero(f.dte, 1)} días`}`;
            const contenido = valido ? `<p>Spot: $${numero(f.spot, 2)} · Strike ATM: $${numero(f.strike_atm, 2)} · IV media: ${porcentaje(f.iv_atm)}</p>
                <table><thead><tr><th>Método</th><th>Movimiento ±</th><th>Intervalo estimado</th></tr></thead><tbody>
                <tr><td>Straddle ATM</td><td>$${numero(f.move_straddle_dolares, 2)} (${porcentaje(f.move_straddle_pct)})</td><td>$${numero(f.limite_inferior_straddle, 2)} – $${numero(f.limite_superior_straddle, 2)}</td></tr>
                <tr><td>IV ATM</td><td>$${numero(f.move_iv_dolares, 2)} (${porcentaje(f.move_iv_pct)})</td><td>$${numero(f.limite_inferior_iv, 2)} – $${numero(f.limite_superior_iv, 2)}</td></tr>
                </tbody></table>
                <p class="detalle-movimiento">Call mid: $${numero(f.call_mid, 2)} · Put mid: $${numero(f.put_mid, 2)}<br>
                Spread call: ${porcentaje(f.call_spread_pct)} · Spread put: ${porcentaje(f.put_spread_pct)}<br>
                ${escapar(f.contratos_validos)} de ${escapar(f.contratos_entrada)} contratos válidos. Antigüedad de cotizaciones no verificada.</p>`
                : `<p>${escapar(f.motivo || "No hay una pareja ATM válida para este vencimiento.")}</p>`;
            return `<details class="movimiento-expiry" ${i === primeroValido ? "open" : ""}>
                <summary>${escapar(encabezado)} — ${valido ? `IV ±${porcentaje(f.move_iv_pct)}` : "Sin estimación"}</summary>
                ${contenido}</details>`;
        }).join("")}
        <p class="detalle-movimiento">Straddle = mid call + mid put. IV = spot × IV media × √(DTE/365). Los intervalos straddle no son sus breakevens.</p>`;
}

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
            </tbody></table>${vistaMovimientoEsperado(informe)}
            <details class="movimiento-expiry"><summary>Estado de los módulos del informe</summary><ul>
            ${Object.entries(informe.estados || {}).map(([nombre, etapa]) => `<li>${escapar(nombre)}: ${escapar(etapa.estado)}${etapa.error ? ` — ${escapar(etapa.error)}` : ""}</li>`).join("")}
            </ul></details>`;
    } catch (error) {
        contenedor.textContent = String(error);
    }
}
