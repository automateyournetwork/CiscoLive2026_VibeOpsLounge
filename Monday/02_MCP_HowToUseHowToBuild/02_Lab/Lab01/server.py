#!/usr/bin/env python3
import logging
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("MultiplyFastMCPServer")

load_dotenv()

mcp = FastMCP("Math Tools MCP")

@mcp.tool(name="multiply", description="Multiply two numbers and return the product.")
def multiply(a: float, b: float) -> dict:
    logger.info("🚀 multiply called with a=%s, b=%s", a, b)
    product = a * b
    return {
        "a": a,
        "b": b,
        "product": product,
        "summary": f"{a} × {b} = {product}",
    }

if __name__ == "__main__":
    logger.info("Starting Math Tools MCP (stdio)")
    mcp.run(transport="stdio")
