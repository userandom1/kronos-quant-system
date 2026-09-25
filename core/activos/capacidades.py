from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CapacidadesActivo:
    """
    Capacidades disponibles para un activo.

    Estas capacidades representan lo que la plataforma puede intentar
    ejecutar sobre el activo, no una garantía de que el proveedor
    actual disponga siempre de todos los datos necesarios.
    """

    historico: bool = True
    intradia: bool = True
    senales: bool = True
    portfolio: bool = True
    riesgo: bool = True

    opciones: bool = False
    options_flow: bool = False
    dealer_engine: bool = False

    forecast: bool = True
    volatilidad_implicita: bool = False
    superficie_volatilidad: bool = False

    def como_dict(self) -> dict[str, bool]:
        """Devuelve las capacidades como diccionario."""

        return {
            "historico": self.historico,
            "intradia": self.intradia,
            "senales": self.senales,
            "portfolio": self.portfolio,
            "riesgo": self.riesgo,
            "opciones": self.opciones,
            "options_flow": self.options_flow,
            "dealer_engine": self.dealer_engine,
            "forecast": self.forecast,
            "volatilidad_implicita": (
                self.volatilidad_implicita
            ),
            "superficie_volatilidad": (
                self.superficie_volatilidad
            ),
        }