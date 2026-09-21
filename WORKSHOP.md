# FastMCP 101 Workshop

Five lessons, about an hour of hands-on work. Each lesson tells you what you are
building and why before you type anything, then gives you the exact commands,
then tells you what success looks like.

Before you start, finish the setup in [README.md](README.md) and make sure
`fastmcp version` prints a 4.x version from inside your virtual environment.
All commands below run from the repo root.

---

## Lesson 1: Build your first MCP server

### What's going on

Every AI assistant has its own way of reaching outside systems, and until
recently every team wrote its own glue code for each one. MCP replaces that
with a shared standard. You build one **server** that offers capabilities, and
any MCP **client** (Claude, ChatGPT, Cursor, a chatbot your agency built) can
use it. The utility company doesn't care what you plug into the outlet; the
assistant doesn't care what's behind your server.

A server offers three kinds of things:

- **Tools**: functions the assistant can call. Verbs. *Look up a forecast.*
- **Resources**: content the assistant can read. Nouns. *The data dictionary.*
- **Prompts**: saved instructions with blanks to fill in. Recipes. *Brief me on X.*

FastMCP is the Python framework that handles the protocol so you don't have to.
You write a normal function, put one decorator on it, and it becomes a tool.

### Do it

Create a file called `hello.py` in the repo root:

```python
from fastmcp import FastMCP

mcp = FastMCP("Hello Server")


@mcp.tool
def greet(name: str) -> str:
    """Say hello to someone by name."""
    return f"Hello, {name}! Welcome to MCP."


if __name__ == "__main__":
    mcp.run()
```

Four things to notice. `FastMCP("Hello Server")` creates the server. `@mcp.tool`
registers the function beneath it as a tool. The docstring becomes the tool's
description, which is what the assistant reads to decide when to use it. The
type hint `name: str` tells the assistant what input to send.

Ask FastMCP to list what this server offers. This starts the server, asks it
for its tool list, and shuts it down:

```bash
fastmcp list hello.py
```

Now call the tool the way an assistant would, without any assistant involved:

```bash
fastmcp call hello.py greet name=Ada
```

Finally, look at what the assistant actually receives. This is the contract
your docstring and type hints produced:

```bash
fastmcp list hello.py --json
```

### What success looks like

`fastmcp list` shows one tool, `greet(name: str)`, with your docstring under
it. `fastmcp call` prints `"Hello, Ada! Welcome to MCP."`. The JSON output has
a `description` that matches your docstring and an `inputSchema` that requires
a string called `name`. You did not write any of that JSON. FastMCP built it
from your function.

If you get stuck, compare with `solutions/hello.py`.

---

## Lesson 2: Turn functions into tools

### What's going on

A tool is a function plus a contract. The **docstring** is the job
description: the assistant reads it to decide *whether* this tool fits the
question. The **type hints** are the form it fills out to call you. The
assistant never sees your code, only that contract, so a clear description
matters more than clever implementation.

Open `weather_server/server.py`. Three functions are already written and
working. They call Open-Meteo, a free weather API, and return readable text:

- `get_weather_forecast(location, days_ahead)` for up to 16 days out
- `get_historical_weather(location, date)` for any past date
- `calculate_rain_probability(location, date)` blends five years of history
  with the forecast

They are plain Python right now. Nothing about them is visible to an
assistant. The helper functions that start with an underscore are shared
plumbing and should stay private.

One design choice is worth naming. Open-Meteo has separate endpoints for
geocoding, forecasts, and history, and we could have exposed each as a tool
and let the assistant chain them. We didn't. `calculate_rain_probability`
makes six API calls and returns one answer, because "will it rain on my event
date" is the question people actually ask. Design tools top-down from the
outcome the user wants, not bottom-up from the endpoints you have. Every
extra call costs the assistant time and context, and every extra step is a
place to go wrong.

### Do it

Confirm the server currently offers nothing:

```bash
fastmcp list weather_server/server.py
```

In your editor, find the three lines that say `# TODO (Lesson 2)` and replace
each one with `@mcp.tool`, directly above the `def` line. Leave the helper
functions alone. Save the file.

List again. Three tools should appear, each with its docstring:

```bash
fastmcp list weather_server/server.py
```

Call one. This makes a real request to Open-Meteo:

```bash
fastmcp call weather_server/server.py get_weather_forecast location=Denver days_ahead=3
```

Now the interesting one. Pick a date a few days from today and ask for the rain
outlook. Use `YYYY-MM-DD` format:

```bash
fastmcp call weather_server/server.py calculate_rain_probability location=Seattle date=2026-09-30
```

Read one tool's schema and compare it with the function signature:

```bash
fastmcp list weather_server/server.py --json
```

Notice that `days_ahead` is *not* in the `required` list because it has a
default value. The assistant can leave it out and you get 7. That is the type
system doing your input validation for you.

### What success looks like

`fastmcp list` shows exactly three tools. The forecast call returns three dated
lines for Denver. The rain call returns a history line, a forecast line, and an
estimated percentage. If a call fails to find a location, try a simpler name:
the geocoder likes `Washington` better than `Washington, DC`.

---

## Lesson 3: Add resources and prompts

### What's going on

Tools *do* things. The other two primitives cover what tools don't.

A **resource** is something the assistant can *read*: reference material with
an address. A data dictionary, a policy document, a status page, a note about
where the data comes from and what it does not cover. Resources are addressed
with URIs like `weather://about`, the same idea as a URL but for your server.

A **prompt** is a saved instruction with blanks. Users end up asking the same
shape of question over and over: *should I keep this outdoor event on this
date?* A prompt captures that phrasing once so the assistant asks the right
tools the right way every time.

Rule of thumb: if the assistant needs to act or compute, write a tool. If it
needs background it should read, write a resource. If people keep asking the
same shaped question, write a prompt.

### Do it

In `weather_server/server.py`, find the line `# TODO (Lesson 3)` near the
bottom and replace it with this:

```python
@mcp.resource("weather://about")
def about() -> str:
    """Explain what this server does and where its data comes from."""
    return (
        "Weather Server answers forecast, history, and rain-probability questions. "
        "Data comes from Open-Meteo (open-meteo.com), a free and open weather API. "
        "Forecasts reach 16 days ahead; history covers roughly 80 years."
    )


@mcp.prompt
def plan_outdoor_event(location: str, date: str) -> str:
    """Ask the assistant to decide whether an outdoor event should keep its date."""
    return (
        f"I'm planning an outdoor event in {location} on {date}. "
        "Check the chance of rain and the forecast, then tell me plainly whether "
        "to keep the date or pick a backup, and why."
    )
```

The resource decorator takes the URI as its argument. The prompt decorator
works like the tool decorator: the function's parameters become the blanks.

List everything the server now offers:

```bash
fastmcp list weather_server/server.py --resources --prompts
```

Read the resource. Anything with `://` in it is treated as a resource URI:

```bash
fastmcp call weather_server/server.py weather://about
```

Render the prompt with its blanks filled in:

```bash
fastmcp call weather_server/server.py plan_outdoor_event --prompt location=Chicago date=2026-10-01
```

### What success looks like

The list shows three tools, one resource at `weather://about`, and one prompt
called `plan_outdoor_event(location, date)`. Reading the resource prints the
Open-Meteo sentence. The prompt comes back with Chicago and the date filled in.
An assistant connected to this server can now read where the data comes from,
and a user can pick "plan outdoor event" from a menu instead of typing the
whole question.

---

## Lesson 4: Test your server with code

### What's going on

You have been testing with the CLI, which is fine for a quick look but not
repeatable. Real projects need tests that run the same way every time.

FastMCP ships a `Client` that can connect to a server three ways: by URL, by
launching a file, or **in memory**, straight to the server object. In-memory
means no port, no subprocess, and tests that finish in well under a second. The
same `Client` class connects to your deployed URL later, so code you write
against it now keeps working after deployment.

Open `tests/test_server.py` and read it before running anything. Every test
follows the same shape: open a client on `mcp`, do one thing, assert one fact.
Tests that hit the live API are marked `integration` and skipped by default.

### Do it

Run the offline tests:

```bash
pytest
```

Run the live one too. It calls Open-Meteo for real:

```bash
pytest -m integration
```

Write the smallest client script yourself so the pattern sticks. Create
`check_client.py` in the repo root:

```python
import asyncio

from fastmcp import Client

from weather_server.server import mcp


async def main():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        print("Tools:", [tool.name for tool in tools])

        result = await client.call_tool(
            "get_weather_forecast", {"location": "Denver", "days_ahead": 2}
        )
        print(result.data)


asyncio.run(main())
```

```bash
python check_client.py
```

`result.data` is the Python value your function returned. If you ever need the
raw protocol response, it is on `result.content`.

Finally, see what a deployment platform sees when it loads your server. This is
the same check Prefect Horizon runs before it deploys:

```bash
fastmcp inspect weather_server/server.py:mcp
```

### What success looks like

`pytest` reports `6 passed, 1 deselected`. `pytest -m integration` reports
`1 passed`. Your client script prints the tool names and a two-day forecast.
`fastmcp inspect` shows 3 tools, 1 prompt, 1 resource, and FastMCP 4.x.

If a test fails, the message tells you which function is missing its
decorator or which piece from Lesson 3 is absent.

---

## Lesson 5: Deploy to Prefect Horizon

### What's going on

So far your server only exists where you run it. When the CLI or a desktop
client launches it, they talk over **stdio**: the client starts your program and
the two exchange messages through standard input and output, like a
conversation in the same room. That is fine for one person on one laptop.

To share the server with a team, or connect it from a hosted assistant, it
needs an address. Over **HTTP**, the server runs as a web service and clients
connect to a URL. Same code, different transport. You'll prove that locally
first, then let Horizon host it.

[Prefect Horizon](https://horizon.prefect.io) deploys FastMCP servers straight
from a GitHub repo. You point it at the repo, tell it which file holds the
server object, and it builds, hosts, and gives you a URL. Every push to `main`
redeploys. It also gives you two ways to try the server without configuring
any client: **ChatMCP**, an assistant preconnected to your server, and the
**Playground**, which lists tools and lets you call them by hand.

You need a GitHub account for this lesson.

### Do it

**Run over HTTP locally.** Start the server as a web service:

```bash
fastmcp run weather_server/server.py:mcp --transport http --port 8000
```

The `file.py:mcp` form names the exact server object. Leave this running and
open a second terminal, activate the virtual environment, and connect to it by
URL:

```bash
fastmcp list http://127.0.0.1:8000/mcp
```

Same three tools, reached over the network. Stop the server with `Ctrl+C`.

**Push to GitHub.** If this is a fresh clone, point it at your own repo. Create
an empty repository on GitHub called `fastmcp-101`, then:

```bash
git remote set-url origin https://github.com/YOUR_USERNAME/fastmcp-101.git
git add .
git commit -m "Complete FastMCP 101"
git push -u origin main
```

If you have the GitHub CLI, `gh repo create fastmcp-101 --public --source=. --remote=origin --push`
does the same in one line.

**Deploy on Horizon.**

1. Open [horizon.prefect.io](https://horizon.prefect.io) and sign in with GitHub.
2. Choose **Deploy a server** and pick your `fastmcp-101` repository. Grant
   access if GitHub asks.
3. Fill in the form:
   - **Server name**: something unique. This becomes your URL.
   - **Entrypoint**: `weather_server/server.py:mcp`
   - **Authentication**: leave it off for now so ChatMCP and other clients can
     connect without a login. You can turn it on later.
4. Click **Deploy Server**. Horizon clones the repo, installs from
   `pyproject.toml`, and starts the server. It usually takes under a minute.

Your server is now live at `https://<your-server-name>.fastmcp.app/mcp`.

**Talk to it.** Open your server in Horizon and choose **ChatMCP** from the left-hand menu. Ask:

- *What's the forecast for Denver this week?*
- *What was the weather in Chicago on July 4th, 2023?*
- *Should I keep an outdoor event in Seattle next Saturday?*

Watch which tool it picks for each question. That choice comes entirely from
your docstrings. Then choose **Playground** from the same menu to see the raw
tool list and call one with explicit arguments, no assistant in the loop.

**Connect a real client.** For Claude Code:

```bash
claude mcp add --transport http weather https://<your-server-name>.fastmcp.app/mcp
```

For Cursor or Claude Desktop, Horizon shows a copy-paste connection snippet on
your server's page.

### What success looks like

`fastmcp list` against `http://127.0.0.1:8000/mcp` shows your three tools.
Horizon shows the deployment as running. ChatMCP answers a weather question
using one of your tools, and you can tell which one from the response. After
`claude mcp add`, `claude mcp list` shows `weather` as connected.

---

## Where to go next

You built a server with all three MCP primitives, tested it in memory, and put
it on the internet. From here:

- **Point it at your own data.** Swap Open-Meteo for an API or database your
  team owns. The decorators don't change.
- **Turn on authentication** in Horizon so only your organization can connect.
- **Log from inside a tool.** Add a `ctx: Context` parameter and call
  `await ctx.info("...")` to send progress back to the client.
- **Read the docs.** [gofastmcp.com](https://gofastmcp.com) covers auth,
  middleware, background tasks, and interactive apps.
