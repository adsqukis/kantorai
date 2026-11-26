// kantorai: status kerja/santai agent dari runtime laporan pagi (GET /state → agent_status).

export type KantorOfficeStatus = "working" | "idle" | "error";
export type KantorStatusMap = Record<string, KantorOfficeStatus>;

const RUNTIME_TO_OFFICE: Record<string, KantorOfficeStatus> = {
  kerja: "working",
  selesai: "idle",
  santai: "idle",
  gagal: "error",
};

const KANTOR_ADAPTERS = new Set(["custom", "local", "claw3d"]);

export const isKantorRuntimeAdapter = (adapter: string | null | undefined): boolean =>
  Boolean(adapter && KANTOR_ADAPTERS.has(adapter));

export const mapKantorStatus = (state: unknown): KantorStatusMap => {
  if (!state || typeof state !== "object" || Array.isArray(state)) return {};
  const raw = (state as { agent_status?: unknown }).agent_status;
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return {};
  const out: KantorStatusMap = {};
  for (const [agentId, value] of Object.entries(raw as Record<string, unknown>)) {
    if (typeof value !== "string") continue;
    const mapped = RUNTIME_TO_OFFICE[value];
    if (mapped) out[agentId] = mapped;
  }
  return out;
};

/** Error dari Claw3D dan kerja karena sedang chat selalu menang; selebihnya status dari runtime laporan. */
export const applyKantorStatus = (
  base: KantorOfficeStatus,
  agentId: string,
  feed: KantorStatusMap,
): KantorOfficeStatus => {
  if (base === "error" || base === "working") return base;
  return feed[agentId] ?? base;
};
