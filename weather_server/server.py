"""Weather MCP server for the FastMCP 101 course.

Three plain Python functions live in this file. Each one calls Open-Meteo,
a free weather API that needs no account or key, and returns a readable
string. Your job in the course is to turn them into MCP tools by adding the
``@mcp.tool`` decorator above each one, then add a resource and a prompt.

Helper functions start with an underscore. They are shared plumbing and are
never exposed to the AI assistant.
"""

from datetime import datetime, timedelta

import requests
from fastmcp import FastMCP

# The server object. Every tool, resource, and prompt registers against it.
mcp = FastMCP("Weather Server")

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
DAILY_FIELDS = "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code"


def _geocode_location(location: str) -> dict | None:
    """Turn a place name into coordinates using Open-Meteo's geocoder."""
    params = {"name": location, "count": 1, "language": "en", "format": "json"}
    try:
        response = requests.get(GEOCODE_URL, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get("results")
    except requests.RequestException:
        return None
    if not results:
        return None
    hit = results[0]
    return {
        "latitude": hit["latitude"],
        "longitude": hit["longitude"],
        "name": hit["name"],
        "country": hit.get("country", ""),
    }


def _describe_weather_code(code: int) -> str:
    """Translate a WMO weather code into plain English."""
    codes = {
        0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 48: "Foggy", 51: "Light drizzle", 53: "Drizzle",
        55: "Heavy drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain",
        71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
        80: "Light showers", 81: "Showers", 82: "Heavy showers",
        85: "Light snow showers", 86: "Snow showers", 95: "Thunderstorm",
        96: "Thunderstorm with hail", 99: "Thunderstorm with hail",
    }
    return codes.get(code, "Unknown")


# TODO (Lesson 2): add @mcp.tool above this function
def get_weather_forecast(location: str, days_ahead: int = 7) -> str:
    """Get the daily weather forecast for a location, up to 16 days ahead.

    Args:
        location: City or place name, for example "Washington" or "Denver".
        days_ahead: How many days to forecast, from 1 to 16. Defaults to 7.
    """
    if days_ahead < 1 or days_ahead > 16:
        return "Error: days_ahead must be between 1 and 16."

    coords = _geocode_location(location)
    if not coords:
        return f"Error: could not find a location called '{location}'."

    params = {
        "latitude": coords["latitude"],
        "longitude": coords["longitude"],
        "daily": DAILY_FIELDS,
        "forecast_days": days_ahead,
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
    }
    try:
        response = requests.get(FORECAST_URL, params=params, timeout=10)
        response.raise_for_status()
        daily = response.json()["daily"]
    except requests.RequestException as exc:
        return f"Error fetching forecast: {exc}"

    lines = [f"Forecast for {coords['name']}, {coords['country']} ({days_ahead} days):", ""]
    for i in range(days_ahead):
        lines.append(
            f"{daily['time'][i]}: {daily['temperature_2m_min'][i]}-{daily['temperature_2m_max'][i]} F, "
            f"{_describe_weather_code(daily['weather_code'][i])}, "
            f"precipitation {daily['precipitation_sum'][i]} in"
        )
    return "\n".join(lines)


# TODO (Lesson 2): add @mcp.tool above this function
def get_historical_weather(location: str, date: str) -> str:
    """Get the recorded weather for a location on a past date.

    Args:
        location: City or place name, for example "Washington" or "Denver".
        date: The date to look up, in YYYY-MM-DD format, for example "2023-07-04".
    """
    try:
        target = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return f"Error: '{date}' is not a valid date. Use YYYY-MM-DD."
    if target > datetime.now():
        return f"Error: {date} is in the future. Use get_weather_forecast for future dates."
    if target < datetime.now() - timedelta(days=365 * 80):
        return f"Error: {date} is too far back. History covers roughly the last 80 years."

    coords = _geocode_location(location)
    if not coords:
        return f"Error: could not find a location called '{location}'."

    params = {
        "latitude": coords["latitude"],
        "longitude": coords["longitude"],
        "start_date": date,
        "end_date": date,
        "daily": DAILY_FIELDS,
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
    }
    try:
        response = requests.get(ARCHIVE_URL, params=params, timeout=10)
        response.raise_for_status()
        daily = response.json()["daily"]
    except requests.RequestException as exc:
        return f"Error fetching historical weather: {exc}"

    precip = daily["precipitation_sum"][0]
    rained = f"It rained ({precip} in)." if precip and precip > 0 else "No precipitation recorded."
    return (
        f"Weather in {coords['name']}, {coords['country']} on {date}:\n"
        f"Temperature: {daily['temperature_2m_min'][0]}-{daily['temperature_2m_max'][0]} F\n"
        f"Conditions: {_describe_weather_code(daily['weather_code'][0])}\n"
        f"{rained}"
    )


# TODO (Lesson 2): add @mcp.tool above this function
def calculate_rain_probability(location: str, date: str) -> str:
    """Estimate the chance of rain on a future date, up to 16 days ahead.

    Combines the last five years of history for that calendar date with the
    current forecast, so the answer is grounded in both patterns and prediction.

    Args:
        location: City or place name, for example "Washington" or "Denver".
        date: The future date to assess, in YYYY-MM-DD format.
    """
    try:
        target = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return f"Error: '{date}' is not a valid date. Use YYYY-MM-DD."
    today = datetime.now().date()
    if target < today:
        return f"Error: {date} is in the past. Use get_historical_weather for past dates."
    days_ahead = (target - today).days
    if days_ahead > 16:
        return f"Error: {date} is more than 16 days away, which is as far as forecasts go."

    coords = _geocode_location(location)
    if not coords:
        return f"Error: could not find a location called '{location}'."

    # Same calendar date, each of the last five years.
    history = []
    for years_back in range(1, 6):
        past = target.replace(year=target.year - years_back).isoformat()
        params = {
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "start_date": past,
            "end_date": past,
            "daily": "precipitation_sum",
            "precipitation_unit": "inch",
        }
        try:
            response = requests.get(ARCHIVE_URL, params=params, timeout=10)
            response.raise_for_status()
            value = response.json()["daily"]["precipitation_sum"][0]
        except (requests.RequestException, KeyError, IndexError):
            continue
        if value is not None:
            history.append(value)

    lines = [f"Rain outlook for {coords['name']}, {coords['country']} on {date}:", ""]

    historical_prob = None
    if history:
        rainy_years = sum(1 for p in history if p > 0.01)
        historical_prob = rainy_years / len(history) * 100
        lines.append(
            f"History: rained on this date in {rainy_years} of the last {len(history)} years "
            f"({historical_prob:.0f}%)."
        )
    else:
        lines.append("History: not available.")

    # Forecast for the target day.
    forecast_precip = None
    params = {
        "latitude": coords["latitude"],
        "longitude": coords["longitude"],
        "daily": "precipitation_sum",
        "forecast_days": min(days_ahead + 1, 16),
        "precipitation_unit": "inch",
    }
    try:
        response = requests.get(FORECAST_URL, params=params, timeout=10)
        response.raise_for_status()
        forecast_precip = response.json()["daily"]["precipitation_sum"][days_ahead]
    except (requests.RequestException, KeyError, IndexError):
        pass

    if forecast_precip is not None:
        verdict = "rain likely" if forecast_precip > 0.01 else "no rain expected"
        lines.append(f"Forecast: {forecast_precip:.2f} in of precipitation, {verdict}.")
    else:
        lines.append("Forecast: not available.")

    # Blend the two signals. Forecast counts more when it predicts rain.
    if historical_prob is not None and forecast_precip is not None:
        forecast_weight = 0.4 if forecast_precip > 0.01 else 0.2
        forecast_signal = 100 if forecast_precip > 0.01 else 0
        combined = historical_prob * (1 - forecast_weight) + forecast_signal * forecast_weight
    elif historical_prob is not None:
        combined = historical_prob
    else:
        lines.append("")
        lines.append("Not enough data to estimate a probability.")
        return "\n".join(lines)

    lines.append("")
    lines.append(f"Estimated chance of rain: {combined:.0f}%")
    if combined >= 70:
        lines.append("High. Plan for rain.")
    elif combined >= 40:
        lines.append("Moderate. Have a backup plan.")
    else:
        lines.append("Low. Looks promising.")
    return "\n".join(lines)


# TODO (Lesson 3): add a resource and a prompt below this line


if __name__ == "__main__":
    # Runs over stdio, the transport local clients like Claude Desktop use.
    mcp.run()
