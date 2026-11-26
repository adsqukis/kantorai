// @vitest-environment node
import { describe, expect, it } from "vitest";
import { applyAgentCollisionBumps } from "@/features/retro-office/systems/NavigationSystem";
import type { RenderAgent } from "@/features/retro-office/core/types";

const agent = (id: string, x: number, state: RenderAgent["state"]): RenderAgent => ({
  id, name: id, status: "idle", color: "#fff", item: "x",
  x, y: 100, targetX: x, targetY: 100, path: [], facing: 0, frame: 0, walkSpeed: 1, phaseOffset: 0, state,
});

describe("collision bumps and leisure poses", () => {
  it.each(["watching", "sleeping", "drinking"] as const)("does not bump agents that are %s", (state) => {
    const out = applyAgentCollisionBumps({ agents: [agent("a", 100, state), agent("b", 105, state)], now: 0 });
    expect(out[0].state).toBe(state);
    expect(out[1].state).toBe(state);
    expect(out[0].bumpedUntil).toBeUndefined();
  });

  it("still bumps standing agents that overlap", () => {
    const out = applyAgentCollisionBumps({ agents: [agent("a", 100, "standing"), agent("b", 105, "standing")], now: 0 });
    expect(out[0].bumpedUntil ?? out[1].bumpedUntil).toBeDefined();
  });
});
