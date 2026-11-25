import bodyUrl from './reach-body.webp';
import restUrl from './rest-photo.webp';
import leftUrl from './left-reach.webp';
import rightUrl from './right-reach.webp';
import leftSleeve from './left-sleeve.webp';
import rightSleeve from './right-sleeve.webp';

const load = src => Object.assign(new Image(), { src });
const body = load(bodyUrl), rest = load(restUrl);
const legs = [
  { image: load(leftUrl), sleeve: load(leftSleeve), x: 298, top: 517, toe: 654 },
  { image: load(rightUrl), sleeve: load(rightSleeve), x: 535, top: 542, toe: 667 },
];
const poses = new WeakMap();

// Use the previous photo rig's shoulder pivot and shared forearm/wrist axis.
// Only the sleeve changes length; the traced paw stays at the photo scale.
const shoulderRow = 453;
function drawLeg(ctx, leg, rootX, rootY, tip, scale) {
  const dx = tip.x-rootX, dy = tip.y-rootY;
  const length = Math.hypot(dx,dy), depth = (leg.toe-leg.top)*scale;
  ctx.save();
  ctx.translate(rootX,rootY);
  ctx.rotate(Math.atan2(-dx,dy));
  if (tip.blend > 0) {
    ctx.save();
    ctx.globalAlpha *= tip.blend;
    ctx.drawImage(leg.sleeve,-108*scale,0,216*scale,Math.max(0,length-depth+24*scale));
    ctx.restore();
  }
  ctx.drawImage(leg.image,-95*scale,length-depth,190*scale,leg.image.naturalHeight*.5*scale);
  ctx.restore();
}

export function renderPhotoTrial(engine, ctx, breath) {
  engine.drawMiniMouse(ctx);
  if (!rest.naturalWidth || !body.naturalWidth || legs.some(leg => !leg.image.naturalWidth || !leg.sleeve.naturalWidth)) { engine.drawKeyboard(ctx); return; }
  const z = (engine.kbCenterY - engine.catTopY - engine.kbHeight * .34) / 650;
  const center = engine.kbCenterX - engine.kbWidth * .075;
  const left = center - 456*z;
  const baseline = engine.kbCenterY - engine.kbHeight/2 + 13 + (center-engine.kbCenterX)*Math.tan(engine.kbTiltRad) + engine.deskHopY;
  const top = baseline - 650*z + breath*.55;
  const zy = z; // Uniform photo scale: breathing translates the whole pose.
  const now = performance.now();
  let pose = poses.get(engine);
  if (!pose) {
    pose = { time: now - 16, arms: legs.map(() => ({ dx: 0, dy: 0 })) };
    poses.set(engine, pose);
  }
  const elapsed = Math.min(80, now - pose.time);
  pose.time = now;
  const tips = legs.map((leg, i) => {
    const paw = i ? engine.rightPaw : engine.leftPaw;
    const swing = pose.arms[i];
    const restX = left + leg.x*z, restY = top + leg.toe*zy;
    const key = !engine.privacyMode && paw.mode === 'poke';
    const mouse = !engine.privacyMode && paw.mode === 'mouse';
    const dx = key || mouse ? paw.target.x-restX : 0;
    const dy = key ? paw.target.y+engine.kbBounce*1.1+engine.deskHopY-restY
      : mouse ? paw.target.y+engine.deskHopY*1.35-restY : 0;
    const mix = 1-Math.exp(-elapsed/(key ? 19 : 48));
    swing.dx += (dx-swing.dx)*mix;
    swing.dy += (dy-swing.dy)*mix;
    if (!key && !mouse && Math.hypot(swing.dx,swing.dy)<.08) swing.dx=swing.dy=0;
    return {x:restX+swing.dx, y:restY+swing.dy};
  });
  const lean = Math.max(-24,Math.min(24,.21*(pose.arms[0].dx+pose.arms[1].dx)));
  const bodyLeft = left+lean;
  for (const [i,tip] of tips.entries()) {
    // A planted paw stays on the desk even when the opposite shoulder leans.
    // Ease out of the original photo rather than toggling the chest patch.
    const arm = pose.arms[i];
    tip.blend = Math.min(1,Math.hypot(arm.dx-lean,arm.dy)/(10*z));
    const x = i ? 421 : 0, w = i ? 491 : 421;
    const args = [x*2,0,w*2,rest.naturalHeight,bodyLeft+x*z,top,w*z,684*zy];
    if (tip.blend < 1) ctx.drawImage(rest,...args);
    if (tip.blend > 0) {
      ctx.save(); ctx.globalAlpha *= tip.blend; ctx.drawImage(body,...args); ctx.restore();
    }
  }
  engine.drawKeyboard(ctx);
  legs.forEach((leg,i) => drawLeg(ctx,leg,bodyLeft+leg.x*z,top+shoulderRow*zy,tips[i],z));
}
