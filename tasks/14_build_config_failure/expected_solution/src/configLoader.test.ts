import fs from 'fs';
import os from 'os';
import path from 'path';
import { buildPackage } from './configLoader';

test('builds packages with CommonJS config', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cfg-'));
  const configPath = path.join(dir, 'build.config.cjs');
  fs.writeFileSync(configPath, "module.exports = { entry: 'src/index.ts', outDir: 'dist' }");

  expect(buildPackage(configPath)).toBe('src/index.ts -> dist');
});
