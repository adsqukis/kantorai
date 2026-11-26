// @vitest-environment node
import { describe, expect, it } from "vitest";
import {
  KANTOR_FURNITURE_TYPES,
  KANTOR_PALETTE_ENTRIES,
} from "@/features/retro-office/core/kantorFurniture";
import { ITEM_FOOTPRINT, ITEM_METADATA, getItemBaseSize } from "@/features/retro-office/core/geometry";

describe("kantor furniture", () => {
  it("adds a TV and a bed to the builder palette", () => {
    expect(KANTOR_FURNITURE_TYPES).toEqual(["tv", "bed"]);
    const byType = Object.fromEntries(KANTOR_PALETTE_ENTRIES.map((e) => [e.type, e]));
    expect(byType.tv.label).toBe("TV");
    expect(byType.bed.label).toBe("Kasur");
  });

  it("gives both a footprint", () => {
    expect(ITEM_FOOTPRINT.tv).toEqual([80, 20]);
    expect(ITEM_FOOTPRINT.bed).toEqual([50, 90]);
    expect(getItemBaseSize({ _uid: "b", type: "bed", x: 0, y: 0 })).toEqual({ width: 50, height: 90 });
  });

  it("TV blocks walking; agents can lie on the bed", () => {
    expect(ITEM_METADATA.tv.blocksNavigation).toBe(true);
    expect(ITEM_METADATA.bed.blocksNavigation).toBe(false);
  });
});
