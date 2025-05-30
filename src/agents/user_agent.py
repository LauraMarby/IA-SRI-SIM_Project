from agents.base_agent import BaseAgent
from ui import user_interface as ui

class UserAgent(BaseAgent):
    async def run(self):
        ui.show_welcome_message()

        while True:
            user_input = ui.get_user_input()

            if user_input.lower() in ['salir', 'exit', 'quit']:
                ui.show_exit_message()
                break

            # Enviar input al detector de intención
            await self.send("intent_detector", {"text": user_input})

            # Esperar respuesta del detector
            intent_response = await self.receive()
            intent_data = intent_response["content"]

            # Enviar datos al coordinator
            await self.send("coordinator", intent_data)

            # Esperar respuesta final del knowledge agent
            final_response = await self.receive()
            result = final_response["content"]

            # Mostrar respuesta final al usuario
            ui.show_response(result)