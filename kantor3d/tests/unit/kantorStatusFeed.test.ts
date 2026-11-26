// @vitest-environment node
import { describe, expect, it } from "vitest";
import {
  applyKantorStatus,
  isKantorRuntimeAdapter,
  mapKantorStatus,
} from "@/lib/kantor/statusFeed";

describe("mapKantorStatus", () => {
  it("maps runtime statuses to office statuses", () => {
    expect(
      mapKantorStatus({
        agent_status: {
          koordinator: "kerja",
          konten: "selesai",
          tiktok: "gagal",
          analis: "santai",
        },
      }),
    ).toEqual({ koordinator: "working", konten: "idle", tiktok: "error", analis: "idle" });
  });

  it("returns an empty map for broken input", () => {
    expect(mapKantorStatus(null)).toEqual({});
    expect(mapKantorStatus("OK")).toEqual({});
    expect(mapKantorStatus({ agent_status: ["x"] })).toEqual({});
    expect(mapKantorStatus({ agent_status: { a: 5, b: "aneh" } })).toEqual({});
  });
});

describe("applyKantorStatus", () => {
  it("feed wins when it knows the agent", () => {
    expect(applyKantorStatus("idle", "tiktok", { tiktok: "working" })).toBe("working");
    expect(applyKantorStatus("working", "tiktok", { tiktok: "idle" })).toBe("working");
  });

  it("keeps working while the agent is chatting even if feed says idle", () => {
    expect(applyKantorStatus("working", "konten", { konten: "idle" })).toBe("working");
  });

  it("claw3d error always wins", () => {
    expect(applyKantorStatus("error", "konten", { konten: "working" })).toBe("error");
  });

  it("falls back to base status for unknown agents", () => {
    expect(applyKantorStatus("idle", "main", {})).toBe("idle");
  });
});

describe("isKantorRuntimeAdapter", () => {
  it("only direct http runtimes poll the feed", () => {
    expect(isKantorRuntimeAdapter("custom")).toBe(true);
    expect(isKantorRuntimeAdapter("local")).toBe(true);
    expect(isKantorRuntimeAdapter("openclaw")).toBe(false);
    expect(isKantorRuntimeAdapter(null)).toBe(false);
  });
});
