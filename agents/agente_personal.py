from .agente_base import AgenteBase
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import threading
from utils.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class AgentePersonal(AgenteBase):
    def __init__(self):
        super().__init__(
            nombre="Agente Personal",
            descripcion="Eres mi asistente personal experto en programacion y sistemas. Vas a ser mi profesor en temas avanzados y temas basicos"
        )
        # Inicializar bot de Telegram solo si hay configuración
        try:
            self.bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None
            self.chat_id = TELEGRAM_CHAT_ID
            self.application = None
        except Exception as e:
            print(f"⚠️  Error configurando Telegram: {e}")
            self.bot = None
            self.application = None

    async def enviar_mensaje_telegram_async(self, mensaje: str):
        """Envía un mensaje por Telegram de forma asíncrona."""
        if not self.bot or not self.chat_id:
            return "❌ Telegram no configurado. Verifica TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID"

        try:
            await self.bot.send_message(chat_id=self.chat_id, text=mensaje)
            return "✅ Mensaje enviado por Telegram"
        except Exception as e:
            return f"❌ Error enviando a Telegram: {str(e)}"

    def enviar_mensaje_telegram(self, mensaje: str):
        """Envía un mensaje por Telegram."""
        if not self.bot or not self.chat_id:
            return "❌ Telegram no configurado. Verifica TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID"

        try:
            # Crear un event loop temporal para enviar el mensaje

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.enviar_mensaje_telegram_async(mensaje))
            loop.close()
            return result
        except Exception as e:
            return f"❌ Error enviando a Telegram: {str(e)}"

    def ejecutar(self, prompt_str: str) -> str:
        """Sobrescribimos el método ejecutar para agregar funcionalidad Telegram"""
        # Primero obtenemos la respuesta normal del agente
        respuesta_agente = super().ejecutar(prompt_str)
        
        # Lógica para decidir si enviar a Telegram
        if self._debe_enviar_telegram(prompt_str):
            resultado_telegram = self.enviar_mensaje_telegram(respuesta_agente)
            return f"{respuesta_agente}\n\n---\n{resultado_telegram}"
        
        return respuesta_agente

    def _debe_enviar_telegram(self, prompt: str) -> bool:
        """Determina si debe enviar a Telegram basado en palabras clave."""
        palabras_clave = [
            "enviar", "mandar", "telegram", "notificar", 
            "envíame", "mándame", "notificarme", "avísame"
        ]
        prompt_lower = prompt.lower()
        return any(palabra in prompt_lower for palabra in palabras_clave)

    async def start_telegram_bot(self):
        """Inicia el bot de Telegram para recibir mensajes."""
        if not TELEGRAM_BOT_TOKEN:
            print("❌ No hay token de Telegram configurado")
            return

        # Crear aplicación con configuración para hilos secundarios
        builder = Application.builder().token(TELEGRAM_BOT_TOKEN)

        # Deshabilitar completamente signal handling para hilos secundarios
        self.application = builder.build()

        # Forzar la desactivación de signals que causan problemas
        try:
            # Deshabilitar signals completamente para evitar problemas en hilos
            self.application._signals = set()
            # También intentar deshabilitar en el updater
            if hasattr(self.application, 'updater') and self.application.updater:
                self.application.updater._signals = set()
        except:
            pass

        # Handler para comandos /start
        self.application.add_handler(CommandHandler("start", self.start_command))

        # Handler para mensajes de texto
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Iniciar el bot sin signal handling
        print("🤖 Bot de Telegram iniciado. Esperando mensajes...")
        try:
            # Usar una versión modificada de run_polling que no use signals
            await self._run_polling_safe()
        except Exception as e:
            print(f"❌ Error en polling: {e}")
            raise

    async def _run_polling_safe(self):
        """Versión segura de run_polling para hilos secundarios."""
        # Inicializar la aplicación
        await self.application.initialize()

        # Inicializar el updater
        await self.application.updater.initialize()

        # Configurar updater
        await self.application.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )

        # Iniciar el procesamiento de updates
        await self.application.start()

        # Mantener el bot corriendo
        print("✅ Bot procesando mensajes...")
        while True:
            await asyncio.sleep(1)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Responde al comando /start."""
        await update.message.reply_text("¡Hola! Soy tu agente personal. ¿En qué puedo ayudarte?")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes entrantes y responde usando el agente."""
        user_message = update.message.text
        print(f"📨 Mensaje recibido: {user_message}")

        # Procesar el mensaje con el agente (sin la lógica de envío automático a Telegram)
        respuesta_agente = super().ejecutar(user_message)

        # Enviar la respuesta
        await update.message.reply_text(respuesta_agente)

    def iniciar_bot_en_hilo(self):
        """Inicia el bot en un hilo separado para no bloquear la aplicación principal."""
        if not TELEGRAM_BOT_TOKEN:
            print("❌ No se puede iniciar el bot: TELEGRAM_BOT_TOKEN no configurado")
            return

        def run_bot():
            # Crear un nuevo event loop para el hilo
            try:
                # Usar nest_asyncio para permitir nested event loops
                import nest_asyncio
                nest_asyncio.apply()

                # Crear y configurar el event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Ejecutar el bot
                loop.run_until_complete(self.start_telegram_bot())
            except ImportError:
                print("❌ Instala nest_asyncio: pip install nest_asyncio")
            except Exception as e:
                print(f"❌ Error en el bot de Telegram: {e}")
                import traceback
                traceback.print_exc()
            finally:
                try:
                    if 'loop' in locals():
                        loop.close()
                except:
                    pass

        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        print("✅ Bot de Telegram iniciado en segundo plano")