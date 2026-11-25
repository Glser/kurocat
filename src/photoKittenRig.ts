import { photoBurst } from './photoKitten';
import bodyUrl from './assets/cream-kitten/reach-body.webp';
import restUrl from './assets/cream-kitten/rest-photo.webp';
import leftUrl from './assets/cream-kitten/left-reach.webp';
import rightUrl from './assets/cream-kitten/right-reach.webp';
import mouseForeleg from './assets/cream-kitten/mouse-foreleg.webp';
import rightSleeve from './assets/cream-kitten/right-sleeve.webp';

const load = (src: string) => Object.assign(new Image(), { src });
const body = load(bodyUrl), rest = load(restUrl);
const sleepPhoto = import.meta.env.VITE_PHOTO_SLEEP_PREVIEW
  ? load(new URL('./assets/cream-kitten/sleep-photo.webp', import.meta.url).href) : null;
const legs = [
  { image: load(leftUrl), sleeve: load(mouseForeleg), sleeveWidth: 200, continuous: true, x: 298, top: 517, toe: 654 },
  { image: load(rightUrl), sleeve: load(rightSleeve), sleeveWidth: 216, continuous: false, x: 535, top: 542, toe: 667 },
];
type Leg = typeof legs[number];
type Tip = { x: number; y: number; blend: number };
type Paw = { mode: string; target: { x: number; y: number } };
interface PhotoFrame {
  portraitAnchorX: number; kbCenterY: number; kbWidth: number; kbHeight: number; kbTiltRad: number;
  catTopY: number; deskHopY: number; kbBounce: number; privacyMode: boolean;
  burst: boolean; asleep: boolean; blinking: boolean; leftPaw: Paw; rightPaw: Paw;
}

// Use the previous photo rig's shoulder pivot and shared forearm/wrist axis.
// Only the sleeve changes length; the traced paw stays at the photo scale.
const shoulderRow = 453;
function drawLeg(ctx: CanvasRenderingContext2D, leg: Leg, rootX: number, rootY: number, tip: Tip, scale: number) {
  const dx = tip.x-rootX, dy = tip.y-rootY;
  const length = Math.hypot(dx,dy), depth = (leg.toe-leg.top)*scale;
  ctx.save();
  ctx.translate(rootX,rootY);
  ctx.rotate(Math.atan2(-dx,dy));
  if (tip.blend > 0) {
    ctx.save();
    ctx.globalAlpha *= tip.blend;
    const width = leg.sleeveWidth * scale;
    if (leg.continuous) {
      // Shoulder and hand come from one photo strip: stretch above the
      // wrist only. Both draws sample the very same seam, with a short
      // matching fur overlap so rotation never exposes a transparent seam.
      const pixels = leg.sleeve.naturalWidth / leg.sleeveWidth;
      const split = (555-425)*pixels;
      const wristY = length-(leg.toe-555)*scale;
      const startY = Math.min((425-shoulderRow)*scale,wristY-scale);
      ctx.drawImage(leg.sleeve,0,0,leg.sleeve.naturalWidth,split+4*pixels,
        -width/2,startY,width,wristY-startY+4*scale);
      ctx.drawImage(leg.sleeve,0,split,leg.sleeve.naturalWidth,leg.sleeve.naturalHeight-split,
        -width/2,wristY,width,(leg.sleeve.naturalHeight-split)*scale/pixels);
    } else {
      ctx.drawImage(leg.sleeve,-width/2,0,width,Math.max(0,length-depth+24*scale));
    }
    ctx.restore();
  }
  if (leg.continuous) ctx.globalAlpha *= 1-tip.blend;
  if (ctx.globalAlpha > 0) ctx.drawImage(leg.image,-95*scale,length-depth,190*scale,leg.image.naturalHeight*.5*scale);
  ctx.restore();
}

export class PhotoKittenRig {
  private time?: number;
  private readonly grip = { phase: 0, x: 0, y: 0 };
  private readonly arms = legs.map(() => ({dx:0, dy:0}));

  draw(frame: PhotoFrame, ctx: CanvasRenderingContext2D, breath: number, drawKeyboard: () => void): void {
    if (!rest.naturalWidth || !body.naturalWidth || legs.some(leg => !leg.image.naturalWidth || !leg.sleeve.naturalWidth)) { drawKeyboard(); return; }
    const z = (frame.kbCenterY - frame.catTopY - frame.kbHeight * .34) / 650;
    const center = frame.portraitAnchorX - frame.kbWidth * .075;
    const left = center - 456*z;
    const baseline = frame.kbCenterY - frame.kbHeight/2 + 13 + (center-frame.portraitAnchorX)*Math.tan(frame.kbTiltRad) + frame.deskHopY;
    const top = baseline - 650*z + breath*.55;
    if (frame.asleep && sleepPhoto?.naturalWidth) {
      drawKeyboard();
      ctx.drawImage(sleepPhoto, left, top, 912*z, 684*z);
      return;
    }
    const zy = z; // Uniform photo scale: breathing translates the whole pose.
    const now = performance.now();
    const elapsed = this.time === undefined ? 16 : Math.min(80, now-this.time);
    this.time = now;
    const tips = legs.map((leg, i) => {
      const paw = i ? frame.rightPaw : frame.leftPaw;
      const swing = this.arms[i];
      const restX = left + leg.x*z, restY = top + leg.toe*zy;
      const key = !frame.privacyMode && paw.mode === 'poke';
      const mouse = !frame.privacyMode && paw.mode === 'mouse';
      // Keep the keyboard pose independent of the mouse grip. Approaching and
      // releasing use a small arc; once planted, the toes track the mouse.
      const dx = key ? paw.target.x-restX : 0;
      const dy = key ? paw.target.y+frame.kbBounce*1.1+frame.deskHopY-restY : 0;
      const mix = 1-Math.exp(-elapsed/(key ? 19 : 48));
      swing.dx += (dx-swing.dx)*mix;
      swing.dy += (dy-swing.dy)*mix;
      if (!key && Math.hypot(swing.dx,swing.dy)<.08) swing.dx=swing.dy=0;
      let x = restX+swing.dx, y = restY+swing.dy;
      if (i === 0) {
        const grip = this.grip;
        if (mouse) {
          const contactY = paw.target.y+frame.deskHopY*1.35;
          const follow = grip.phase === 0 ? 1 : 1-Math.exp(-elapsed/20);
          grip.x += (paw.target.x-grip.x)*follow;
          grip.y += (contactY-grip.y)*follow;
        }
        grip.phase = Math.max(0,Math.min(1,grip.phase + (mouse ? elapsed/195 : -elapsed/(key ? 90 : 220))));
        const w = grip.phase*grip.phase*(3-2*grip.phase);
        x += (grip.x-x)*w;
        y += (grip.y-y)*w - 22*z*4*w*(1-w);
      }
      return {x, y, dx:x-restX, dy:y-restY, blend:0};
    });
    const lean = Math.max(-24,Math.min(24,.21*(tips[0].dx+tips[1].dx)));
    const bodyLeft = left+lean;
    if (frame.burst && photoBurst.naturalWidth) {
      // Register by eye midpoint and eye spacing, not the bounds of the prop.
      // Normal portrait: 912 x 684 units; burst plate: 1050 x 900 pixels.
      const burstScale = z * (148.73 / 188.63);
      ctx.drawImage(photoBurst, bodyLeft + 487.45*z - 589.87*burstScale,
        top + 261.14*z - 373.21*burstScale,
        photoBurst.naturalWidth*burstScale, photoBurst.naturalHeight*burstScale);
      drawKeyboard();
      return;
    }
    // Blink with the photographed face, without changing the active paw pose.
    const blinkPhoto = frame.blinking && sleepPhoto?.naturalWidth ? sleepPhoto : null;
    const headRows = blinkPhoto ? 420 : 0;
    if (blinkPhoto) {
      ctx.drawImage(blinkPhoto,0,0,blinkPhoto.naturalWidth,2*headRows,
        bodyLeft,top,912*z,headRows*zy);
    }
    for (const [i,tip] of tips.entries()) {
      // A planted paw stays on the desk even when the opposite shoulder leans.
      // Ease out of the original photo rather than toggling the chest patch.
      tip.blend = Math.min(1,Math.hypot(tip.dx-lean,tip.dy)/(10*z));
      const x = i ? 421 : 0, w = i ? 491 : 421;
      const args: [number, number, number, number, number, number, number, number] = [x*2,headRows*2,w*2,rest.naturalHeight-headRows*2,
        bodyLeft+x*z,top+headRows*zy,w*z,(684-headRows)*zy];
      if (tip.blend < 1) ctx.drawImage(rest,...args);
      if (tip.blend > 0) {
        ctx.save(); ctx.globalAlpha *= tip.blend; ctx.drawImage(body,...args); ctx.restore();
      }
    }
    drawKeyboard();
    legs.forEach((leg,i) => drawLeg(ctx,leg,bodyLeft+leg.x*z,top+shoulderRow*zy,tips[i],z));
  }
}
