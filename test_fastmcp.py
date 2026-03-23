try:
    from mcp.server.fastapi import create_mcp_server
    print("create_mcp_server exists!")
except ImportError:
    print("no create_mcp_server")
