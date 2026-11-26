// @vitest-environment node
import { describe, expect, it } from "vitest";
import {
  LEISURE_ROTATE_MS,
  availableActivities,
  buildLeisureOccupancy,
  pickLeisureActivity,
  resolveLeisureSpot,
} from "@/features/retro-office/core/leisure";
import type { FurnitureItem } from "@/features/retro-office/core/types";

const coffee: FurnitureItem = { _uid: "cm", type: "coffee_machine", x: 100, y: 100, w: 40, h: 40 };
const tv: FurnitureItem = { _uid: "tv", type: "tv", x: 400, y: 100, w: 80, h: 20, facing: 0 };
const couch: FurnitureItem = { _uid: "couch", type: "couch", x: 390, y: 220, w: 100, h: 40 };
const beanbag: FurnitureItem = { _uid: "bb", type: "beanbag", x: 520, y: 220, w: 40, h: 40 };
const farBeanbag: FurnitureItem = { _uid: "far", type: "beanbag", x: 1400, y: 900, w: 40, h: 40 };
const bed: FurnitureItem = { _uid: "bed", type: "bed", x: 700, y: 100, w: 50, h: 90 };
const ALL = [coffee, tv, couch, beanbag, bed];

describe("availableActivities", () => {
  it("lists only activities whose furniture exists", () => {
    expect(availableActivities(ALL)).toEqual(["ngopi", "nonton", "tidur"]);
    expect(availableActivities([coffee])).toEqual(["ngopi"]);
    expect(availableActivities([tv])).toEqual([]); // TV tanpa tempat duduk
    expect(availableActivities([tv, farBeanbag])).toEqual([]); // kursi terlalu jauh dari TV
    expect(availableActivities([])).toEqual([]);
  });
});

describe("pickLeisureActivity", () => {
  it("is deterministic and rotates every 20 minutes", () => {
    const a = pickLeisureActivity("tiktok", 0, ["ngopi", "nonton", "tidur"]);
    expect(pickLeisureActivity("tiktok", LEISURE_ROTATE_MS - 1, ["ngopi", "nonton", "tidur"])).toBe(a);
    const seen = new Set(
      [0, 1, 2].map((i) => pickLeisureActivity("tiktok", i * LEISURE_ROTATE_MS, ["ngopi", "nonton", "tidur"])),
    );
    expect(seen).toEqual(new Set(["ngopi", "nonton", "tidur"]));
  });

  it("skips activities without furniture and returns null when none", () => {
    for (let i = 0; i < 3; i++) {
      expect(pickLeisureActivity("konten", i * LEISURE_ROTATE_MS, ["tidur"])).toBe("tidur");
    }
    expect(pickLeisureActivity("konten", 0, [])).toBeNull();
  });
});

describe("resolveLeisureSpot", () => {
  it("ngopi stands in front of the coffee machine facing it", () => {
    const s = resolveLeisureSpot("ngopi", "a", ALL, new Map())!;
    expect(s.state).toBe("drinking");
    expect(s.uid).toBe("cm");
    expect(s.y).toBeGreaterThan(140);
    expect(Math.abs(s.x - 120)).toBeLessThanOrEqual(20);
    expect(s.facing).toBeCloseTo(Math.atan2(120 - s.x, 120 - s.y)); // menghadap ke tengah mesin
    expect(s.approachX).toBe(s.x);
  });

  it("nonton sits near the TV facing it, approaching from outside the seat", () => {
    const s = resolveLeisureSpot("nonton", "a", ALL, new Map())!;
    expect(s.state).toBe("watching");
    expect(["couch", "bb"]).toContain(s.uid);
    const dx = 440 - s.x;
    const dy = 110 - s.y;
    expect(Math.abs(s.facing - Math.atan2(dx, dy))).toBeLessThan(1e-9);
    expect(s.approachY).toBeLessThan(s.y); // mendekat dari sisi TV
  });

  it("tidur lies on the bed", () => {
    const s = resolveLeisureSpot("tidur", "a", ALL, new Map())!;
    expect(s.state).toBe("sleeping");
    expect(s.uid).toBe("bed");
    expect(s.x).toBeCloseTo(725);
    expect(s.y).toBeGreaterThan(145);
    expect(s.y).toBeLessThan(190);
    expect(s.facing).toBe(0);
  });

  it("respects capacity so agents never share one spot", () => {
    const occ = new Map([["bed", 1]]);
    expect(resolveLeisureSpot("tidur", "a", ALL, occ)).toBeNull();
    const first = resolveLeisureSpot("ngopi", "a", ALL, new Map())!;
    const second = resolveLeisureSpot("ngopi", "b", ALL, new Map([["cm", 1]]))!;
    expect(second.uid).toBe("cm");
    expect(second.x).not.toBe(first.x);
    expect(resolveLeisureSpot("ngopi", "c", ALL, new Map([["cm", 2]]))).toBeNull();
  });

  it("returns null when the furniture is missing", () => {
    expect(resolveLeisureSpot("tidur", "a", [coffee], new Map())).toBeNull();
  });
});

describe("buildLeisureOccupancy", () => {
  it("counts idle agents heading to or using furniture, excluding one agent", () => {
    const agents = [
      { id: "a", status: "idle" as const, leisureUid: "bed" },
      { id: "b", status: "idle" as const, leisureUid: "cm" },
      { id: "c", status: "working" as const, leisureUid: "cm" },
      { id: "d", status: "idle" as const },
    ];
    expect(buildLeisureOccupancy(agents, "a")).toEqual(new Map([["cm", 1]]));
    expect(buildLeisureOccupancy(agents, "z")).toEqual(new Map([["bed", 1], ["cm", 1]]));
  });
});

import { planLeisureStep } from "@/features/retro-office/core/leisure";

describe("planLeisureStep", () => {
  const path = [{ x: 1, y: 1 }];
  const base = { id: "konten", status: "idle" as const };
  const astarOk = () => path;
  const astarNone = () => [];

  it("does nothing for working agents (work beats leisure)", () => {
    const p = planLeisureStep({ agent: { ...base, status: "working" }, now: 0, furniture: ALL, occupancy: new Map(), x: 0, y: 0, astar: astarOk });
    expect(p.kind).toBe("none");
  });

  it("does nothing without leisure furniture (falls back to default idle behaviour)", () => {
    const p = planLeisureStep({ agent: base, now: 0, furniture: [], occupancy: new Map(), x: 0, y: 0, astar: astarOk });
    expect(p.kind).toBe("none");
  });

  it("waits after a blocked path", () => {
    const p = planLeisureStep({ agent: { ...base, leisureRetryAt: 5000 }, now: 1000, furniture: ALL, occupancy: new Map(), x: 0, y: 0, astar: astarOk });
    expect(p.kind).toBe("none");
  });

  it("walks there when far, arrives when close", () => {
    const far = planLeisureStep({ agent: base, now: 0, furniture: ALL, occupancy: new Map(), x: 0, y: 0, astar: astarOk });
    expect(far.kind).toBe("walk");
    if (far.kind !== "walk") throw new Error();
    expect(far.path).toBe(path);
    const near = planLeisureStep({ agent: base, now: 0, furniture: ALL, occupancy: new Map(), x: far.spot.approachX + 3, y: far.spot.approachY, astar: astarOk });
    expect(near.kind).toBe("arrive");
  });

  it("reports blocked when no route exists", () => {
    const p = planLeisureStep({ agent: base, now: 0, furniture: ALL, occupancy: new Map(), x: 0, y: 0, astar: astarNone });
    expect(p.kind).toBe("blocked");
  });

  it("tries another activity when the chosen one is full", () => {
    const full = new Map([["cm", 2], ["couch", 2], ["bb", 1]]);
    const p = planLeisureStep({ agent: base, now: 0, furniture: ALL, occupancy: full, x: 0, y: 0, astar: astarOk });
    expect(p.kind).toBe("walk");
    if (p.kind === "walk") expect(p.spot.state).toBe("sleeping");
    const allFull = new Map([...full, ["bed", 1]]);
    expect(planLeisureStep({ agent: base, now: 0, furniture: ALL, occupancy: allFull, x: 0, y: 0, astar: astarOk }).kind).toBe("none");
  });
});
