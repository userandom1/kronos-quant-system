"""Comprueba la integridad y las conciliaciones de una ejecución guardada."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


CAMPOS = (
    "contratos_con_griegas",
    "contratos_con_oi",
    "oi_conocido",
    "delta_oi_unidades",
    "gamma_oi_unidades_por_precio",
)


def exigir(condicion: bool, mensaje: str) -> None:
    if not condicion:
        raise ValueError(mensaje)


def conciliar(detalle: list[dict], resumen: list[dict], claves: tuple[str, ...], campos: tuple[str, ...]) -> None:
    grupos: dict[tuple, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for fila in detalle:
        clave = tuple(fila[c] for c in claves)
        for campo in campos:
            grupos[clave][campo] += float(fila[campo])
    exigir(len(grupos) == len(resumen), f"grupos distintos en {claves}")
    for fila in resumen:
        clave = tuple(fila[c] for c in claves)
        exigir(clave in grupos, f"grupo ausente: {clave}")
        for campo in campos:
            esperado = grupos[clave][campo]
            obtenido = float(fila[campo])
            exigir(math.isclose(obtenido, esperado, rel_tol=1e-10, abs_tol=1e-8),
                   f"{campo} no concilia en {clave}: {obtenido} != {esperado}")


def verificar(ruta: Path) -> dict:
    ruta = ruta.resolve()
    manifiesto = json.loads((ruta / "manifiesto.json").read_text(encoding="utf-8"))
    huellas = manifiesto["archivos_sha256"]
    for nombre, huella in huellas.items():
        archivo = (ruta / nombre).resolve()
        exigir(archivo.parent == ruta and archivo.is_file(), f"archivo ausente o fuera de ejecución: {nombre}")
        exigir(hashlib.sha256(archivo.read_bytes()).hexdigest() == huella,
               f"huella incorrecta: {nombre}")
    exigir(manifiesto["huella_analisis"] == huellas["informe.json"],
           "la huella del análisis no coincide con el informe")

    informe = json.loads((ruta / "informe.json").read_text(encoding="utf-8"))
    actual = informe["captura_actual"]
    exigir(actual["filas"] == actual["validos"] + actual["rechazados"],
           "filas de captura no concilian")
    exigir(actual["validos"] == len(informe["griegas"]) + len(informe["omitidos_griegas"]),
           "cobertura de griegas no concilia")
    exigir(actual["sha256_metadatos"] == hashlib.sha256((ruta / "actual_metadatos.json").read_bytes()).hexdigest(),
           "metadatos de captura no concilian")
    exigir(actual["sha256_csv"] == hashlib.sha256((ruta / "actual_contratos.csv").read_bytes()).hexdigest(),
           "CSV de captura no concilia")
    conciliar(informe["agregados_strike"], informe["agregados_vencimiento"],
             ("vencimiento", "tipo"), CAMPOS)

    escenario = informe.get("escenario_dealer_strike")
    if escenario is not None:
        conciliar(escenario, informe["escenario_dealer_vencimiento"],
                 ("vencimiento",), tuple(c for c in CAMPOS if c != "oi_conocido"))
        exigir(all(f["convencion"] == "HIPOTESIS_CALLS_CORTAS_PUTS_LARGAS" for f in escenario),
               "convención dealer no identificada")

    actividad = informe.get("actividad")
    comparables = 0
    if actividad is not None:
        exigir(actividad["tipo_dato"] != "OPERACIONES_INDIVIDUALES",
               "comparación de capturas mal etiquetada")
        filas = actividad["contratos"]
        comparables = sum(f["incremento_volumen_estimado"] is not None for f in filas)
        exigir(len(filas) == actual["validos"], "cobertura de actividad no concilia")
        esperado = defaultdict(lambda: [0, 0, 0])
        for fila in filas:
            clave = (fila["vencimiento"], fila["tipo"])
            esperado[clave][0] += 1
            if fila["incremento_volumen_estimado"] is not None:
                esperado[clave][1] += 1
                esperado[clave][2] += int(fila["incremento_volumen_estimado"])
        exigir(len(esperado) == len(informe["actividad_por_vencimiento"]),
               "grupos de actividad no concilian")
        for fila in informe["actividad_por_vencimiento"]:
            clave = (fila["vencimiento"], fila["tipo"])
            actuales, comparables_grupo, incremento = esperado[clave]
            esperado_resumen = [actuales, comparables_grupo,
                                incremento if comparables_grupo else None]
            exigir(esperado_resumen == [fila["contratos_actuales"],
                                        fila["contratos_comparables"],
                                        fila["incremento_volumen_estimado"]],
                   f"actividad no concilia en {clave}")

    return {
        "ejecucion": ruta.name,
        "sha256_informe": huellas["informe.json"],
        "archivos_verificados": len(huellas),
        "contratos": actual["filas"],
        "griegas": len(informe["griegas"]),
        "omitidos": len(informe["omitidos_griegas"]),
        "contratos_comparables": comparables,
        "estado": "OK",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ejecucion", type=Path)
    args = parser.parse_args()
    print(json.dumps(verificar(args.ejecucion), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
