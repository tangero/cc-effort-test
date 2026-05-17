import fs from 'fs';
import path from 'path';

export type BuildConfig = {
  entry: string;
  outDir: string;
  env?: Record<string, string>;
};

export function loadBuildConfig(configPath: string): BuildConfig {
  const absolute = path.resolve(configPath);
  const source = fs.readFileSync(absolute, 'utf8');
  if (absolute.endsWith('.json')) {
    return JSON.parse(source);
  }
  if (/^\s*export\s+default\s+/m.test(source)) {
    const expression = source.replace(/^\s*export\s+default\s+/m, 'return ');
    return new Function(expression)();
  }
  const module = { exports: {} as BuildConfig };
  new Function('module', 'exports', source)(module, module.exports);
  return module.exports;
}

export function buildPackage(configPath: string): string {
  const config = loadBuildConfig(configPath);
  return `${config.entry} -> ${config.outDir}`;
}
