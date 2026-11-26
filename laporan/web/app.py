import secrets
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .. import db
from ..config import Settings, load_sources
from ..timeutil import today_wib

AGENT_IDS = ["koordinator", "konten", "tiktok", "taqis", "keuangan", "analis"]
REPORTER_IDS = ["konten", "tiktok", "taqis", "keuangan"]
STATUS_LABEL = {"OK": "OK", "PERLU_DICEK": "PERLU DICEK", "GAGAL": "GAGAL"}


def agent_state(run) -> dict:
    agents = {a: "santai" for a in AGENT_IDS}
    if run and run.status == "BERJALAN":
        done = {r.source_id: r.status for r in run.reporters}
        agents["koordinator"] = "kerja"
        for sid in REPORTER_IDS:
            if sid in done:
                agents[sid] = "gagal" if done[sid] == "GAGAL" else "selesai"
            else:
                agents[sid] = "kerja"
        if all(sid in done for sid in REPORTER_IDS):
            agents["analis"] = "kerja"
    return {
        "run_date": run.run_date.isoformat() if run else None,
        "status": run.status if run else None,
        "agents": [{"id": a, "status": agents[a]} for a in AGENT_IDS],
    }


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(title="Laporan Pagi", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(
        SessionMiddleware, secret_key=settings.session_secret or secrets.token_hex(32),
        max_age=30 * 24 * 3600, same_site="lax", https_only=settings.cookie_secure,
    )
    templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
    conn = db.connect(settings.db_path)
    sources = {s.id: s for s in load_sources(settings)}

    def authed(req: Request) -> bool:
        return req.session.get("ok") is True

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request):
        return templates.TemplateResponse(request, "login.html", {"error": None})

    @app.post("/login")
    def login(request: Request, password: str = Form("")):
        if settings.dashboard_password and secrets.compare_digest(password, settings.dashboard_password):
            request.session["ok"] = True
            return RedirectResponse("/", status_code=303)
        return templates.TemplateResponse(request, "login.html", {"error": "Password salah."}, status_code=401)

    @app.post("/logout")
    def logout(request: Request):
        request.session.clear()
        return RedirectResponse("/login", status_code=303)

    def render(request: Request, run_date: date | None):
        if not authed(request):
            return RedirectResponse("/login", status_code=303)
        dates = db.list_run_dates(conn)
        run_date = run_date or (dates[0] if dates else None)
        run = db.load_run(conn, run_date) if run_date else None
        if run is None:
            return templates.TemplateResponse(
                request, "index.html", {"run": None, "dates": dates, "rows": [], "label": STATUS_LABEL},
                status_code=404 if run_date else 200,
            )
        by_id = {r.source_id: r for r in run.reporters}
        comps = {r.source_id: r.comparisons for r in db.load_raw(conn, run.run_date)}
        rows = []
        for sid in REPORTER_IDS:
            spec = sources.get(sid)
            changes = []
            for _key, paths in comps.get(sid, {}).items():
                changes.extend(paths.items())
            changes.sort(key=lambda kv: -abs(kv[1]))
            rows.append({"id": sid, "nama": spec.nama if spec else sid, "web": spec.web if spec else sid,
                         "res": by_id.get(sid), "changes": changes[:6]})
        return templates.TemplateResponse(
            request, "index.html", {"run": run, "dates": dates, "rows": rows, "label": STATUS_LABEL})

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        return render(request, None)

    @app.get("/laporan/{tanggal}", response_class=HTMLResponse)
    def by_date(request: Request, tanggal: date):
        return render(request, tanggal)

    @app.get("/api/state")
    def state(request: Request):
        if not authed(request):
            return JSONResponse({"error": "perlu login"}, status_code=401)
        dates = db.list_run_dates(conn, limit=1)
        today = today_wib()
        run = db.load_run(conn, today) or (db.load_run(conn, dates[0]) if dates else None)
        return agent_state(run)

    return app
