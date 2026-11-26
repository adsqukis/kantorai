// @vitest-environment node
import { describe, expect, it } from "vitest";
import { ensureKantorLounge } from "@/features/retro-office/core/furnitureDefaults";
import { availableActivities } from "@/features/retro-office/core/leisure";
import type { FurnitureItem } from "@/features/retro-office/core/types";

const desk: FurnitureItem = { _uid: "d1", type: "desk_cubicle", x: 100, y: 100 };

describe("ensureKantorLounge", () => {
  it("adds a full lounge once: TV, couch, two beds, coffee machine", () => {
    const out = ensureKantorLounge([desk]);
    const types = out.map((i) => i.type).sort();
    expect(types).toEqual(["bed", "bed", "coffee_machine", "couch", "desk_cubicle", "tv"]);
    expect(availableActivities(out)).toEqual(["ngopi", "nonton", "tidur"]);
    expect(new Set(out.map((i) => i._uid)).size).toBe(out.length);
  });

  it("is idempotent", () => {
    const once = ensureKantorLounge([desk]);
    expect(ensureKantorLounge(once)).toBe(once);
  });

  it("keeps an existing coffee machine instead of adding another", () => {
    const cm: FurnitureItem = { _uid: "cm", type: "coffee_machine", x: 10, y: 10 };
    const out = ensureKantorLounge([desk, cm]);
    expect(out.filter((i) => i.type === "coffee_machine")).toHaveLength(1);
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
