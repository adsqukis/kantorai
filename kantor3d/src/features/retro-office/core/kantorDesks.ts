// kantorai: agent tanpa meja otomatis mendapat meja kosong supaya bisa bekerja di meja.

export const autoAssignDeskIndexes = (
  deskCount: number,
  manual: Record<string, number>,
  agentIds: string[],
  isUsable: (deskIndex: number) => boolean = () => true,
): Record<string, number> => {
  const out: Record<string, number> = { ...manual };
  const taken = new Set(Object.values(manual));
  let next = 0;
  for (const id of agentIds) {
    if (id in out) continue;
    while (next < deskCount && (taken.has(next) || !isUsable(next))) next += 1;
    if (next >= deskCount) break;
    out[id] = next;
    taken.add(next);
  }
  return out;
};
