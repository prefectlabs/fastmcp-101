"""Lesson 1: the smallest useful MCP server."""

from fastmcp import FastMCP

mcp = FastMCP("Hello Server")


@mcp.tool
def greet(name: str) -> str:
    """Say hello to someone by name."""
    return f"Hello, {name}! Welcome to MCP."


if __name__ == "__main__":
    mcp.run()
