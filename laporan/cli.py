import argparse
import asyncio
import json
import sys

from .config import Settings, load_servers
from .mcp_client import McpClient


def get_settings() -> Settings:
    return Settings()


async def _probe(settings: Settings, server: str | None, transport) -> int:
    servers = load_servers(settings)
    client = McpClient(servers, transport=transport)
    names = [server] if server else list(servers)
    code = 0
    for name in names:
        print(f"== {name} ({servers[name].url})")
        try:
            for t in await client.list_tools(name):
                schema = json.dumps(t.get("inputSchema") or {}, ensure_ascii=False)
                print(f"  - {t['name']}: {schema[:300]}")
        except Exception as e:  # tampilkan semua error koneksi/token dengan jelas
            print(f"  GAGAL: {e}")
            code = 1
    return code


def main(argv: list[str] | None = None, *, transport=None) -> int:
    p = argparse.ArgumentParser(prog="laporan")
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("probe", help="lihat daftar tool tiap server MCP")
    pr.add_argument("--server")
    args = p.parse_args(argv)
    settings = get_settings()
    if args.cmd == "probe":
        return asyncio.run(_probe(settings, args.server, transport))
    return 2


if __name__ == "__main__":
    sys.exit(main())
