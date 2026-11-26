import argparse
import asyncio
import json
import logging
import sys
from datetime import date

from .config import Settings, load_brands, load_servers, load_sources
from .coordinator import run_day
from .db import connect
from .llm import LLM, make_client
from .fetch import fetch_source
from .timeutil import today_wib
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


async def _probe_try(settings: Settings, source_id: str, transport) -> int:
    spec = next((s for s in load_sources(settings) if s.id == source_id), None)
    if spec is None:
        print(f"Sumber '{source_id}' tidak ada di sources.yaml")
        return 1
    raw = await fetch_source(McpClient(load_servers(settings), transport=transport), spec, today_wib())
    for key, value in raw.items.items():
        top = list(value)[:8] if isinstance(value, dict) else type(value).__name__
        print(f"  OK    {key}: {len(json.dumps(value, ensure_ascii=False))} karakter, kunci {top}")
    for key, err in raw.errors.items():
        print(f"  GAGAL {key}: {err}")
    return 1 if raw.errors else 0


async def _run(settings: Settings, run_date: date, transport, llm) -> int:
    client = McpClient(load_servers(settings), transport=transport)
    llm = llm or LLM(make_client(settings.deepseek_api_key), settings.deepseek_model)
    out = await run_day(run_date, client=client, llm=llm, conn=connect(settings.db_path),
                        sources=load_sources(settings), brands=load_brands(settings))
    for r in out.reporters:
        print(f"  {r.source_id:9} {r.status:12} percobaan {r.attempts}  {r.error or ''}")
    print(f"Status run {run_date}: {out.status}")
    return 1 if out.status == "GAGAL" else 0


def main(argv: list[str] | None = None, *, transport=None, llm=None) -> int:
    p = argparse.ArgumentParser(prog="laporan")
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("probe", help="lihat daftar tool tiap server MCP")
    pr.add_argument("--server")
    pr.add_argument("--try", dest="try_source", metavar="SOURCE_ID")
    rn = sub.add_parser("run", help="jalankan laporan pagi")
    rn.add_argument("--date", help="YYYY-MM-DD (WIB); bawaan hari ini")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_settings()
    if args.cmd == "probe":
        if args.try_source:
            return asyncio.run(_probe_try(settings, args.try_source, transport))
        return asyncio.run(_probe(settings, args.server, transport))
    if args.cmd == "run":
        run_date = date.fromisoformat(args.date) if args.date else today_wib()
        return asyncio.run(_run(settings, run_date, transport, llm))
    return 2


if __name__ == "__main__":
    sys.exit(main())
