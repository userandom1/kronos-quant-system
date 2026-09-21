from __future__ import annotations

import json
from pathlib import Path

import uvicorn

from starlette.applications import Starlette
from starlette.responses import (
    FileResponse,
    JSONResponse,
)
from starlette.routing import Route
from starlette.staticfiles import StaticFiles

from dashboard.cargador_datos import (
    construir_resumen_dashboard,
    cargar_dataset,
    cargar_todos_disponibles,
)
from dashboard.estado_sistema import (
    obtener_estado_sistema,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_STATIC = (
    RUTA_BASE
    / "dashboard"
    / "static"
)


async def pagina_principal(
    request,
):
    """Sirve la aplicación principal."""

    return FileResponse(
        RUTA_STATIC
        / "index.html"
    )


async def api_estado(
    request,
):
    """Devuelve estado general del sistema."""

    estado = obtener_estado_sistema()

    estado[
        "datasets"
    ] = cargar_todos_disponibles()

    return JSONResponse(
        estado
    )


async def api_resumen(
    request,
):
    """Devuelve KPIs principales."""

    datos = construir_resumen_dashboard()

    return JSONResponse(
        datos
    )


async def api_dataset(
    request,
):
    """Devuelve cualquier dataset registrado."""

    nombre = request.path_params[
        "nombre"
    ]

    try:
        datos = cargar_dataset(
            nombre
        )

        return JSONResponse(
            datos
        )

    except KeyError as exc:

        return JSONResponse(
            {
                "error": str(
                    exc
                )
            },
            status_code=404,
        )

    except Exception as exc:

        return JSONResponse(
            {
                "error": str(
                    exc
                )
            },
            status_code=500,
        )


routes = [
    Route(
        "/",
        pagina_principal,
    ),
    Route(
        "/api/estado",
        api_estado,
    ),
    Route(
        "/api/resumen",
        api_resumen,
    ),
    Route(
        "/api/datos/{nombre}",
        api_dataset,
    ),
]


app = Starlette(
    debug=False,
    routes=routes,
)


app.mount(
    "/static",
    StaticFiles(
        directory=RUTA_STATIC
    ),
    name="static",
)


def main() -> None:
    """Arranca el servidor local."""

    uvicorn.run(
        "dashboard.servidor_perspective:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()