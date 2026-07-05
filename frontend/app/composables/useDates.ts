export function toDateKey(d: Date): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function todayKey(): string {
  return toDateKey(new Date());
}

export function shiftDateKey(key: string, days: number): string {
  const [y, m, d] = key.split("-").map(Number);
  const date = new Date(y!, m! - 1, d!);
  date.setDate(date.getDate() + days);
  return toDateKey(date);
}

/** Last `count` date keys ending at `end` (inclusive), newest first. */
export function lastNDateKeys(count: number, end: string = todayKey()): string[] {
  return Array.from({ length: count }, (_, i) => shiftDateKey(end, -i));
}

export function weekdayShort(key: string): string {
  const [y, m, d] = key.split("-").map(Number);
  return new Date(y!, m! - 1, d!).toLocaleDateString(undefined, { weekday: "short" });
}

export function dayOfMonth(key: string): number {
  return Number(key.slice(8));
}
