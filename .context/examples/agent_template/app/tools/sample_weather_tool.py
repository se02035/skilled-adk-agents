"""
Filename: sample_weather_tool.py
Author: Oliver Lintner  
Date: 2026-02-22
Version: 1.0
Description: 
    This script demonstrates a sample weather tool for ADK agent.

License: MIT License
Contact: [EMAIL_ADDRESS]
Dependencies: 
"""

def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": (
                "The weather in New York is sunny with a temperature of 25 degrees"
                " Celsius (77 degrees Fahrenheit)."
            ),
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }