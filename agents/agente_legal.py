from .agente_base import AgenteBase

class AgenteLegal(AgenteBase):
    def __init__(self):
        super().__init__(
            nombre="Agente Legal",
            descripcion="Asesor en procesos legales chilenos"
        )