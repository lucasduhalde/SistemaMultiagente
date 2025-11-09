from .agente_base import AgenteBase

class AgenteFinanzas(AgenteBase):
    def __init__(self):
        super().__init__(
            nombre="Agente Finanzas",
            descripcion="Asesor en gestión y planificación financiera"
        )
