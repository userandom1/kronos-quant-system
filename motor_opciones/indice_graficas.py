from __future__ import annotations

import html
from pathlib import Path


def _titulo_desde_nombre(
    nombre: str,
) -> str:
    """Convierte nombre interno en título legible."""

    return (
        nombre
        .replace(
            "_",
            " ",
        )
        .title()
        .replace(
            "Gex",
            "GEX",
        )
        .replace(
            "Dex",
            "DEX",
        )
        .replace(
            "Iv",
            "IV",
        )
        .replace(
            "Pnl",
            "P&L",
        )
    )


def _categoria(
    nombre: str,
) -> str:
    """Clasifica una gráfica."""

    nombre_lower = (
        nombre.lower()
    )

    if (
        "escenario" in nombre_lower
        or "pnl_" in nombre_lower
        or "theta_decay" in nombre_lower
        or "delta_comparacion"
        in nombre_lower
    ):
        return "ESCENARIOS"

    if (
        "gex" in nombre_lower
        or "dex" in nombre_lower
        or "exposure" in nombre_lower
        or "open_interest"
        in nombre_lower
    ):
        return "DEALER / POSICIONAMIENTO"

    if "surface" in nombre_lower:
        return "SUPERFICIES 3D"

    return "GREEKS 2D"


def generar_indice_graficas(
    ticker: str,
    graficas: dict[str, str],
    ruta_salida: Path,
) -> Path:
    """Genera un índice HTML visual de todas las gráficas."""

    ruta_salida.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    categorias = {
        "GREEKS 2D": [],
        "SUPERFICIES 3D": [],
        "DEALER / POSICIONAMIENTO": [],
        "ESCENARIOS": [],
    }

    for nombre, ruta in graficas.items():
        categorias[
            _categoria(
                nombre
            )
        ].append(
            (
                nombre,
                Path(
                    ruta
                ),
            )
        )

    bloques = []

    for categoria, elementos in categorias.items():
        if not elementos:
            continue

        tarjetas = []

        for nombre, ruta in elementos:
            ruta_relativa = (
                ruta.relative_to(
                    ruta_salida.parent
                )
                if ruta.is_relative_to(
                    ruta_salida.parent
                )
                else ruta
            )

            ruta_html = html.escape(
                str(
                    ruta_relativa
                ).replace(
                    "\\",
                    "/",
                )
            )

            titulo = html.escape(
                _titulo_desde_nombre(
                    nombre
                )
            )

            if ruta.suffix.lower() == ".png":
                contenido = f"""
                    <a
                        href="{ruta_html}"
                        target="_blank"
                    >
                        <img
                            src="{ruta_html}"
                            alt="{titulo}"
                            loading="lazy"
                        >
                    </a>
                """

            else:
                contenido = f"""
                    <iframe
                        src="{ruta_html}"
                        loading="lazy"
                    ></iframe>

                    <a
                        class="abrir"
                        href="{ruta_html}"
                        target="_blank"
                    >
                        Abrir gráfica 3D
                    </a>
                """

            tarjetas.append(
                f"""
                <article class="tarjeta">
                    <h3>{titulo}</h3>
                    {contenido}
                </article>
                """
            )

        bloques.append(
            f"""
            <section>
                <h2>{categoria}</h2>

                <div class="grid">
                    {''.join(tarjetas)}
                </div>
            </section>
            """
        )

    documento = f"""
<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>
        {html.escape(ticker)} — Índice de gráficas
    </title>

    <style>
        :root {{
            color-scheme: dark;
            font-family:
                Inter,
                Segoe UI,
                Arial,
                sans-serif;

            --fondo: #090b10;
            --panel: #11151d;
            --borde: #252b37;
            --texto: #f0f3f8;
            --muted: #8c96a8;
            --acento: #67a9ff;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            padding: 32px;
            background: var(--fondo);
            color: var(--texto);
        }}

        header {{
            max-width: 1600px;
            margin: 0 auto 40px auto;
        }}

        .tag {{
            color: var(--acento);
            font-size: 12px;
            letter-spacing: 2px;
        }}

        h1 {{
            margin: 8px 0;
            font-size: 34px;
        }}

        header p {{
            color: var(--muted);
        }}

        section {{
            max-width: 1600px;
            margin: 0 auto 50px auto;
        }}

        h2 {{
            margin-bottom: 18px;
            border-bottom:
                1px solid var(--borde);
            padding-bottom: 10px;
        }}

        .grid {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(
                        480px,
                        1fr
                    )
                );
            gap: 18px;
        }}

        .tarjeta {{
            background: var(--panel);
            border:
                1px solid var(--borde);
            border-radius: 12px;
            padding: 16px;
            overflow: hidden;
        }}

        h3 {{
            margin-top: 0;
            font-size: 16px;
        }}

        img {{
            width: 100%;
            height: auto;
            display: block;
            border-radius: 7px;
        }}

        iframe {{
            width: 100%;
            height: 520px;
            border:
                1px solid var(--borde);
            border-radius: 7px;
            background: #ffffff;
        }}

        .abrir {{
            display: inline-block;
            margin-top: 12px;
            color: var(--acento);
            text-decoration: none;
        }}

        .abrir:hover {{
            text-decoration: underline;
        }}

        @media (
            max-width: 700px
        ) {{
            body {{
                padding: 15px;
            }}

            .grid {{
                grid-template-columns:
                    1fr;
            }}

            iframe {{
                height: 400px;
            }}
        }}
    </style>
</head>

<body>

    <header>
        <div class="tag">
            QUANT PLATFORM V2.1
        </div>

        <h1>
            {html.escape(ticker)}
            — Índice de gráficas
        </h1>

        <p>
            Greeks, superficies 3D,
            posicionamiento dealer y
            escenarios ITM / ATM / OTM.
        </p>
    </header>

    {''.join(bloques)}

</body>

</html>
"""

    ruta_salida.write_text(
        documento,
        encoding="utf-8",
    )

    return ruta_salida