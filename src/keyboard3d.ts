import { buildPhotoMouseShell } from './mouseShell3d';
import { keyboardCase, keyRows, frontLegend } from './keyboardFinish';
import * as THREE from 'three';
import {
  getKeyboardLayout,
  resolveKeyByVk,
  type KeyboardLayoutId,
  type KeySpec,
} from './keyboardLayout';
import type { KeyboardOrientation } from './catEngine';

export class Spring1D {
  public x: number;
  public v = 0;
  public hz: number;
  public damping: number;

  constructor(x = 0, hz = 2, damping = 0.7) {
    this.x = x;
    this.hz = hz;
    this.damping = damping;
  }

  public step(target: number, dt: number): number {
    const w = 2 * Math.PI * this.hz;
    const n = Math.max(1, Math.ceil(dt * 240));
    const h = dt / n;
    for (let i = 0; i < n; i++) {
      this.v += (w * w * (target - this.x) - 2 * this.damping * w * this.v) * h;
      this.x += this.v * h;
    }
    return this.x;
  }

  public kick(v: number): void {
    this.v += v;
  }

  public set(x: number): void {
    this.x = x;
    this.v = 0;
  }
}

export class Spring3D {
  public x: THREE.Vector3;
  public v = new THREE.Vector3();
  public hz: number;
  public damping: number;

  constructor(x: THREE.Vector3, hz = 3.2, damping = 0.78) {
    this.x = x.clone();
    this.hz = hz;
    this.damping = damping;
  }

  public step(target: THREE.Vector3, dt: number): THREE.Vector3 {
    const w = 2 * Math.PI * this.hz;
    const n = Math.max(1, Math.ceil(dt * 240));
    const h = dt / n;
    for (let i = 0; i < n; i++) {
      this.v.x += (w * w * (target.x - this.x.x) - 2 * this.damping * w * this.v.x) * h;
      this.v.y += (w * w * (target.y - this.x.y) - 2 * this.damping * w * this.v.y) * h;
      this.v.z += (w * w * (target.z - this.x.z) - 2 * this.damping * w * this.v.z) * h;
      this.x.x += this.v.x * h;
      this.x.y += this.v.y * h;
      this.x.z += this.v.z * h;
    }
    return this.x;
  }
}

export const approach = (rate: number, dt: number): number => 1 - Math.exp(-rate * dt);
export const clamp = (v: number, a: number, b: number): number => Math.max(a, Math.min(b, v));
export const mix = (a: number, b: number, t: number): number => a + (b - a) * t;
export const smoothstep = (a: number, b: number, x: number): number => {
  const t = clamp((x - a) / (b - a), 0, 1);
  return t * t * (3 - 2 * t);
};

/** Dynamic variable-radius 3D tube rebuilt cleanly in place each frame (zero GC churn). */
export class TaperTube3D {
  public readonly mesh: THREE.Mesh;
  private readonly n: number;
  private readonly m: number;
  private readonly pts: THREE.Vector3[];
  private readonly T = new THREE.Vector3();
  private readonly N = new THREE.Vector3();
  private readonly B = new THREE.Vector3();
  private readonly tmp = new THREE.Vector3();

  constructor(segments: number, radial: number, material: THREE.Material, renderOrder = 0) {
    this.n = segments;
    this.m = radial;
    const geo = new THREE.BufferGeometry();
    const count = (segments + 1) * radial;
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(count * 3), 3));
    geo.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(count * 3), 3));
    geo.setAttribute(
      'along',
      new THREE.BufferAttribute(
        Float32Array.from({ length: count }, (_, k) => Math.floor(k / radial) / segments),
        1,
      ),
    );
    const index: number[] = [];
    for (let i = 0; i < segments; i++) {
      for (let j = 0; j < radial; j++) {
        const a = i * radial + j;
        const b = i * radial + ((j + 1) % radial);
        const c = a + radial;
        const d = b + radial;
        index.push(a, b, c, b, d, c);
      }
    }
    geo.setIndex(index);
    this.mesh = new THREE.Mesh(geo, material);
    this.mesh.renderOrder = renderOrder;
    this.mesh.frustumCulled = false;
    this.pts = Array.from({ length: segments + 1 }, () => new THREE.Vector3());
  }

  public update(
    point: (t: number, out: THREE.Vector3) => void,
    radius: (t: number) => number,
    grow: number | ((t: number) => number) = 0,
  ): void {
    const { n, m, pts, T, N, B, tmp } = this;
    for (let i = 0; i <= n; i++) point(i / n, pts[i]);
    const pos = this.mesh.geometry.attributes.position.array as Float32Array;
    const nrm = this.mesh.geometry.attributes.normal.array as Float32Array;
    for (let i = 0; i <= n; i++) {
      T.subVectors(pts[Math.min(n, i + 1)], pts[Math.max(0, i - 1)]).normalize();
      if (i === 0) {
        tmp.set(0, 1, 0);
        if (Math.abs(T.dot(tmp)) > 0.9) tmp.set(1, 0, 0);
        N.crossVectors(T, tmp).normalize();
      } else {
        B.crossVectors(N, T);
        N.crossVectors(T, B).normalize();
      }
      B.crossVectors(T, N).normalize();
      const gVal = typeof grow === 'function' ? grow(i / n) : grow;
      const r = Math.max(0.0008, radius(i / n) + gVal);
      for (let j = 0; j < m; j++) {
        const a = (j / m) * Math.PI * 2;
        const ca = Math.cos(a);
        const sa = Math.sin(a);
        const c = ca * r;
        const s = sa * r;
        const k = (i * m + j) * 3;
        pos[k] = pts[i].x + N.x * c + B.x * s;
        pos[k + 1] = pts[i].y + N.y * c + B.y * s;
        pos[k + 2] = pts[i].z + N.z * c + B.z * s;
        nrm[k] = N.x * ca + B.x * sa;
        nrm[k + 1] = N.y * ca + B.y * sa;
        nrm[k + 2] = N.z * ca + B.z * sa;
      }
    }
    this.mesh.geometry.attributes.position.needsUpdate = true;
    this.mesh.geometry.attributes.normal.needsUpdate = true;
    this.mesh.geometry.computeBoundingSphere();
  }
}

interface KeyEntry3D {
  spec: KeySpec;
  holder: THREE.Group;
  topMat: THREE.MeshBasicMaterial;
  baseColor: THREE.Color;
  x: number;
  z: number;
  down: boolean;
  depth: number;
  glow: number;
}

const legendTextureCache = new Map<string, THREE.CanvasTexture>();

// CylinderGeometry wraps the four bevel faces across U=0..1. Its last quarter
// faces the viewer after capGeo's quarter-diagonal turn; leave the top unprinted.
function makeFrontPrint(label: string, rotated: boolean, width: number): THREE.CanvasTexture {
  const key = `front:${label}:${rotated}:${width}`;
  const cached = legendTextureCache.get(key);
  if (cached) return cached;
  const c = document.createElement('canvas');
  c.width = 512;
  c.height = 64;
  const g = c.getContext('2d')!;
  g.fillStyle = '#ffffff';
  g.fillRect(0, 0, c.width, c.height);
  g.translate(448, 32);
  if (rotated) g.rotate(Math.PI);
  g.scale(1 / width, 1);
  g.font = 'bold 46px "Segoe UI", sans-serif';
  g.fillStyle = '#263d4c';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.fillText(label, 0, 0, 110 * width);
  const tex = new THREE.CanvasTexture(c);
  tex.anisotropy = 4;
  tex.colorSpace = THREE.SRGBColorSpace;
  legendTextureCache.set(key, tex);
  return tex;
}

function makeSoftShadowTexture(): THREE.CanvasTexture {
  const c = document.createElement('canvas');
  c.width = 256;
  c.height = 256;
  const g = c.getContext('2d')!;
  const grad = g.createRadialGradient(128, 128, 22, 128, 128, 122);
  grad.addColorStop(0, 'rgba(0, 0, 0, 0.44)');
  grad.addColorStop(0.55, 'rgba(0, 0, 0, 0.20)');
  grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 256, 256);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function makeRoundedSlab(w: number, d: number, h: number, r: number, color: string, y: number): THREE.Mesh {
  const s = new THREE.Shape();
  const x0 = -w / 2;
  const z0 = -d / 2;
  s.moveTo(x0 + r, z0);
  s.lineTo(x0 + w - r, z0);
  s.quadraticCurveTo(x0 + w, z0, x0 + w, z0 + r);
  s.lineTo(x0 + w, z0 + d - r);
  s.quadraticCurveTo(x0 + w, z0 + d, x0 + w - r, z0 + d);
  s.lineTo(x0 + r, z0 + d);
  s.quadraticCurveTo(x0, z0 + d, x0, z0 + d - r);
  s.lineTo(x0, z0 + r);
  s.quadraticCurveTo(x0, z0, x0 + r, z0);
  const g = new THREE.ExtrudeGeometry(s, { depth: h, bevelEnabled: false, curveSegments: 6 });
  g.rotateX(Math.PI / 2);
  g.translate(0, y + h, 0);
  return new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color }));
}

/**
 * KuroCat's iconic clean desktop gear in real 3D:
 * - Slightly canted ivory mechanical keyboard (NO KeyCat white sticker halo!)
 * - Photo-mapped wireless mouse with independent button and wheel highlights.
 */
export class KeyboardAndMouse3D {
  public readonly boardGroup = new THREE.Group();
  public readonly mouseGroup = new THREE.Group();
  public readonly deskGroup = new THREE.Group();

  private readonly capGeo: THREE.CylinderGeometry;
  private readonly capBottomMat = new THREE.MeshBasicMaterial({ color: '#1b1c20' });
  private readonly shadowTex = makeSoftShadowTexture();

  private keys = new Map<string, KeyEntry3D>();
  private layoutId: KeyboardLayoutId = '65';
  private orientation: KeyboardOrientation = 'cat';
  private hitColor = new THREE.Color('#d4f044');
  private rightBtnColor = new THREE.Color('#ff7b3b');
  private boardH = 0.115;
  private capH = 0.056;
  private boardWidth = 2.4;

  // Cordless 3D KuroCat Mini Mouse
  private readonly mouseShape = new THREE.Group();
  private readonly mouseBodyMat: THREE.MeshBasicMaterial;
  private readonly leftBtnMat: THREE.MeshBasicMaterial;
  private readonly rightBtnMat: THREE.MeshBasicMaterial;
  private readonly wheelMat: THREE.MeshBasicMaterial;
  private readonly mouseHome = new THREE.Vector3(-1.32, 0.015, 1.04);
  private readonly mouseOffset = new THREE.Vector3();
  private readonly mouseTarget = new THREE.Vector3();
  private readonly mouseFollow = new Spring3D(new THREE.Vector3(), 5.5, 0.78);
  private leftPress = 0;
  private rightPress = 0;
  private wheelGlow = 0;

  private privacyPlate: THREE.Mesh | null = null;
  private privacyMat: THREE.MeshBasicMaterial | null = null;

  constructor(scene: THREE.Scene) {
    this.capGeo = new THREE.CylinderGeometry(Math.SQRT1_2 * 0.80, Math.SQRT1_2, 1, 4, 1);
    this.capGeo.rotateY(Math.PI / 4);
    this.capGeo.translate(0, 0.5, 0);

    // Subtle playful KuroCat keyboard tilt matching original catEngine.ts
    this.boardGroup.position.set(0.24, 0.015, 1.08);
    this.boardGroup.rotation.set(0.06, -0.042, 0);
    this.deskGroup.add(this.boardGroup);

    // Reference mouse uses the same moving group and paw contact target as before.
    this.mouseGroup.position.copy(this.mouseHome);
    this.mouseShape.rotation.y = -0.10;
    this.mouseGroup.add(this.mouseShape);

    const shell = buildPhotoMouseShell();
    this.mouseBodyMat = shell.body;
    this.leftBtnMat = shell.left;
    this.rightBtnMat = shell.right;
    this.wheelMat = shell.wheel;
    const shadow = new THREE.Mesh(new THREE.PlaneGeometry(.48, .67),
      new THREE.MeshBasicMaterial({ map: this.shadowTex, transparent: true, depthWrite: false, opacity: .72 }));
    shadow.rotation.x = -Math.PI / 2;
    shadow.position.set(0, .001, .012);
    this.mouseShape.add(shadow, shell.group);
    this.deskGroup.add(this.mouseGroup);

    scene.add(this.deskGroup);
    this.rebuildBoard('65', 'cat');
  }

  public setAccentColors(primaryHex: string, rightHex: string): void {
    this.hitColor.set(primaryHex);
    this.rightBtnColor.set(rightHex);
    this.leftBtnMat.color.set(primaryHex);
    this.rightBtnMat.color.set(rightHex);
  }

  public setStyle(style: '3d' | '2d'): void {
    const is3D = style === '3d';
    this.mouseBodyMat.vertexColors = is3D;
    this.mouseBodyMat.color.set(is3D ? '#ffffff' : '#f4f4f0');
    this.mouseBodyMat.needsUpdate = true;
  }

  public rebuildBoard(layoutId: KeyboardLayoutId, orientation: KeyboardOrientation): void {
    this.layoutId = layoutId;
    this.orientation = orientation;
    this.keys.clear();

    while (this.boardGroup.children.length > 0) {
      this.boardGroup.remove(this.boardGroup.children[0]);
    }

    const layout = getKeyboardLayout(layoutId);
    const is108 = layoutId === '108';
    const isCatFacing = orientation === 'cat';

    // Sync mouse orientation (180° cat-facing vs 0° viewer-facing)
    this.mouseShape.rotation.y = isCatFacing ? -0.10 : Math.PI - 0.10;

    const U = is108 ? 0.122 : 2.25 / layout.totalUnits; // retain the compact desk footprint
    const CAP = U * 0.87;
    const W = layout.totalUnits * U + 0.14;
    const D = layout.totalRows * U + 0.14;
    this.boardWidth = W;
    this.boardH = 0.112;
    this.capH = is108 ? 0.048 : 0.056;

    this.boardGroup.position.set(is108 ? 0.24 : 0.24, 0.015, 1.08);
    this.mouseHome.set(is108 ? -1.46 : -1.16, 0.015, 0.96);

    // Soft grounded desk shadow under keyboard (replaces KeyCat white sticker halo!)
    const kbShadow = new THREE.Mesh(
      new THREE.PlaneGeometry(W * 1.18, D * 1.38),
      new THREE.MeshBasicMaterial({ map: this.shadowTex, transparent: true, depthWrite: false, opacity: 0.72 }),
    );
    kbShadow.rotation.x = -Math.PI / 2;
    kbShadow.position.set(0, 0.002, 0.025);

    // Ivory chassis with a recessed plate and a shaded lower edge.
    const baseChassis = makeRoundedSlab(W, D, this.boardH, 0.068, keyboardCase.edge, 0);
    const topBezel = makeRoundedSlab(W - 0.014, D - 0.014, 0.014, 0.060, keyboardCase.rim, this.boardH - 0.008);
    const plate = makeRoundedSlab(W - 0.062, D - 0.062, 0.008, 0.044, keyboardCase.bed, this.boardH + 0.004);
    this.boardGroup.add(kbShadow, baseChassis, topBezel, plate);

    for (const spec of layout.keys) {
      const rY = spec.rowY ?? spec.row;
      const rSpan = spec.rowSpan ?? 1;
      const uCenter = spec.uStart + spec.uWidth * 0.5;
      const rCenter = rY + rSpan * 0.5;

      const screenU = isCatFacing ? layout.totalUnits - uCenter : uCenter;
      const screenR = isCatFacing ? layout.totalRows - rCenter : rCenter;

      const x = (screenU - layout.totalUnits * 0.5) * U;
      const z = (screenR - layout.totalRows * 0.5) * U;
      const finish = keyRows[spec.row];
      const baseColor = new THREE.Color(finish.top);
      const topMat = new THREE.MeshBasicMaterial({ color: baseColor });
      const sideMat = new THREE.MeshBasicMaterial({
        color: finish.side, map: makeFrontPrint(frontLegend(spec), isCatFacing, spec.uWidth),
      });

      const cap = new THREE.Mesh(this.capGeo, [sideMat, topMat, this.capBottomMat]);
      cap.scale.set(
        Math.max(0.06, spec.uWidth * U - (U - CAP)),
        this.capH,
        Math.max(0.06, rSpan * U - (U - CAP)),
      );

      const holder = new THREE.Group();
      holder.position.set(x, this.boardH + 0.008, z);
      holder.add(cap);
      this.boardGroup.add(holder);

      this.keys.set(spec.id, {
        spec,
        holder,
        topMat,
        baseColor,
        x,
        z,
        down: false,
        depth: 0,
        glow: 0,
      });
    }

    // Privacy dark frosted shield over the 3D keyboard
    const pCanvas = document.createElement('canvas');
    pCanvas.width = 512;
    pCanvas.height = 160;
    const pg = pCanvas.getContext('2d')!;
    pg.fillStyle = 'rgba(15, 20, 32, 0.88)';
    pg.fillRect(0, 0, 512, 160);
    pg.strokeStyle = 'rgba(244, 114, 182, 0.65)';
    pg.lineWidth = 6;
    pg.strokeRect(6, 6, 500, 148);
    pg.font = 'bold 34px "Segoe UI", "PingFang SC", sans-serif';
    pg.fillStyle = '#fbcfe8';
    pg.textAlign = 'center';
    pg.textBaseline = 'middle';
    pg.fillText('🔒 密码防偷窥 · 已隐藏按键', 256, 80);
    const pTex = new THREE.CanvasTexture(pCanvas);
    pTex.colorSpace = THREE.SRGBColorSpace;
    this.privacyMat = new THREE.MeshBasicMaterial({
      map: pTex,
      transparent: true,
      opacity: 0,
      depthTest: false,
    });
    this.privacyPlate = new THREE.Mesh(new THREE.PlaneGeometry(W - 0.08, D - 0.08), this.privacyMat);
    this.privacyPlate.rotation.x = -Math.PI / 2;
    this.privacyPlate.position.set(0, this.boardH + this.capH + 0.025, 0);
    this.privacyPlate.renderOrder = 30;
    this.privacyPlate.visible = false;
    this.boardGroup.add(this.privacyPlate);
  }

  public getLayoutId(): KeyboardLayoutId {
    return this.layoutId;
  }

  public getOrientation(): KeyboardOrientation {
    return this.orientation;
  }

  public getBoardWidth(): number {
    return this.boardWidth;
  }

  public resolveKey(vk: number): KeyEntry3D | null {
    const spec = resolveKeyByVk(vk, this.layoutId);
    if (!spec) return null;
    return this.keys.get(spec.id) || null;
  }

  public getKeyById(id: string): KeyEntry3D | null {
    return this.keys.get(id) || null;
  }

  public setKeyDown(id: string, down: boolean): void {
    const k = this.keys.get(id);
    if (k) k.down = down;
  }

  public releaseAllKeys(): void {
    for (const k of this.keys.values()) k.down = false;
  }

  public keyTopWorld(id: string, out = new THREE.Vector3()): THREE.Vector3 {
    const k = this.keys.get(id);
    this.boardGroup.updateMatrixWorld(true);
    if (!k) return out.set(0.24, this.boardH + this.capH, 1.08);
    return out
      .set(k.x, this.boardH + 0.008 + this.capH - k.depth, k.z)
      .applyMatrix4(this.boardGroup.matrixWorld);
  }

  public isRightEdgeTailKey(id: string): boolean {
    const k = this.keys.get(id);
    if (!k) return false;
    return k.x >= this.boardWidth * 0.22;
  }

  public setMouseNormalized(nx: number, ny: number): void {
    this.mouseTarget.set((nx - 0.5) * 0.22, 0, (ny - 0.5) * 0.14);
  }

  public pulseScrollWheel(): void {
    this.wheelGlow = 1;
  }

  public mouseTopWorld(out = new THREE.Vector3()): THREE.Vector3 {
    this.mouseGroup.updateMatrixWorld(true);
    return out.set(0, 0.115, -0.05).applyMatrix4(this.mouseShape.matrixWorld);
  }

  public update(
    dt: number,
    leftDown: boolean,
    rightDown: boolean,
    deskHopY: number,
    privacyAlpha: number,
  ): void {
    this.deskGroup.position.y = deskHopY;

    for (const k of this.keys.values()) {
      const targetDepth = k.down ? 0.032 : 0;
      k.depth += (targetDepth - k.depth) * approach(k.down ? 62 : 24, dt);
      k.glow += ((k.down ? 1 : 0) - k.glow) * approach(k.down ? 44 : 6.5, dt);
      k.holder.position.y = this.boardH + 0.008 - k.depth;
      k.topMat.color.copy(k.baseColor).lerp(this.hitColor, k.glow * 0.90);
    }

    if (this.privacyPlate && this.privacyMat) {
      this.privacyPlate.visible = privacyAlpha > 0.02;
      this.privacyMat.opacity = privacyAlpha;
    }

    this.mouseTarget.multiplyScalar(1 - approach(1.6, dt));
    this.mouseOffset.copy(this.mouseFollow.step(this.mouseTarget, dt));
    this.mouseGroup.position.copy(this.mouseHome).add(this.mouseOffset);

    this.leftPress += ((leftDown ? 1 : 0) - this.leftPress) * approach(32, dt);
    this.rightPress += ((rightDown ? 1 : 0) - this.rightPress) * approach(32, dt);
    this.wheelGlow = Math.max(0, this.wheelGlow - dt * 3.8);

    // Since mouseShape already rotates 180° when switching cat/viewer orientation, L plate is always LMB!
    this.leftBtnMat.opacity = 0.88 * this.leftPress;
    this.rightBtnMat.opacity = 0.88 * this.rightPress;
    this.wheelMat.color.copy(this.hitColor);
    this.wheelMat.opacity = .84 * this.wheelGlow;

    const anyPress = Math.max(this.leftPress, this.rightPress);
    this.mouseShape.scale.set(1 + 0.03 * anyPress, 1 - 0.10 * anyPress, 1);
  }
}
