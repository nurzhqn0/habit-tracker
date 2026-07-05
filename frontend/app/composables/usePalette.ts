// The 20-color uhabits palette (Themes.kt color(paletteIndex)); index 8 is the default.
export const PALETTE = [
  "#D32F2F", "#E64A19", "#F57C00", "#FF8F00", "#F9A825",
  "#AFB42B", "#7CB342", "#388E3C", "#00897B", "#00ACC1",
  "#039BE5", "#1976D2", "#303F9F", "#5E35B1", "#8E24AA",
  "#D81B60", "#5D4037", "#424242", "#757575", "#9E9E9E",
] as const;

export function paletteColor(index: number): string {
  return PALETTE[index] ?? PALETTE[8]!;
}
