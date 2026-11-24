import { defineConfig, normalizePath } from 'vite';
import path from 'node:path';
const project = process.cwd();
const experiment = path.join(project, 'output/whole-kitten-lab');
export default defineConfig({
  root: path.join(project, 'website'), base: '/kurocat/', cacheDir: path.join(experiment, 'vite-cache'),
  server: {host:'127.0.0.1',port:1422,strictPort:true,fs:{allow:[project]}},
  plugins: [{ name:'local-whole-kitten', enforce:'pre', transform(code, id) {
    if (normalizePath(id) !== normalizePath(path.join(project,'src/catEngine.ts'))) return;
    code = code.replace(/\r\n/g, '\n');
    // This photographed kitten has two visible forelegs and no tail sprite.
    code = code.replace("if (this.tailKeyMode === 'off') return false;", "if (this.customSkin?.id === CREAM_KITTEN.id || this.tailKeyMode === 'off') return false;");
    code = code.replace('const clampedTarget = this.clampToKeyboardSurface(targetPoint);', 'const clampedTarget = this.customSkin?.id === CREAM_KITTEN.id ? targetPoint : this.clampToKeyboardSurface(targetPoint);');
    const start=code.indexOf('      // Keep the portrait behind the keybed');
    const end=code.indexOf('\n    } else {\n      this.drawMiniMouse(ctx);',start);
    if (start<0 || end<0) throw Error('Cannot find photo renderer');
    return `import {renderPhotoTrial} from '../output/whole-kitten-lab/trial.js';\n` + code.slice(0,start) + '      renderPhotoTrial(this, ctx, breath);' + code.slice(end);
  }}]
});


