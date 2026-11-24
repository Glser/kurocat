import mousePoseUrl from './assets/cream-kitten/mouse-pose.webp';
import pawsUrl from './assets/cream-kitten/native-forepaws.webp';
import restUrl from './assets/cream-kitten/rest.webp';
import portraitUrl from './assets/cream-kitten/portrait.webp';

function load(src: string): HTMLImageElement {
  const image = new Image();
  image.src = src;
  return image;
}
export const photoChest = load(restUrl), photoArmed = load(portraitUrl);
export const photoMousePose = load(mousePoseUrl);
const paws = load(pawsUrl);
// Landmarks in the 600-unit portrait, measured at the opaque toe contour.
export const photoToes = { left: { x: 131, y: 564 }, right: { x: 398, y: 568 } };

/** The same native fur as the portrait; only the shoulder-to-wrist span deforms.
 * Coordinates are in portrait space. The last band moves rigidly to the contact point. */
export function drawReachingPaw(ctx: CanvasRenderingContext2D, side: 'left' | 'right', dx: number, dy: number): void {
  if (!paws.naturalWidth) return;
  const x = side === 'left' ? 0 : 300, k = paws.naturalWidth / 600;
  const top = 330, wrist = 494, bands = 8;
  const move = (t: number) => t*t*(3-2*t);
  for (let i = 0; i < bands; i++) {
    const a = i/bands, b = (i+1)/bands, m0 = move(a), m1 = move(b);
    const h = (wrist-top)/bands, y = top+i*h, shift = m1-m0;
    ctx.save();
    ctx.transform(1, 0, dx*shift/h, 1+dy*shift/h, x+dx*m0, y+dy*m0);
    ctx.drawImage(paws, x*k, (y-top)*k, 300*k, h*k, 0, 0, 300, h+0.35);
    ctx.restore();
  }
  ctx.drawImage(paws, x*k, (wrist-top)*k, 300*k, (600-wrist)*k,
    x+dx, wrist+dy, 300, 600-wrist);
}

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
