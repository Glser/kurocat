import * as THREE from 'three';
import { MOUSE_PHOTO, mouseControls } from './mouseAppearance';

// Top-photo cross sections (image y, left x, right x), with crown heights from the side view.
const sections = [
  [2, 122, 154, .025], [9, 101, 175, .034], [26, 65, 211, .044], [45, 33, 242, .052],
  [72, 24, 251, .059], [110, 18, 257, .067], [160, 13, 262, .078], [226, 9, 265, .098],
  [287, 7, 265, .112], [329, 14, 260, .118], [373, 25, 250, .116], [410, 39, 236, .107],
  [441, 59, 216, .094], [459, 77, 198, .076], [470, 94, 181, .059], [478, 117, 159, .039], [480, 131, 146, .019],
];

function controlMaterial(part: keyof typeof mouseControls) {
  const canvas = document.createElement('canvas');
  canvas.width = MOUSE_PHOTO.width;
  canvas.height = MOUSE_PHOTO.height;
  const ctx = canvas.getContext('2d')!;
  ctx.fillStyle = '#fff'; ctx.fill(mouseControls[part]);
  return new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(canvas), transparent: true, opacity: 0,
    depthWrite: false, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 });
}

export function buildPhotoMouseShell() {
  const group = new THREE.Group();
  const tex = new THREE.TextureLoader().load(MOUSE_PHOTO.url);
  tex.colorSpace = THREE.SRGBColorSpace;
  const body = new THREE.MeshBasicMaterial({ map: tex, vertexColors: true });
  const cols = 42, rows = 80;
  // The first and last columns turn under the shell to form the shaded side walls.
  const geo = new THREE.PlaneGeometry(1, 1, cols, rows);
  const pos = geo.attributes.position, uv = geo.attributes.uv, colors: number[] = [];
  let section = 0;
  for (let j = 0; j <= rows; j++) {
    const py = 2 + 478 * j / rows;
    while (section + 2 < sections.length && py > sections[section + 1][0]) section++;
    const a = sections[section], b = sections[section + 1];
    const t = (py - a[0]) / (b[0] - a[0]);
    const lo = THREE.MathUtils.lerp(a[1], b[1], t), hi = THREE.MathUtils.lerp(a[2], b[2], t);
    const crown = THREE.MathUtils.lerp(a[3], b[3], t);
    for (let i = 0; i <= cols; i++) {
      const u = THREE.MathUtils.clamp((i - 1) / (cols - 2), 0, 1);
      const skirt = i === 0 || i === cols;
      const px = lo + (hi - lo) * u;
      const wheel = Math.max(0, 1 - ((px - 137) / 16) ** 2 - ((py - 95) / 42) ** 2);
      const y = skirt ? .004 : crown * (.32 + .68 * Math.sin(Math.PI * u) ** .40) + wheel * .009;
      const idx = j * (cols + 1) + i;
      pos.setXYZ(idx, (137 - px) * .00115 * (skirt ? .96 : 1), y, (.5 - (py - 2) / 478) * .49 * (skirt ? .98 : 1));
      uv.setXY(idx, px / MOUSE_PHOTO.width, 1 - py / MOUSE_PHOTO.height);
      const shade = skirt ? .55 : .85 + .15 * Math.sin(Math.PI * u);
      colors.push(shade, shade, shade);
    }
  }
  geo.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  geo.computeVertexNormals();
  group.add(new THREE.Mesh(geo, body));
  // Close the unprinted underside and both tips without stretching the top photo over them.
  const baseIndices: number[] = [], stride = cols + 1;
  for (let j = 0; j < rows; j++) {
    const a = j * stride, b = a + stride;
    baseIndices.push(a, a + cols, b, b, a + cols, b + cols);
  }
  for (const start of [0, rows * stride]) {
    for (let i = 1; i < cols; i++) baseIndices.push(start, start + i, start + i + 1);
  }
  const base = new THREE.BufferGeometry();
  base.setAttribute('position', pos);
  base.setIndex(baseIndices);
  group.add(new THREE.Mesh(base, new THREE.MeshBasicMaterial({ color: '#b9c2c8', side: THREE.DoubleSide })));
  const left = controlMaterial('left'), right = controlMaterial('right'), wheel = controlMaterial('wheel');
  for (const mat of [left, right, wheel]) {
    const patch = new THREE.Mesh(geo, mat); patch.renderOrder = 5; group.add(patch);
  }
  const thumbMat = new THREE.MeshBasicMaterial({ color: '#d4dce0' });
  const thumbGeo = new THREE.SphereGeometry(1, 12, 8);
  for (const z of [.029, -.032]) {
    const button = new THREE.Mesh(thumbGeo, thumbMat);
    button.position.set(.148, .032, z); button.scale.set(.009, .009, .027); group.add(button);
  }
  return { group, body, left, right, wheel };
}
