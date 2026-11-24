import bodyUrl from './reach-body.webp';
import leftUrl from './left-reach.webp';
import rightUrl from './right-reach.webp';

const load = src => Object.assign(new Image(), { src });
const body = load(bodyUrl);
const legs = [
  { side: 'left', image: load(leftUrl), x: 322, toe: 620 },
  { side: 'right', image: load(rightUrl), x: 567, toe: 622 },
];
const poses = new WeakMap();

// The last 62 photo units are the wrist and toes. Keep their proportions
// while the upper leg rotates from the flank and supplies the remaining reach.
function drawLeg(ctx, leg, rootX, rootY, tipX, tipY, scale) {
  const dx = tipX - rootX, dy = tipY - rootY;
  const length = Math.hypot(dx, dy);
  const wristRow = leg.toe - 62 - 400;
  const wristDistance = Math.max(2, length - 62 * scale);
  const image = leg.image;
  const pixels = image.naturalWidth / 244;
  const wristPixel = Math.round(wristRow * pixels);
  ctx.save();
  ctx.translate(rootX, rootY);
  ctx.rotate(Math.atan2(-dx, dy));
  const width = 244 * scale;
  ctx.drawImage(image, 0, 0, image.width, wristPixel, -width / 2, 0, width, wristDistance + .18);
  ctx.drawImage(image, 0, wristPixel, image.width, image.height - wristPixel,
    -width / 2, wristDistance, width, (image.height - wristPixel) * scale / pixels);
  ctx.restore();
}

export function renderPhotoTrial(engine, ctx, breath) {
  engine.drawMiniMouse(ctx);
  if (!body.naturalWidth || legs.some(leg => !leg.image.naturalWidth)) { engine.drawKeyboard(ctx); return; }
  const z = (engine.kbCenterY - engine.catTopY - engine.kbHeight * .34) / 630;
  const center = engine.kbCenterX - engine.kbWidth * .075;
  const left = center - 468*z;
  const baseline = engine.kbCenterY - engine.kbHeight/2 + 13 + (center-engine.kbCenterX)*Math.tan(engine.kbTiltRad) + engine.deskHopY;
  const top = baseline - 630*z + breath*.55;
  const zy = (baseline-top)/630;
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
    const click = !engine.privacyMode && !i && (engine.mouseLeftDown || engine.mouseRightDown);
    const dx = key ? paw.target.x-restX : 0;
    const dy = key ? paw.target.y+engine.kbBounce*1.1+engine.deskHopY-restY : click ? 3 : 0;
    const mix = 1-Math.exp(-elapsed/(key ? 19 : 48));
    swing.dx += (dx-swing.dx)*mix;
    swing.dy += (dy-swing.dy)*mix;
    return {x:restX+swing.dx, y:restY+swing.dy};
  });
  const [a,b] = pose.arms;
  const lean = Math.max(-24, Math.min(24, .21*(a.dx+b.dx)));
  ctx.drawImage(body, left+lean, top, 960*z, 640*zy);
  engine.drawKeyboard(ctx);
  legs.forEach((leg, i) => drawLeg(ctx, leg, left+lean+leg.x*z, top+400*zy, tips[i].x,tips[i].y,z));
}
