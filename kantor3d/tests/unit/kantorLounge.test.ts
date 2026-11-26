// @vitest-environment node
import { describe, expect, it } from "vitest";
import { ensureKantorLounge } from "@/features/retro-office/core/furnitureDefaults";
import { availableActivities } from "@/features/retro-office/core/leisure";
import type { FurnitureItem } from "@/features/retro-office/core/types";

const desk: FurnitureItem = { _uid: "d1", type: "desk_cubicle", x: 100, y: 100 };

describe("ensureKantorLounge", () => {
  it("adds a full lounge once: TV, couch, two beds, coffee corner", () => {
    const out = ensureKantorLounge([desk]);
    const types = out.map((i) => i.type).sort();
    expect(types).toEqual(["bed", "bed", "coffee_machine", "couch", "desk_cubicle", "table_rect", "tv"]);
    expect(availableActivities(out)).toEqual(["ngopi", "nonton", "tidur"]);
    expect(new Set(out.map((i) => i._uid)).size).toBe(out.length);
  });

  it("is idempotent", () => {
    const once = ensureKantorLounge([desk]);
    expect(ensureKantorLounge(once)).toBe(once);
  });

  it("brings its own coffee corner even when the kitchen has a machine (kitchens are often closed off)", () => {
    const cm: FurnitureItem = { _uid: "cm", type: "coffee_machine", x: 10, y: 10 };
    const out = ensureKantorLounge([desk, cm]);
    expect(out.filter((i) => i.type === "coffee_machine")).toHaveLength(2);
    const lounge = out.find((i) => i.type === "coffee_machine" && i._uid !== "cm")!;
    expect(lounge.elevation).toBeGreaterThan(0); // di atas meja
  });

  it("does not touch a layout that already has a TV", () => {
    const tv: FurnitureItem = { _uid: "tv", type: "tv", x: 0, y: 0 };
    const layout = [desk, tv];
    expect(ensureKantorLounge(layout)).toBe(layout);
  });
});

import {
  ensureOfficeAtm,
  ensureOfficeGymRoom,
  ensureOfficeJukebox,
  ensureOfficeKanbanBoard,
  ensureOfficePhoneBooth,
  ensureOfficePingPongTable,
  ensureOfficeQaLab,
  ensureOfficeServerRoom,
  ensureOfficeSmsBooth,
  materializeDefaults,
} from "@/features/retro-office/core/furnitureDefaults";
import { getItemBounds } from "@/features/retro-office/core/geometry";

describe("default lounge placement", () => {
  it("does not overlap the default office furniture", () => {
    const steps = [
      ensureOfficePingPongTable, ensureOfficeAtm, ensureOfficeSmsBooth, ensureOfficePhoneBooth,
      ensureOfficeServerRoom, ensureOfficeGymRoom, ensureOfficeQaLab, ensureOfficeJukebox, ensureOfficeKanbanBoard,
    ];
    const base = steps.reduce((items, step) => step(items), materializeDefaults("default" as never));
    const out = ensureKantorLounge(base);
    const added = out.slice(base.length);
    const overlaps = (a: FurnitureItem, b: FurnitureItem) => {
      const A = getItemBounds(a);
      const B = getItemBounds(b);
      return A.x < B.x + B.w && B.x < A.x + A.w && A.y < B.y + B.h && B.y < A.y + A.h;
    };
    for (const item of added) {
      const hit = base.find((b) => overlaps(item, b));
      expect(hit, `${item.type} menabrak ${hit?.type}`).toBeUndefined();
    }
  });
});

import { astar, buildNavGrid, getDeskLocations } from "@/features/retro-office/core/navigation";
import { planLeisureStep, resolveLeisureSpot } from "@/features/retro-office/core/leisure";

describe("leaving the lounge for work", () => {
  it("every lounge spot has a route to a desk and back", () => {
    const steps = [
      ensureOfficePingPongTable, ensureOfficeAtm, ensureOfficeSmsBooth, ensureOfficePhoneBooth,
      ensureOfficeServerRoom, ensureOfficeGymRoom, ensureOfficeQaLab, ensureOfficeJukebox, ensureOfficeKanbanBoard,
    ];
    const layout = ensureKantorLounge(steps.reduce((items, step) => step(items), materializeDefaults("default" as never)));
    const grid = buildNavGrid(layout);
    const desk = getDeskLocations(layout).find((d) => astar(d.x, d.y, 640, 217, grid).length > 0)!;
    const route = (fx: number, fy: number, tx: number, ty: number) => astar(fx, fy, tx, ty, grid);
    const seen = new Set<string>();
    // Satu agent per kegiatan; furnitur lain dianggap penuh supaya tiap kegiatan diuji.
    for (const [act, full] of [
      ["ngopi", ["tv", "bed"]],
      ["nonton", ["cm", "bed"]],
      ["tidur", ["cm", "tv"]],
    ] as const) {
      const occupancy = new Map<string, string[]>();
      for (const f of layout) {
        const blocked = (full as readonly string[]).includes(f.type === "coffee_machine" ? "cm" : f.type === "bed" ? "bed" : ["couch", "couch_v", "beanbag"].includes(f.type) ? "tv" : "");
        if (blocked) occupancy.set(f._uid, ["x", "y", "z"]);
      }
      const plan = planLeisureStep({ agent: { id: "konten", status: "idle" }, now: 0, furniture: layout, occupancy, x: desk.x, y: desk.y, astar: route });
      expect(plan.kind, act).toBe("walk");
      if (plan.kind !== "walk") continue;
      seen.add(plan.spot.state);
      expect(route(plan.spot.x, plan.spot.y, desk.x, desk.y).length, `${act} → meja`).toBeGreaterThan(0);
    }
    expect(seen).toEqual(new Set(["drinking", "watching", "sleeping"]));
  });
});
