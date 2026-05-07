#!/usr/bin/env python3
"""MCP stdio server entry point."""
import sys
sys.path.insert(0, "apps/brain_qa")
from brain_qa.mcp_stdio_server import main
if __name__ == "__main__":
    main()
