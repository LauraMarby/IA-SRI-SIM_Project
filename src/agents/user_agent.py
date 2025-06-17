from agents.base_agent import BaseAgent
from ui import user_interface as ui

class UserAgent(BaseAgent):
    """
    Agente responsable de la interacción con el usuario.

    Este agente se encarga de mostrar mensajes en la interfaz, recoger la entrada del usuario,
    y gestionar la comunicación con el detector de intenciones y el coordinador para obtener
    respuestas adecuadas.
    """
    async def run(self):
        """
        Ejecuta el ciclo principal del agente de usuario.

        - Muestra un mensaje de bienvenida.
        - Espera entradas del usuario a través de la interfaz.
        - Si el usuario escribe "salir", "exit" o "quit", muestra mensaje de salida y termina.
        - Envia la entrada del usuario al agente `intent_detector`.
        - Espera la detección de intención y la reenvía al `coordinator`.
        - Espera respuestas del `coordinator` y las muestra usando la interfaz de usuario.
        - Si la intención es "await", continúa esperando resultados adicionales (por ejemplo, de múltiples fuentes).
        """

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

            # Esperar respuesta final del coordinator
            
            while True:
                final_response = await self.receive()
                intencion = final_response['content']['intencion']
                result = final_response['content']['content']
                # Mostrar respuesta final al usuario
                ui.show_response(result)
                if intencion != "await":
                    break
