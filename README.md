# FastMCP 101

Build, test, and deploy your first MCP server in Python. No prior MCP experience needed.

The Model Context Protocol (MCP) is the shared standard that lets AI assistants
use outside systems: your data, your APIs, your expertise. You build a **server**
that offers capabilities; any MCP **client** (Claude, ChatGPT, Cursor, an agency
chatbot) can then use them. Think of it as the wall outlet between assistants and
the systems you own. The utility doesn't care what you plug in.

[FastMCP](https://gofastmcp.com) is the Python framework that makes a server out
of ordinary functions. One decorator per function. This repo pins **FastMCP 4**.

## What you'll build

A weather server with three tools, one resource, and one prompt, backed by
[Open-Meteo](https://open-meteo.com) (free, no API key). By the end you will
have run it locally, tested it in memory, and deployed it to a public URL on
[Prefect Horizon](https://horizon.prefect.io).

| Lesson | You will | Time |
|---|---|---|
| 1. Build your first MCP server | Write a one-tool server and call it from the CLI | 10 min |
| 2. Turn functions into tools | Decorate three weather functions and read the schema the AI sees | 15 min |
| 3. Add resources and prompts | Give the assistant something to read and a saved recipe | 10 min |
| 4. Test your server with code | Use the in-memory client and run the test suite | 10 min |
| 5. Deploy to Prefect Horizon | Run over HTTP, push to GitHub, deploy, chat with it | 20 min |

The lessons live in [WORKSHOP.md](WORKSHOP.md). Follow them in order.

Prefer a browser sandbox with nothing to install? The same course runs on
Instruqt: [FastMCP Foundations](https://play.instruqt.com/prefect/tracks/fastmcp-foundations).

## Prerequisites

- Python 3.10 or newer (3.12 recommended)
- Git
- A GitHub account (Lesson 5 only)
- Any editor. VS Code, Cursor, and PyCharm all work.

## Setup

Clone the repo, then pick **one** of the two install paths.

```bash
git clone https://github.com/prefectlabs/fastmcp-101.git
cd fastmcp-101
```

**Option A: uv** (fastest, and what the lessons assume)

```bash
# Install uv once if you don't have it: https://docs.astral.sh/uv/
uv sync
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

**Option B: plain venv and pip**

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Confirm it worked:

```bash
fastmcp version
```

You should see `FastMCP version: 4.x`. Now open [WORKSHOP.md](WORKSHOP.md) and
start Lesson 1.

## Repo layout

```text
fastmcp-101/
├── weather_server/
│   └── server.py        # the starter: three functions waiting for @mcp.tool
├── solutions/
│   ├── hello.py         # Lesson 1 answer
│   └── server.py        # finished server: tools, resource, prompt
├── tests/
│   └── test_server.py   # in-memory tests you run in Lesson 4
├── WORKSHOP.md          # the five lessons
├── pyproject.toml       # dependencies (FastMCP 4, requests, pytest)
└── requirements.txt     # same dependencies for plain pip
```

The starter server intentionally fails its tests until you finish Lessons 2
and 3. If you get stuck, diff your file against `solutions/server.py`.

## Handy commands

```bash
fastmcp list weather_server/server.py --resources --prompts   # what the AI sees
fastmcp call weather_server/server.py get_weather_forecast location=Denver days_ahead=3
fastmcp inspect weather_server/server.py:mcp                  # summary a deploy platform sees
pytest                                                        # offline tests
pytest -m integration                                         # also hit the live API
fastmcp run weather_server/server.py:mcp --transport http --port 8000   # serve over HTTP
```

## Deploying

Lesson 5 walks through it. The short version: push this repo to your own
GitHub, sign in at [horizon.prefect.io](https://horizon.prefect.io), pick the
repo, set the entrypoint to `weather_server/server.py:mcp`, and click Deploy.
Your server gets a URL like `https://<your-server-name>.fastmcp.app/mcp` and
redeploys on every push to `main`.

## Connecting a client

Once deployed, any MCP client can use your server. For Claude Code:

```bash
claude mcp add --transport http weather https://<your-server-name>.fastmcp.app/mcp
```

For Cursor, Claude Desktop, and others, Horizon shows a copy-paste connection
snippet on your server's page.

## Going further

- [FastMCP docs](https://gofastmcp.com) for everything past 101: auth, middleware, background tasks, interactive apps
- [MCP specification](https://modelcontextprotocol.io)
- [Deploying to Prefect Horizon](https://gofastmcp.com/deployment/prefect-horizon)

## License

Apache 2.0. See [LICENSE](LICENSE).
