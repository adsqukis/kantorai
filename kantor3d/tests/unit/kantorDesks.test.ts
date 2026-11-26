// @vitest-environment node
import { describe, expect, it } from "vitest";
import { autoAssignDeskIndexes } from "@/features/retro-office/core/kantorDesks";

describe("autoAssignDeskIndexes", () => {
  it("gives unassigned agents the first free desks, in agent order", () => {
    expect(autoAssignDeskIndexes(4, { b: 0 }, ["a", "b", "c"])).toEqual({ b: 0, a: 1, c: 2 });
  });

  it("keeps manual assignments and leaves extra agents without a desk", () => {
    expect(autoAssignDeskIndexes(2, { c: 1 }, ["a", "b", "c"])).toEqual({ c: 1, a: 0 });
  });

  it("ignores agents that are not in the office", () => {
    expect(autoAssignDeskIndexes(3, { ghost: 0 }, ["a"])).toEqual({ ghost: 0, a: 1 });
  });
});

describe("autoAssignDeskIndexes with unreachable desks", () => {
  it("skips desks agents cannot walk to", () => {
    expect(autoAssignDeskIndexes(4, {}, ["a", "b"], (i) => i !== 0)).toEqual({ a: 1, b: 2 });
  });
});
