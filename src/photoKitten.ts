import leftLegUrl from './assets/cream-kitten/key-leg-left.webp';
import rightLegUrl from './assets/cream-kitten/key-leg-right.webp';
import restUrl from './assets/cream-kitten/reference-head-rest.webp';
import burstUrl from './assets/cream-kitten/reference-head-burst.webp';

function load(src: string): HTMLImageElement {
  const image = new Image();
  image.src = src;
  return image;
}
export const photoRest = load(restUrl), photoBurst = load(burstUrl);
const legs = { left: load(leftLegUrl), right: load(rightLegUrl) };

// Plates share the same right edge and 600-unit body. The grip has extra left bleed.
export function drawPhotoBody(ctx: CanvasRenderingContext2D, pose: HTMLImageElement,
  x: number, y: number, width: number, height: number): void {
  if (!pose.naturalWidth) return;
  const plateWidth = width * pose.naturalWidth / pose.naturalHeight;
  ctx.drawImage(pose, x + width - plateWidth, y, plateWidth, height);
}
// Relaxed toes turn in slightly from the elbows, in 600-unit portrait space.
export const photoToes = { left: { x: 112, y: 568 }, right: { x: 379, y: 568 } };
export const photoMouseToe = { x: -77, y: 579 };

// Feather the proximal fur into the chest while the outer shoulder silhouette
// comes from the intact photograph drawn behind the body.
const frontLegs = new WeakMap<HTMLImageElement, HTMLCanvasElement>();
function foregroundLeg(keyLeg: HTMLImageElement): HTMLCanvasElement {
  const cached = frontLegs.get(keyLeg);
  if (cached) return cached;
  const canvas = document.createElement('canvas');
  canvas.width = keyLeg.naturalWidth;
  canvas.height = keyLeg.naturalHeight;
  const ctx = canvas.getContext('2d')!;
  ctx.drawImage(keyLeg, 0, 0);
  const mask = ctx.createLinearGradient(0, canvas.height * 0.10, 0, canvas.height * 0.26);
  mask.addColorStop(0, 'transparent');
  mask.addColorStop(1, 'black');
  ctx.globalCompositeOperation = 'destination-in';
  ctx.fillStyle = mask;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  // Ease the chest-facing edge into the breast fur above the wrist. The
  // anatomical left/right mirror is applied later by drawReachingPaw.
  const unit = canvas.height / 270;
  const overlap = ctx.createLinearGradient(108*unit, 0, 165*unit, 0);
  overlap.addColorStop(0, 'black');
  overlap.addColorStop(1, 'transparent');
  const edgeMask = document.createElement('canvas');
  edgeMask.width = canvas.width;
  edgeMask.height = canvas.height;
  const edge = edgeMask.getContext('2d')!;
  edge.fillStyle = overlap;
  edge.fillRect(0, 0, canvas.width, canvas.height);
  const wrist = edge.createLinearGradient(0, 90*unit, 0, 156*unit);
  wrist.addColorStop(0, 'transparent');
  wrist.addColorStop(1, 'black');
  edge.fillStyle = wrist;
  edge.fillRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(edgeMask, 0, 0);
  frontLegs.set(keyLeg, canvas);
  return canvas;
}

export function drawReachingPaw(ctx: CanvasRenderingContext2D, side: 'left' | 'right',
  toeX: number, toeY: number, layer: 'shoulder' | 'forearm'): void {
  const keyLeg = legs[side];
  if (!keyLeg.naturalWidth) return;
  const left = side === 'left';
  // At the marked inner edges of the flanks, in portrait coordinates.
  const shoulderX = left ? 109 : 448;
  const shoulderY = left ? 363 : 441;
  const vx = toeX - shoulderX, vy = toeY - shoulderY;
  const scale = 0.78, wrist = 155, toe = 245;
  const wristDistance = Math.max(1, Math.hypot(vx, vy) - (toe-wrist)*scale);
  const k = keyLeg.naturalHeight / 270;
  const width = keyLeg.naturalWidth / k, leftEdge = -(82 + 24)*scale;
  const fur = layer === 'shoulder' ? keyLeg : foregroundLeg(keyLeg);
  ctx.save();
  ctx.translate(shoulderX, shoulderY);
  ctx.rotate(Math.atan2(-vx, vy));
  if (!left) ctx.scale(-1, 1);
  ctx.drawImage(fur, 0, 0, keyLeg.naturalWidth, wrist*k,
    leftEdge, -24, width*scale, wristDistance+24.4);
  if (layer === 'forearm') {
    ctx.drawImage(fur, 0, wrist*k, keyLeg.naturalWidth, (270-wrist)*k,
      leftEdge, wristDistance, width*scale, (270-wrist)*scale);
  }
  ctx.restore();
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
