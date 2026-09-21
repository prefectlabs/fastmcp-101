"""Tests for the weather server.

These use FastMCP's in-memory client: the test talks to the server object
directly, with no network, no subprocess, and no port. The only tests that
reach the internet are marked ``integration`` and skipped by default.

Run everything that is offline with:  pytest
Run the network tests too with:       pytest -m integration
"""

import pytest
from fastmcp import Client

from weather_server.server import mcp

EXPECTED_TOOLS = {
    "get_weather_forecast",
    "get_historical_weather",
    "calculate_rain_probability",
}


async def test_all_three_tools_are_registered():
    async with Client(mcp) as client:
        names = {tool.name for tool in await client.list_tools()}
    missing = EXPECTED_TOOLS - names
    assert not missing, f"Add @mcp.tool above these functions: {sorted(missing)}"


async def test_tool_descriptions_come_from_docstrings():
    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
    forecast = tools["get_weather_forecast"]
    assert forecast.description.startswith("Get the daily weather forecast")
    assert set(forecast.input_schema["properties"]) == {"location", "days_ahead"}


async def test_forecast_rejects_out_of_range_days():
    # Validation runs before any network call, so this stays offline.
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_weather_forecast", {"location": "Washington", "days_ahead": 30}
        )
    assert "between 1 and 16" in result.data


async def test_historical_rejects_bad_date_format():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_historical_weather", {"location": "Denver", "date": "July 4 2023"}
        )
    assert "YYYY-MM-DD" in result.data


async def test_about_resource_is_readable():
    async with Client(mcp) as client:
        contents = await client.read_resource("weather://about")
    assert "Open-Meteo" in contents[0].text


async def test_plan_outdoor_event_prompt_fills_in_arguments():
    async with Client(mcp) as client:
        prompt = await client.get_prompt(
            "plan_outdoor_event", {"location": "Chicago", "date": "2026-10-01"}
        )
    text = prompt.messages[0].content.text
    assert "Chicago" in text and "2026-10-01" in text


@pytest.mark.integration
async def test_live_forecast_returns_daily_lines():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_weather_forecast", {"location": "Washington", "days_ahead": 3}
        )
    assert "Forecast for Washington" in result.data
    assert result.data.count(" F, ") == 3
