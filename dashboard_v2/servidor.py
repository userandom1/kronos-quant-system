from __future__ import annotations

import traceback
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.responses import (
    FileResponse,
    JSONResponse,
    Response,
)
from starlette.routing import Route
from starlette.staticfiles import StaticFiles

from motor_sistema.api_v2 import (
    api_activo,
    api_health,
    api_universo,
    api_watchlist,
    api_watchlists,
)


RUTA_BASE = Path(
    __file__
).resolve().parents[1]

RUTA_STATIC = (
    RUTA_BASE
    / "dashboard_v2"
    / "static"
)


def respuesta_error(
    error: Exception,
) -> JSONResponse:
    """Construye respuesta estándar para errores API."""

    traceback.print_exc()

    return JSONResponse(
        {
            "error": str(
                error
            ),
            "tipo": type(
                error
            ).__name__,
        },
        status_code=500,
    )


async def inicio(
    request,
) -> FileResponse:
    """Entrega el dashboard."""

    return FileResponse(
        RUTA_STATIC
        / "index.html"
    )


async def favicon(
    request,
) -> Response:
    """Evita un 404 innecesario del navegador."""

    return Response(
        status_code=204
    )


async def health(
    request,
) -> JSONResponse:
    """API de Health Check."""

    try:
        return JSONResponse(
            api_health()
        )

    except Exception as error:
        return respuesta_error(
            error
        )


async def activo(
    request,
) -> JSONResponse:
    """API de análisis individual."""

    simbolo = (
        request.path_params[
            "simbolo"
        ]
        .strip()
        .upper()
    )

    try:
        horizonte = int(
            request.query_params.get(
                "horizonte",
                "20",
            )
        )

        resultado = api_activo(
            simbolo=simbolo,
            horizonte=horizonte,
        )

        return JSONResponse(
            resultado
        )

    except Exception as error:
        return respuesta_error(
            error
        )


async def universo(
    request,
) -> JSONResponse:
    """API de análisis de universo."""

    nombre = (
        request.path_params[
            "nombre"
        ]
        .strip()
        .upper()
    )

    try:
        resultado = api_universo(
            nombre
        )

        return JSONResponse(
            resultado
        )

    except Exception as error:
        return respuesta_error(
            error
        )


async def watchlists(
    request,
) -> JSONResponse:
    """API con las watchlists disponibles."""

    try:
        return JSONResponse(
            api_watchlists()
        )

    except Exception as error:
        return respuesta_error(
            error
        )


async def watchlist(
    request,
) -> JSONResponse:
    """API de análisis de watchlist."""

    nombre = (
        request.path_params[
            "nombre"
        ]
        .strip()
        .upper()
    )

    try:
        resultado = api_watchlist(
            nombre
        )

        return JSONResponse(
            resultado
        )

    except Exception as error:
        return respuesta_error(
            error
        )


rutas = [
    Route(
        "/",
        inicio,
    ),
    Route(
        "/favicon.ico",
        favicon,
    ),
    Route(
        "/api/v2/health",
        health,
    ),
    Route(
        "/api/v2/activo/{simbolo}",
        activo,
    ),
    Route(
        "/api/v2/universo/{nombre}",
        universo,
    ),
    Route(
        "/api/v2/watchlists",
        watchlists,
    ),
    Route(
        "/api/v2/watchlist/{nombre}",
        watchlist,
    ),
]


app = Starlette(
    debug=False,
    routes=rutas,
)


app.mount(
    "/static",
    StaticFiles(
        directory=RUTA_STATIC,
    ),
    name="static",
)


def main() -> None:
    """Lanza el Dashboard V2."""

    uvicorn.run(
        "dashboard_v2.servidor:app",
        host="127.0.0.1",
        port=8010,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()