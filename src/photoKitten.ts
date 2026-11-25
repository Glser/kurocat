import burstUrl from './assets/cream-kitten/reference-head-burst.webp';

function load(src: string): HTMLImageElement {
  const image = new Image();
  image.src = src;
  return image;
}
export const photoBurst = load(burstUrl);

export const photoMouseToe = { x: -77, y: 579 };

// Independent of the cat's generic excitement meter: only fresh typing strokes count.
const BURST_KEYS = 8, WINDOW_MS = 800, DRAW_MS = 110, HOLD_MS = 950, LOWER_MS = 200;
const POSE_MS = DRAW_MS + HOLD_MS + LOWER_MS, COOLDOWN_MS = 3200;
export class PhotoKittenAction {
  private strokes: number[] = [];
  private started = -Infinity;
  reset(): void { this.strokes.length = 0; this.started = -Infinity; }
  onStroke(vk: number, now: number): void {
    if (now - this.started < POSE_MS + COOLDOWN_MS) return;
    if (!(vk === 8 || vk === 13 || vk === 32 || (vk >= 0x30 && vk <= 0x39) ||
        (vk >= 0x41 && vk <= 0x5a) || (vk >= 0x60 && vk <= 0x6f) ||
        (vk >= 0xba && vk <= 0xc0) || (vk >= 0xdb && vk <= 0xdf))) return;
    while (this.strokes.length && now - this.strokes[0] > WINDOW_MS) this.strokes.shift();
    this.strokes.push(now);
    if (this.strokes.length === BURST_KEYS) { this.started = now; this.strokes.length = 0; }
  }
  amount(now: number): number {
    const t = now - this.started;
    if (t < 0 || t >= POSE_MS) return 0;
    if (t < DRAW_MS) return 1 - (1 - t / DRAW_MS) ** 3;
    return Math.min(1, (POSE_MS - t) / LOWER_MS);
  }
}
