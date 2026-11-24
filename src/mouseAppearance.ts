import topView from './assets/mouse/white-g.webp';

// Coordinates in the cropped top photograph; both renderers tint the same physical controls.
export const MOUSE_PHOTO = { url: topView, width: 271, height: 483 };
export const mouseControls = {
  left: new Path2D('M116 6 Q77 21 38 43 Q29 46 27 58 Q14 119 10 228 L116 180 Z'),
  right: new Path2D('M160 6 Q196 20 238 42 Q245 47 246 57 Q258 126 263 228 L158 180 Z'),
  wheel: new Path2D('M123 58 Q137 54 151 58 L151 131 Q137 135 123 131 Z'),
};
const image = new Image();
image.src = topView;

export function drawPhotoMouse(ctx: CanvasRenderingContext2D, x: number, y: number, catFacing: boolean,
  left: number, right: number, wheel: number, colors: { left: string; right: string; middle: string }): void {
  if (!image.naturalWidth) return;
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(-0.06 + (catFacing ? Math.PI : 0));
  ctx.scale(34 / MOUSE_PHOTO.width, 50 / MOUSE_PHOTO.height);
  ctx.translate(-MOUSE_PHOTO.width / 2, -MOUSE_PHOTO.height / 2);
  ctx.save();
  ctx.shadowColor = 'rgba(27,37,47,0.33)';
  ctx.shadowBlur = 3;
  ctx.shadowOffsetY = 2;
  ctx.drawImage(image, 0, 0);
  ctx.restore();
  if (left > 0.01) { ctx.globalAlpha = 0.76 * left; ctx.fillStyle = colors.left; ctx.fill(mouseControls.left); }
  if (right > 0.01) { ctx.globalAlpha = 0.76 * right; ctx.fillStyle = colors.right; ctx.fill(mouseControls.right); }
  if (wheel > 0.01) { ctx.globalAlpha = 0.84 * wheel; ctx.fillStyle = colors.middle; ctx.fill(mouseControls.wheel); }
  ctx.restore();
}
