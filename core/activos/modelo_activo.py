from dataclasses import dataclass

from core.activos.capacidades import CapacidadesActivo
from core.activos.clases_activo import ClaseActivo


@dataclass(frozen=True, slots=True)
class Activo:
    """Representación universal de un activo financiero."""

    simbolo: str
    clase: ClaseActivo

    benchmark: str
    divisa: str
    proveedor: str

    mercado: str | None = None
    descripcion: str | None = None

    capacidades: CapacidadesActivo = CapacidadesActivo()

    def resumen(self) -> str:
        """Devuelve un resumen legible del activo."""

        mercado = (
            self.mercado
            if self.mercado is not None
            else "DESCONOCIDO"
        )

        return (
            f"{self.simbolo} | "
            f"{self.clase.value} | "
            f"{mercado} | "
            f"{self.divisa} | "
            f"Benchmark: {self.benchmark}"
        )