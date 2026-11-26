"use client";
// kantorai: polling status agent dari runtime laporan pagi.

import { useEffect, useState } from "react";
import { fetchCustomRuntimeJson } from "@/lib/runtime/custom/http";
import { mapKantorStatus, type KantorStatusMap } from "@/lib/kantor/statusFeed";

const EMPTY: KantorStatusMap = {};

export function useKantorStatusFeed(
  runtimeUrl: string | null,
  intervalMs = 10_000,
): KantorStatusMap {
  const [feed, setFeed] = useState<KantorStatusMap>({});
  useEffect(() => {
    if (!runtimeUrl) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const state = await fetchCustomRuntimeJson(runtimeUrl, "/state");
        if (!cancelled) setFeed(mapKantorStatus(state));
      } catch {
        // Runtime sedang mati: pertahankan status terakhir.
      }
    };
    void poll();
    const timer = window.setInterval(poll, intervalMs);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [runtimeUrl, intervalMs]);
  return runtimeUrl ? feed : EMPTY;
}
