from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.agente_legal import AgenteLegal
from agents.agente_finanzas import AgenteFinanzas
from agents.agente_personal import AgentePersonal

app = FastAPI(title="AgenteHub")

# Registro de agentes
agentes = {
    "legal": AgenteLegal(),
    "finanzas": AgenteFinanzas(),
    "personal": AgentePersonal(),
}

# Iniciar el bot de Telegram para el agente personal
if "personal" in agentes:
    agentes["personal"].iniciar_bot_en_hilo()

class PromptInput(BaseModel):
    prompt: str

@app.get("/")
def home():
    return {"message": "AgenteHub activo 🚀", "agentes_disponibles": list(agentes.keys())}

@app.post("/run/{nombre_agente}")
def run_agente(nombre_agente: str, data: PromptInput):
    if nombre_agente not in agentes:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    respuesta = agentes[nombre_agente].ejecutar(data.prompt)
    return {"agente": nombre_agente, "respuesta": respuesta}
