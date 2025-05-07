import datetime
import os
import requests
import logging
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
from dotenv import load_dotenv

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de APIs
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
TIMEZONEDB_API_KEY = os.getenv('TIMEZONEDB_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

# Note: Specific model names might change. Refer to LiteLLM/Provider documentation.
MODEL_GPT_4O = "openai/gpt-4o"
MODEL_CLAUDE_SONNET = "anthropic/claude-3-sonnet-20240229"

AGENT_MODEL = MODEL_GEMINI_2_0_FLASH # Starting with Gemini

# --- Session Management ---
# Key Concept: SessionService stores conversation history & state.
# InMemorySessionService is simple, non-persistent storage for this tutorial.
session_service = InMemorySessionService()

# Define constants for identifying the interaction context
APP_NAME = "weather_tutorial_app"
USER_ID = "user_1"
SESSION_ID = "session_001" # Using a fixed ID for simplicity

# Create the specific session where the conversation will happen
session = session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID
)
print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")



# Verificar API keys
logger.info("🔑 Verificando API keys...")
logger.info(f"OPENWEATHER_API_KEY: {'Configurada ✅' if OPENWEATHER_API_KEY else 'No configurada ❌'}")
logger.info(f"TIMEZONEDB_API_KEY: {'Configurada ✅' if TIMEZONEDB_API_KEY else 'No configurada ❌'}")
logger.info(f"GOOGLE_API_KEY: {'Configurada ✅' if GOOGLE_API_KEY else 'No configurada ❌'}")



def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city using OpenWeatherMap API."""
    try:
        logger.info(f"🌤️ Iniciando solicitud de clima para la ciudad: {city}")
        
        # Hacer la petición a OpenWeatherMap
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        logger.info(f"📡 Llamando a OpenWeatherMap API para {city}")
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            temp_c = data['main']['temp']
            temp_f = (temp_c * 9/5) + 32
            weather_desc = data['weather'][0]['description']
            
            logger.info(f"✅ Datos del clima obtenidos exitosamente para {city}")
            return {
                "status": "success",
                "report": (
                    f"The weather in {city} is {weather_desc} with a temperature of "
                    f"{temp_c:.1f}°C ({temp_f:.1f}°F)."
                ),
            }
        else:
            logger.error(f"❌ Error al obtener clima para {city}. Código: {response.status_code}")
            return {
                "status": "error",
                "error_message": f"Weather information for '{city}' is not available. Error: {response.status_code}",
            }
    except Exception as e:
        logger.error(f"❌ Excepción al obtener clima para {city}: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error getting weather data: {str(e)}",
        }

def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city using TimeZoneDB API."""
    try:
        logger.info(f"🕒 Iniciando solicitud de hora para la ciudad: {city}")
        
        # Primero obtener las coordenadas de la ciudad usando OpenWeatherMap
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_API_KEY}"
        logger.info(f"📡 Llamando a OpenWeatherMap Geo API para obtener coordenadas de {city}")
        geo_response = requests.get(geo_url)
        
        if geo_response.status_code != 200:
            logger.error(f"❌ Error al obtener coordenadas para {city}")
            return {
                "status": "error",
                "error_message": f"Could not find coordinates for {city}",
            }
            
        geo_data = geo_response.json()
        if not geo_data:
            logger.error(f"❌ No se encontraron datos geográficos para {city}")
            return {
                "status": "error",
                "error_message": f"City '{city}' not found",
            }
            
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        logger.info(f"📍 Coordenadas obtenidas para {city}: lat={lat}, lon={lon}")
        
        # Obtener la zona horaria usando TimeZoneDB
        tz_url = f"http://api.timezonedb.com/v2.1/get-time-zone?key={TIMEZONEDB_API_KEY}&format=json&by=position&lat={lat}&lng={lon}"
        logger.info(f"📡 Llamando a TimeZoneDB API para {city}")
        tz_response = requests.get(tz_url)
        
        if tz_response.status_code == 200:
            tz_data = tz_response.json()
            if tz_data['status'] == 'OK':
                tz = ZoneInfo(tz_data['zoneName'])
                now = datetime.datetime.now(tz)
                logger.info(f"✅ Hora obtenida exitosamente para {city}")
                report = f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z")}'
                return {"status": "success", "report": report}
        
        logger.error(f"❌ Error al obtener zona horaria para {city}")
        return {
            "status": "error",
            "error_message": f"Could not get timezone information for {city}",
        }
    except Exception as e:
        logger.error(f"❌ Excepción al obtener hora para {city}: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error getting time data: {str(e)}",
        }

def get_forecast(city: str) -> dict:
    """Retrieves the weather forecast for the next 5 days for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the forecast.

    Returns:
        dict: status and result or error msg.
    """
    try:
        logger.info(f"🌤️ Iniciando solicitud de pronóstico para la ciudad: {city}")
        
        if not OPENWEATHER_API_KEY:
            logger.error("❌ No se encontró OPENWEATHER_API_KEY")
            return {
                "status": "error",
                "error_message": "OpenWeather API key no está configurada"
            }

        # Hacer la petición a OpenWeatherMap para el pronóstico
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        logger.info(f"📡 Llamando a OpenWeatherMap API (forecast) para {city}")
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            forecast_list = data['list']
            
            # Agrupar pronósticos por día
            daily_forecasts = {}
            for forecast in forecast_list:
                date = datetime.datetime.fromtimestamp(forecast['dt']).strftime('%Y-%m-%d')
                if date not in daily_forecasts:
                    daily_forecasts[date] = {
                        'temp_min': float('inf'),
                        'temp_max': float('-inf'),
                        'descriptions': set()
                    }
                
                daily_forecasts[date]['temp_min'] = min(daily_forecasts[date]['temp_min'], forecast['main']['temp_min'])
                daily_forecasts[date]['temp_max'] = max(daily_forecasts[date]['temp_max'], forecast['main']['temp_max'])
                daily_forecasts[date]['descriptions'].add(forecast['weather'][0]['description'])

            # Crear reporte
            forecast_report = f"Pronóstico del tiempo para {city}:\n\n"
            for date, forecast in list(daily_forecasts.items())[:5]:  # Limitamos a 5 días
                temp_min_f = (forecast['temp_min'] * 9/5) + 32
                temp_max_f = (forecast['temp_max'] * 9/5) + 32
                conditions = ", ".join(forecast['descriptions'])
                
                forecast_report += (
                    f"📅 {date}:\n"
                    f"   🌡️ Temperatura: {forecast['temp_min']:.1f}°C a {forecast['temp_max']:.1f}°C "
                    f"({temp_min_f:.1f}°F a {temp_max_f:.1f}°F)\n"
                    f"   ☁️ Condiciones: {conditions}\n\n"
                )
            
            logger.info(f"✅ Pronóstico obtenido exitosamente para {city}")
            return {
                "status": "success",
                "report": forecast_report
            }
        else:
            error_msg = f"Forecast information for '{city}' is not available. Error: {response.status_code}"
            if response.status_code == 401:
                error_msg = "API key inválida o no configurada correctamente"
            elif response.status_code == 404:
                error_msg = f"No se encontró la ciudad: {city}"
            
            logger.error(f"❌ Error al obtener pronóstico para {city}. {error_msg}")
            return {
                "status": "error",
                "error_message": error_msg
            }
            
    except Exception as e:
        logger.error(f"❌ Excepción al obtener pronóstico para {city}: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error getting forecast data: {str(e)}"
        }

root_agent = Agent(
    name="weather_time_assistant",
    model=AGENT_MODEL,
    description=(
        "Soy un asistente especializado que proporciona información precisa y en tiempo real "
        "sobre el clima actual, pronóstico del tiempo y la hora en cualquier ciudad del mundo. "
        "Utilizo datos de OpenWeatherMap para el clima y pronóstico, y TimeZoneDB para las zonas horarias."
    ),
    instruction=(
        "Responde siempre en español. "
        "Cuando te pregunten sobre el clima actual, usa la función get_weather. "
        "Cuando te pregunten sobre el pronóstico, usa la función get_forecast. "
        "Cuando te pregunten sobre la hora, usa la función get_current_time. "
        "Si te preguntan por múltiples datos, usa las funciones necesarias. "
        "Si hay un error, explica claramente qué sucedió y sugiere alternativas. "
        "Sé amable y conversacional, pero mantén las respuestas concisas y relevantes. "
        "Si la ciudad no se especifica claramente en la pregunta, pide una aclaración."
    ),
    tools=[get_weather, get_current_time, get_forecast],
)

# Log cuando el módulo se carga
logger.info("🚀 Agente de clima y hora inicializado y listo para usar")

# --- Runner ---
# Key Concept: Runner orchestrates the agent execution loop.
runner = Runner(
    agent=root_agent, # The agent we want to run
    app_name=APP_NAME,   # Associates runs with our app
    session_service=session_service # Uses our session manager
)
print(f"Runner created for agent '{runner.agent.name}'.")


async def call_agent_async(query: str, runner, user_id, session_id):
  """Sends a query to the agent and prints the final response."""
  print(f"\n>>> User Query: {query}")

  # Prepare the user's message in ADK format
  content = types.Content(role='user', parts=[types.Part(text=query)])

  final_response_text = "Agent did not produce a final response." # Default

  # Key Concept: run_async executes the agent logic and yields Events.
  # We iterate through events to find the final answer.
  async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
      # You can uncomment the line below to see *all* events during execution
      # print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

      # Key Concept: is_final_response() marks the concluding message for the turn.
      if event.is_final_response():
          if event.content and event.content.parts:
             # Assuming text response in the first part
             final_response_text = event.content.parts[0].text
          elif event.actions and event.actions.escalate: # Handle potential errors/escalations
             final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
          # Add more checks here if needed (e.g., specific error codes)
          break # Stop processing events once the final response is found

  print(f"<<< Agent Response: {final_response_text}")

# Función principal para ejecutar la conversación
async def run_conversation():
    await call_agent_async("¿Cómo está el clima en Londres?",
                          runner=runner,
                          user_id=USER_ID,
                          session_id=SESSION_ID)

    await call_agent_async("¿Y en París?",
                          runner=runner,
                          user_id=USER_ID,
                          session_id=SESSION_ID)

    await call_agent_async("Dime el clima en Nueva York",
                          runner=runner,
                          user_id=USER_ID,
                          session_id=SESSION_ID)
      
    await call_agent_async("Dime el forecast en Cochabamba",
                          runner=runner,
                          user_id=USER_ID,
                          session_id=SESSION_ID)
    # Execute the conversation using await in an async context (like Colab/Jupyter)


import asyncio
if __name__ == "__main__":
    try:
        asyncio.run(run_conversation())
    except Exception as e:
        print(f"An error occurred: {e}")