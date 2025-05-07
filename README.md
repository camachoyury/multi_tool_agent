# Asistente de Clima y Hora con Google ADK

Este proyecto implementa un agente conversacional utilizando Google ADK (Agent Development Kit) que proporciona información en tiempo real sobre el clima y la hora en diferentes ciudades del mundo.

## 🚀 Características

- Consulta del clima actual en cualquier ciudad
- Pronóstico del tiempo para los próximos 5 días
- Información de la hora actual en diferentes zonas horarias
- Interfaz conversacional en español
- Integración con APIs reales (OpenWeatherMap y TimeZoneDB)

## 📋 Prerrequisitos

- Python 3.8 o superior
- Cuenta en OpenWeatherMap (API key)
- Cuenta en TimeZoneDB (API key)
- Cuenta en Google Cloud (API key)

## 🔧 Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd ADK
```

2. Crear y activar un entorno virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
Crear un archivo `.env` en la carpeta `multi_tool_agent` con las siguientes variables:
```env
OPENWEATHER_API_KEY=tu_api_key_aquí
TIMEZONEDB_API_KEY=tu_api_key_aquí
GOOGLE_API_KEY=tu_api_key_aquí
```

## 🏃‍♂️ Uso

Para ejecutar el agente:

```bash
python multi_tool_agent/agent.py
```

El agente responderá a consultas como:
- "¿Cómo está el clima en Londres?"
- "¿Y en París?"
- "Dime el clima en Nueva York"
- "Dime el forecast en Cochabamba"

## 📄 Estructura del Proyecto 


## 📄 Estructura del Proyecto 

ADK/
├── multi_tool_agent/
│ ├── init.py
│ ├── agent.py
│ └── .env
├── requirements.txt
└── README.md


## 🛠️ Tecnologías Utilizadas

- Google ADK (Agent Development Kit)
- OpenWeatherMap API
- TimeZoneDB API
- Python 3.8+
- asyncio para operaciones asíncronas

## 📝 Notas

- El agente está configurado para responder en español
- Utiliza el modelo Gemini 2.0 Flash por defecto
- Las respuestas incluyen temperaturas en Celsius y Fahrenheit
- Incluye manejo de errores y logging detallado

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue para discutir los cambios propuestos.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

