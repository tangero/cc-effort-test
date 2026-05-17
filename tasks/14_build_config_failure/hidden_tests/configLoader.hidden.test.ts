import fs from 'fs';
import os from 'os';
import path from 'path';
import { buildPackage, loadBuildConfig } from '../configLoader';

describe('workspace build config compatibility', () => {
  test('loads ESM-style default config without requiring package-wide type module', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cfg-'));
    const configPath = path.join(dir, 'build.config.js');
    fs.writeFileSync(
      configPath,
      "export default { entry: 'packages/web/src/index.ts', outDir: 'packages/web/dist' }"
    );

    expect(buildPackage(configPath)).toBe('packages/web/src/index.ts -> packages/web/dist');
  });

  test('keeps CommonJS configs working after adding ESM support', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cfg-'));
    const configPath = path.join(dir, 'build.config.cjs');
    fs.writeFileSync(configPath, "module.exports = { entry: 'api/index.ts', outDir: 'api/dist' }");

    expect(loadBuildConfig(configPath)).toEqual({ entry: 'api/index.ts', outDir: 'api/dist' });
  });

  test('loads JSON configs for older packages', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cfg-'));
    const configPath = path.join(dir, 'build.config.json');
    fs.writeFileSync(configPath, JSON.stringify({ entry: 'worker.ts', outDir: 'build' }));

    expect(buildPackage(configPath)).toBe('worker.ts -> build');
  });
});
