// kantorai: sistem santai — agent yang tidak bekerja pergi ngopi, nonton TV, atau tidur.
// Semua fungsi di sini murni (tanpa React/Three) supaya mudah diuji.

import {
  getItemBaseSize,
  getItemRotationRadians,
} from "@/features/retro-office/core/geometry";
import type { FurnitureItem } from "@/features/retro-office/core/types";

export type LeisureActivity = "ngopi" | "nonton" | "tidur";
export type LeisureState = "drinking" | "watching" | "sleeping";

export const LEISURE_ROTATE_MS = 20 * 60 * 1000;
export const LEISURE_RETRY_MS = 60 * 1000;
const ORDER: LeisureActivity[] = ["ngopi", "nonton", "tidur"];
const TV_RADIUS = 400;
const SEAT_TYPES = ["couch", "couch_v", "beanbag"];
const CAPACITY: Record<string, number> = {
  coffee_machine: 2,
  couch: 2,
  couch_v: 1,
  beanbag: 1,
  bed: 1,
};
const BODY_LENGTH = 55; // panjang badan agent berbaring, satuan kanvas

export type LeisureSpot = {
  x: number;
  y: number;
  approachX: number;
  approachY: number;
  facing: number;
  state: LeisureState;
  uid: string;
};

const center = (item: FurnitureItem) => {
  const { width, height } = getItemBaseSize(item);
  return { cx: item.x + width / 2, cy: item.y + height / 2, width, height };
};

/** Putar offset lokal (lx, lz) sesuai rotasi furnitur — sama dengan rotation.y di three.js. */
const rotate = (lx: number, lz: number, theta: number) => ({
  x: lx * Math.cos(theta) + lz * Math.sin(theta),
  y: -lx * Math.sin(theta) + lz * Math.cos(theta),
});

const hash = (s: string) => {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
};

const seatsNearTv = (furniture: FurnitureItem[]) => {
  const tvs = furniture.filter((f) => f.type === "tv");
  const out: Array<{ seat: FurnitureItem; tv: FurnitureItem; dist: number }> =
    [];
  for (const seat of furniture.filter((f) => SEAT_TYPES.includes(f.type))) {
    const s = center(seat);
    let best: { tv: FurnitureItem; dist: number } | null = null;
    for (const tv of tvs) {
      const t = center(tv);
      const dist = Math.hypot(t.cx - s.cx, t.cy - s.cy);
      if (dist <= TV_RADIUS && (!best || dist < best.dist)) best = { tv, dist };
    }
    if (best) out.push({ seat, ...best });
  }
  return out.sort((a, b) => a.dist - b.dist);
};

export const availableActivities = (
  furniture: FurnitureItem[],
): LeisureActivity[] => {
  const out: LeisureActivity[] = [];
  if (furniture.some((f) => f.type === "coffee_machine")) out.push("ngopi");
  if (seatsNearTv(furniture).length > 0) out.push("nonton");
  if (furniture.some((f) => f.type === "bed")) out.push("tidur");
  return out;
};

export const pickLeisureActivity = (
  agentId: string,
  now: number,
  available: LeisureActivity[],
): LeisureActivity | null => {
  const start =
    (hash(agentId) + Math.floor(now / LEISURE_ROTATE_MS)) % ORDER.length;
  for (let i = 0; i < ORDER.length; i++) {
    const a = ORDER[(start + i) % ORDER.length];
    if (available.includes(a)) return a;
  }
  return null;
};

/** occupied: uid furnitur → id agent LAIN yang memakainya. */
export type LeisureOccupancy = Map<string, string[]>;

const free = (item: FurnitureItem, occupied: LeisureOccupancy) =>
  (occupied.get(item._uid)?.length ?? 0) < (CAPACITY[item.type] ?? 1);

/** Slot stabil: urutan id agent di antara pemakai furnitur yang sama. */
const slotOf = (
  item: FurnitureItem,
  agentId: string,
  occupied: LeisureOccupancy,
) => (occupied.get(item._uid) ?? []).filter((other) => other < agentId).length;

/** Semua kandidat tempat untuk satu kegiatan, urut dari yang paling diutamakan. */
export const resolveLeisureSpots = (
  activity: LeisureActivity,
  agentId: string,
  furniture: FurnitureItem[],
  occupied: LeisureOccupancy,
): LeisureSpot[] => {
  if (activity === "ngopi") {
    const out: LeisureSpot[] = [];
    for (const machine of furniture.filter(
      (f) => f.type === "coffee_machine" && free(f, occupied),
    )) {
      const { cx, cy, width, height } = center(machine);
      const slot = slotOf(machine, agentId, occupied);
      const side = slot === 0 ? -12 : 12;
      const theta = getItemRotationRadians(machine);
      // Depan dulu, lalu kiri, kanan, belakang — mesin sering menempel ke counter atau tembok.
      const sides: Array<[number, number]> = [
        [side, height / 2 + 18],
        [-(width / 2 + 18), side],
        [width / 2 + 18, side],
        [side, -(height / 2 + 18)],
      ];
      for (const [lx, lz] of sides) {
        const off = rotate(lx, lz, theta);
        const x = cx + off.x;
        const y = cy + off.y;
        out.push({
          x,
          y,
          approachX: x,
          approachY: y,
          facing: Math.atan2(cx - x, cy - y),
          state: "drinking",
          uid: machine._uid,
        });
      }
    }
    return out;
  }
  if (activity === "nonton") {
    const out: LeisureSpot[] = [];
    for (const { seat, tv } of seatsNearTv(furniture).filter(({ seat }) =>
      free(seat, occupied),
    )) {
      const s = center(seat);
      const t = center(tv);
      const slot = slotOf(seat, agentId, occupied);
      const along =
        seat.type === "couch" ? (slot === 0 ? -s.width / 6 : s.width / 6) : 0;
      const off = rotate(along, 0, getItemRotationRadians(seat));
      const x = s.cx + off.x;
      const y = s.cy + off.y;
      const dist = Math.hypot(t.cx - x, t.cy - y) || 1;
      const reach = Math.min(s.width, s.height) / 2 + 20;
      out.push({
        x,
        y,
        approachX: x + ((t.cx - x) / dist) * reach,
        approachY: y + ((t.cy - y) / dist) * reach,
        facing: Math.atan2(t.cx - x, t.cy - y),
        state: "watching",
        uid: seat._uid,
      });
    }
    return out;
  }
  return furniture
    .filter((f) => f.type === "bed" && free(f, occupied))
    .map((bed) => {
      const { cx, cy, height } = center(bed);
      const theta = getItemRotationRadians(bed);
      // Titik asal agent = kaki; kepala mengarah ke sandaran (sisi -z lokal).
      const feet = rotate(
        0,
        Math.min(height / 2 - 12, BODY_LENGTH - 25),
        theta,
      );
      const x = cx + feet.x;
      const y = cy + feet.y;
      return {
        x,
        y,
        approachX: x,
        approachY: y,
        facing: theta,
        state: "sleeping" as const,
        uid: bed._uid,
      };
    });
};

/** Kandidat utama (untuk tampilan/uji); null bila tidak ada tempat. */
export const resolveLeisureSpot = (
  activity: LeisureActivity,
  agentId: string,
  furniture: FurnitureItem[],
  occupied: LeisureOccupancy,
): LeisureSpot | null =>
  resolveLeisureSpots(activity, agentId, furniture, occupied)[0] ?? null;

/** Kelompokkan klaim agent lain per furnitur (agentId → uid furnitur). */
export const groupLeisureClaims = (
  claims: Map<string, string>,
  excludeId: string,
): LeisureOccupancy => {
  const out: LeisureOccupancy = new Map();
  for (const [agentId, uid] of claims) {
    if (agentId === excludeId) continue;
    out.set(uid, [...(out.get(uid) ?? []), agentId]);
  }
  return out;
};

export type LeisurePlan =
  | { kind: "none" }
  | { kind: "blocked" }
  | { kind: "arrive"; spot: LeisureSpot }
  | { kind: "walk"; spot: LeisureSpot; path: Array<{ x: number; y: number }> };

const ARRIVE_DISTANCE = 15;

/** Satu langkah keputusan untuk agent idle. Kerja selalu menang; tanpa furnitur → perilaku bawaan. */
export const planLeisureStep = (params: {
  agent: { id: string; status: string; leisureRetryAt?: number };
  now: number;
  furniture: FurnitureItem[];
  occupancy: LeisureOccupancy;
  x: number;
  y: number;
  astar: (
    fromX: number,
    fromY: number,
    toX: number,
    toY: number,
  ) => Array<{ x: number; y: number }>;
}): LeisurePlan => {
  const { agent, now, furniture, occupancy, x, y, astar } = params;
  if (agent.status !== "idle") return { kind: "none" };
  if ((agent.leisureRetryAt ?? 0) > now) return { kind: "none" };
  const available = availableActivities(furniture);
  const first = pickLeisureActivity(agent.id, now, available);
  if (!first) return { kind: "none" };
  const order = [
    first,
    ...ORDER.filter((a) => a !== first && available.includes(a)),
  ];
  let sawSpot = false;
  for (const activity of order) {
    const spots = resolveLeisureSpots(activity, agent.id, furniture, occupancy);
    for (const spot of spots) {
      sawSpot = true;
      const atSpot = Math.hypot(x - spot.x, y - spot.y) <= 2;
      if (
        atSpot ||
        Math.hypot(x - spot.approachX, y - spot.approachY) <= ARRIVE_DISTANCE
      ) {
        return { kind: "arrive", spot };
      }
      const path = astar(x, y, spot.approachX, spot.approachY);
      const end = path[path.length - 1];
      // Titik tujuan terhalang → rute berakhir di sel terdekat. Sudah di sana = sampai.
      if (end && path.length <= 1 && Math.hypot(end.x - x, end.y - y) <= ARRIVE_DISTANCE) {
        return { kind: "arrive", spot };
      }
      if (path.length > 0) return { kind: "walk", spot, path };
    }
  }
  return sawSpot ? { kind: "blocked" } : { kind: "none" };
};
