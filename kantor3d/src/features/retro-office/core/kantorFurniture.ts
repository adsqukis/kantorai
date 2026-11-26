// kantorai: furnitur pojok santai (TV dan kasur) untuk kantor tim agent.

export const KANTOR_FURNITURE_TYPES = ["tv", "bed"] as const;
export type KantorFurnitureType = (typeof KANTOR_FURNITURE_TYPES)[number];

export const KANTOR_FOOTPRINT: Record<KantorFurnitureType, [number, number]> = {
  tv: [80, 20],
  bed: [50, 90],
};

export const KANTOR_PALETTE_ENTRIES: Array<{
  type: KantorFurnitureType;
  label: string;
  icon: string;
  defaults: { w?: number; h?: number; facing?: number };
}> = [
  { type: "tv", label: "TV", icon: "📺", defaults: { w: 80, h: 20, facing: 0 } },
  { type: "bed", label: "Kasur", icon: "🛏️", defaults: { w: 50, h: 90 } },
];
