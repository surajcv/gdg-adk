import datetime
import os
import requests
from zoneinfo import ZoneInfo
from timezonefinder import TimezoneFinder
from google.adk.agents import Agent

def get_weather(city: str) -> dict:
    """Retrieves the current weather report and timezone for any city.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result (including timezone) or error msg.
    """
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        return {
            "status": "error",
            "error_message": "API key not found. Please set OPENWEATHER_API_KEY environment variable.",
        }
    
    # Get weather and coordinates
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        lat = data['coord']['lat']
        lon = data['coord']['lon']
        
        # Get timezone from coordinates
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=lat, lng=lon)
        
        if not timezone_str:
            timezone_str = "UTC"
        
        report = (
            f"The weather in {city} (Lat: {lat}, Lon: {lon}, Timezone: {timezone_str}) is {description} "
            f"with a temperature of {temp}°C. Humidity is {humidity}%, and wind speed is {wind_speed} m/s."
        )
        return {
            "status": "success",
            "report": report,
            "timezone": timezone_str,
            "latitude": lat,
            "longitude": lon,
            "temperature": temp,
            "description": description,
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error_message": f"Failed to retrieve weather data: {str(e)}",
        }
    except KeyError as e:
        return {
            "status": "error",
            "error_message": f"Invalid response from weather API for city '{city}': {str(e)}",
        }


def get_current_time(city: str) -> dict:
    """Returns the current time in any city by automatically determining its timezone.

    Args:
        city (str): The name of the city for which to retrieve the current time.

    Returns:
        dict: status and result or error msg.
    """
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        return {
            "status": "error",
            "error_message": "API key not found. Please set OPENWEATHER_API_KEY environment variable.",
        }
    
    # Get city coordinates and timezone via weather API
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        lat = data['coord']['lat']
        lon = data['coord']['lon']
        
        # Get timezone from coordinates
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=lat, lng=lon)
        
        if not timezone_str:
            return {
                "status": "error",
                "error_message": f"Could not determine timezone for {city}.",
            }
        
        tz = ZoneInfo(timezone_str)
        now = datetime.datetime.now(tz)
        report = (
            f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
        )
        return {
            "status": "success",
            "report": report,
            "timezone": timezone_str,
            "latitude": lat,
            "longitude": lon,
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error_message": f"Failed to retrieve location data for city '{city}': {str(e)}",
        }
    except KeyError:
        return {
            "status": "error",
            "error_message": f"Invalid response from API for city '{city}'.",
        }


root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.5-flash",
    description=(
        "Agent to answer questions about the time and weather in a city."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city."
    ),
    tools=[get_weather, get_current_time],
)