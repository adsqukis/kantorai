# Kantor 3D (Claw3D) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kantor 3D berbasis fork Claw3D tempat 6 agent laporan pagi terlihat bekerja di meja saat ada kerjaan, dan saat santai pergi ngopi, nonton TV, atau tidur di kasur.

**Architecture:** Sistem Python (rencana A) menyediakan *custom runtime* Claw3D di `127.0.0.1:8081` (`/health`, `/state`, `/registry`, `/v1/chat/completions`). `/state.active` membuat 6 agent muncul; `/state.agent_status` dibaca fork lewat *status feed* untuk mengisi status kerja/santai. Fork menambah furnitur prosedural TV & kasur, sistem santai deterministik (ngopi/nonton/tidur), pose baru, dan tata ruang pojok santai bawaan.

**Tech Stack:** Python/FastAPI (runtime), fork Claw3D di `kantor3d/` (Next.js 16, React 19, react-three-fiber, Vitest).

**Spec:** `docs/superpowers/specs/2026-11-26-tim-agent-laporan-harian-design.md` (§6.6b). Keputusan pemilik 26 Nov: **versi 2** (lengkap: TV, kasur, pose tidur, Zzz).

## Global Constraints

- Lisensi Claw3D MIT: `kantor3d/LICENSE` tetap; tambah `kantor3d/NOTICE.md` yang menyebut fork + perubahan.
- Agent id tetap: `koordinator`, `konten`, `tiktok`, `taqis`, `keuangan`, `analis`.
- Status runtime → office: `kerja` → `working`; `gagal` → `error`; `selesai`/`santai` → `idle`.
- Kegiatan santai: `ngopi` (mesin kopi, berdiri + cangkir), `nonton` (sofa/beanbag menghadap TV, duduk), `tidur` (kasur, berbaring + "Zzz"). Bergiliran per agent tiap 20 menit.
- Runtime hanya listen di `127.0.0.1`; tidak pernah di-expose langsung. Kantor 3D di internet wajib `STUDIO_ACCESS_TOKEN`.
- Chat dengan agent hanya membaca laporan; tidak memanggil tool MCP apa pun.
- Perubahan di fork dibuat di file baru sebisa mungkin; sentuhan ke `RetroOffice3D.tsx`/`agents.tsx`/`OfficeScreen.tsx` sekecil mungkin dan ditandai komentar `// kantorai:`.

## Review Focus

1. **Tidak ada furnitur santai di layout** (pengguna menghapus TV/kasur) → agent kembali ke perilaku santai bawaan Claw3D, tidak macet. Test di Task 4.
2. **Lebih banyak agent daripada kursi/kasur** → dua agent tidak menempati titik yang sama; yang tidak kebagian memilih kegiatan lain atau perilaku bawaan. Test di Task 4.
3. **Runtime mati / `/state` gagal** → status feed mempertahankan status terakhir dan tidak melempar error ke UI. Test di Task 2.
4. **Agent dipanggil kerja saat sedang tidur** → bangun dan berjalan ke meja (status working mengalahkan kegiatan santai). Test di Task 4.
5. **Chat dengan agent saat belum ada laporan** → jawaban sopan "belum ada laporan hari ini", bukan error 500. Test di Task 1.

---

### Task 1: Custom runtime di sistem laporan

**Files:** Create `laporan/runtime.py`, `deploy/laporan-runtime.service`; Modify `laporan/cli.py` (sub-perintah `runtime --port 8081`); Test `tests/test_runtime.py`.

**Interfaces:**
- Consumes: `db.load_run`, `db.list_run_dates`, `agent_state(run)` dari `laporan/web/app.py`, `LLM`.
- Produces: `create_runtime_app(settings, llm=None) -> FastAPI`:
  - `GET /health` → `{"ok": true, "status": "ok"}`
  - `GET /state` → `{"runtime": {"name": "Kantor Qukis", "vendor": "kantorai", "status": "ok", "active_model": <model>}, "active": {<6 id>: <model>}, "agent_status": {<id>: "kerja"|"selesai"|"gagal"|"santai"}, "run_date": ..., "run_status": ...}`
  - `GET /registry` → `{"models": {<model>: {"provider": "deepseek"}}}`
  - `POST /v1/chat/completions` body `{role, messages:[{role,content}]}` → OpenAI-shape `{"choices":[{"message":{"role":"assistant","content": str}}]}`. Persona per `role` (id agent). Konteks = ringkasan + laporan run terbaru (JSON). Tanpa laporan → jawaban tetap "Belum ada laporan hari ini…" tanpa memanggil LLM. `role` tak dikenal → 400.
  - `LLM.chat(system: str, messages: list[dict]) -> str` ditambahkan ke `laporan/llm.py` (teks bebas, `temperature=0.4`, `max_tokens=1200`).

- [ ] Step 1: tests — `test_state_lists_six_agents`, `test_state_agent_status_matches_api_state`, `test_registry_has_model`, `test_chat_uses_persona_and_report_context`, `test_chat_without_report_is_polite`, `test_chat_unknown_role_400`, `test_runtime_cli_binds_localhost`.
- [ ] Step 2: run → FAIL. Step 3: implement. Step 4: run → PASS (seluruh suite). Step 5: commit `feat: custom runtime untuk kantor 3D`.

### Task 2: Fork — salin Claw3D + status feed

**Files:** Create `kantor3d/NOTICE.md`, `kantor3d/src/lib/kantor/statusFeed.ts`, `kantor3d/src/lib/kantor/useKantorStatusFeed.ts`; Modify `kantor3d/src/features/office/screens/OfficeScreen.tsx` (`mapAgentToOffice` menerima override); Test `kantor3d/tests/unit/kantorStatusFeed.test.ts`.

**Interfaces:**
- `mapKantorStatus(state: unknown): Record<string, "working" | "idle" | "error">` — dari `state.agent_status`; input rusak → `{}`.
- `applyKantorStatus(base: OfficeAgent["status"], agentId: string, feed: Record<string, ...>): OfficeAgent["status"]` — feed menang bila ada id; `error` dari runtime Claw3D tetap menang.
- `useKantorStatusFeed(runtimeUrl: string | null, intervalMs = 10000)` — polling `/state` via `fetchCustomRuntimeJson`; error → simpan map terakhir.

- [ ] Steps: test pure functions (status mapping, input rusak, error menang, fallback) → FAIL → implement → PASS (`npx vitest run tests/unit/kantorStatusFeed.test.ts`) → `npm run typecheck` tidak menambah error baru → commit `feat(kantor3d): status feed dari runtime laporan`.

### Task 3: Fork — furnitur TV & kasur

**Files:** Create `kantor3d/src/features/retro-office/objects/Leisure.tsx` (`TvModel`, `BedModel`, prosedural seperti `Jukebox.tsx`); Modify `RetroOffice3D.tsx` (palet + dispatch render), `core/geometry.ts` bila ukuran dasar perlu; Test `kantor3d/tests/unit/kantorFurniture.test.ts`.

**Interfaces:** palet builder berisi `{ type: "tv", label: "TV", defaults: { w: 80, h: 20, facing: 0 } }` dan `{ type: "bed", label: "Kasur", defaults: { w: 50, h: 90 } }`; ekspor `KANTOR_FURNITURE_TYPES = ["tv","bed"]`. TV: layar berpendar berganti warna pelan. Kasur: rangka kayu, kasur, bantal.

- [ ] Steps: test palet memuat `tv`/`bed` dan ukurannya → FAIL → implement → PASS → commit.

### Task 4: Fork — sistem santai + pose

**Files:** Create `kantor3d/src/features/retro-office/core/leisure.ts`; Modify `core/types.ts` (state `"drinking" | "watching" | "sleeping"`, field `leisureUid?: string`), `RetroOffice3D.tsx` (cabang agent idle di `tick`), `objects/agents.tsx` (pose + Zzz + cangkir); Test `kantor3d/tests/unit/kantorLeisure.test.ts`.

**Interfaces:**
- `type LeisureActivity = "ngopi" | "nonton" | "tidur"`
- `pickLeisureActivity(agentId: string, now: number, available: LeisureActivity[]): LeisureActivity | null` — rotasi deterministik: indeks = (hash(agentId) + floor(now / 20 menit)) mod 3, lewati yang tidak tersedia.
- `resolveLeisureSpot(activity, agentId, furniture: FurnitureItem[], occupied: Set<string>): { x: number; y: number; facing: number; state: "drinking"|"watching"|"sleeping"; uid: string } | null` — ngopi: sel depan `coffee_machine`; nonton: `couch`/`couch_v`/`beanbag` dalam radius 400 dari `tv`, menghadap TV; tidur: `bed`. `occupied` berisi `uid` furnitur yang sudah dipakai (kasur/beanbag 1 orang, sofa 2, mesin kopi 2).
- `availableActivities(furniture)` → kegiatan yang furniturnya ada.
- Integrasi `tick`: agent `status === "idle"`, bukan remote/janitor, path kosong → hitung spot; jauh → jalan (astar), dekat → set state + facing. Bila tidak ada spot atau astar kosong → perilaku bawaan (dengan jeda 60 dtk sebelum mencoba lagi). Status `working` memakai jalur meja bawaan (mengalahkan santai).

- [ ] Steps: tests (rotasi deterministik, lewati kegiatan tanpa furnitur, tidak ada furnitur → null, occupied mencegah tabrakan, TV menentukan arah hadap, prioritas kerja) → FAIL → implement → PASS → typecheck → commit.

### Task 5: Fork — tata ruang pojok santai bawaan

**Files:** Modify `core/furnitureDefaults.ts` (`ensureKantorLounge(items)` seperti `ensureOfficeJukebox`), titik panggil yang sama dengan `ensureOfficeJukebox`; Test `kantor3d/tests/unit/kantorLounge.test.ts`.

**Interfaces:** `ensureKantorLounge(items: FurnitureItem[]): FurnitureItem[]` — bila belum ada `tv`, tambahkan satu set: TV, 2 sofa/beanbag menghadap TV, 2 kasur, 1 mesin kopi (bila belum ada) di area kosong; idempoten.

- [ ] Steps: test (menambah set lengkap sekali, idempoten, tidak menimpa layout yang sudah punya TV) → FAIL → implement → PASS → commit.

### Task 6: Cek visual menyeluruh

- [ ] Jalankan `laporan runtime` dengan DB contoh (satu run BERJALAN sebagian) + `kantor3d` dev server dengan profil `custom` → Playwright screenshot kantor: agent kerja di meja, sisanya di pojok santai (ngopi/nonton/tidur). Perbaiki yang tampak salah (satu putaran).
- [ ] `npx vitest run` untuk test baru, `npm run typecheck`, `npm run build` — tidak ada error baru dibanding sebelum fork (catat error bawaan di ledger).

### Task 7: Deploy kantor 3D

**Files:** Create `deploy/kantor3d.service`, `deploy/laporan-runtime.service`; Modify `deploy/Caddyfile` (situs kedua `{$KANTOR_DOMAIN}` → `127.0.0.1:3000`), `deploy/RUNBOOK.md` (instal Node 22, `npm ci && npm run build`, `.env` kantor3d: `HOST=127.0.0.1`, `PORT=3000`, `STUDIO_ACCESS_TOKEN`, profil runtime `custom` → `http://127.0.0.1:8081`).

- [ ] Verifikasi: `systemd-analyze verify` tanpa error sintaks; RUNBOOK mencakup langkah dari nol; commit.
