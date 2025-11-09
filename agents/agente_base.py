from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableSequence
from langchain.tools import tool
from utils.config import OPENAI_API_KEY, GROK_API_KEY 
from langchain_xai import ChatXAI


class AgenteBase:
    def __init__(self, nombre: str, descripcion: str, tools=None):
        self.nombre = nombre
        self.descripcion = descripcion
        self.tools = tools or []

        # Inicializamos el modelo
        self.llm = ChatXAI(
            xai_api_key=GROK_API_KEY,
            model="grok-4-latest",
        )

        # Creamos un prompt moderno
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are {self.nombre}. {self.descripcion}"),
            MessagesPlaceholder("agent_scratchpad"),
            ("human", "{input}")
        ])

        # Creamos el pipeline: prompt → llm
        self.agent = RunnableSequence(self.prompt | self.llm)

    def ejecutar(self, prompt_str: str) -> str:
        response = self.agent.invoke({"input": prompt_str, "agent_scratchpad": []})
        return response.content if hasattr(response, "content") else str(response)
