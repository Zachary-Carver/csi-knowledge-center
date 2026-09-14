import fs from 'node:fs';
import path from 'node:path';

const ROOT = path.resolve(import.meta.dirname, '..');
const IMAGE = {
  '@type': 'ImageObject',
  url: 'https://answers.cleansceneinvestigators.com/assets/csi-shield-logo.svg',
  contentUrl: 'https://answers.cleansceneinvestigators.com/assets/csi-shield-logo.svg',
  caption: 'CSI: Clean Scene Investigators shield logo',
};
const FAVICON = '<link rel="icon" href="/assets/csi-shield-logo.svg" type="image/svg+xml">';

function files(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === '.git') continue;
    const target = path.join(dir, entry.name);
    if (entry.isDirectory()) files(target, out);
    else if (entry.name.endsWith('.html')) out.push(target);
  }
  return out;
}

let articleCount = 0;
let missingAfter = 0;
function reconcile(value) {
  let changed = false;
  if (Array.isArray(value)) {
    for (const item of value) changed = reconcile(item) || changed;
    return changed;
  }
  if (!value || typeof value !== 'object') return false;
  const types = Array.isArray(value['@type']) ? value['@type'] : [value['@type']];
  if (types.includes('Article')) articleCount++;
  if (types.includes('Article') && !value.image) {
    value.image = IMAGE;
    changed = true;
  }
  for (const item of Object.values(value)) changed = reconcile(item) || changed;
  return changed;
}

let changedFiles = 0;
for (const file of files(ROOT)) {
  let source = fs.readFileSync(file, 'utf8');
  const original = source;
  source = source.replace(/(<script\b[^>]*type=["']application\/ld\+json["'][^>]*>)([\s\S]*?)(<\/script>)/gi,
    (whole, open, body, close) => {
      try {
        const data = JSON.parse(body);
        return reconcile(data) ? open + JSON.stringify(data) + close : whole;
      } catch {
        return whole;
      }
    });
  if (!/<link\b[^>]*rel=["'][^"']*icon/i.test(source)) {
    source = source.replace('</head>', FAVICON + '</head>');
  }
  if (source !== original) {
    fs.writeFileSync(file, source);
    changedFiles++;
  }
}
console.log(`Reconciled Article images and favicon in ${changedFiles} files`);
for (const file of files(ROOT)) {
  const source = fs.readFileSync(file, 'utf8');
  source.replace(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi, (_whole, body) => {
    try {
      const queue = [JSON.parse(body)];
      while (queue.length) {
        const value = queue.pop();
        if (Array.isArray(value)) queue.push(...value);
        else if (value && typeof value === 'object') {
          const types = Array.isArray(value['@type']) ? value['@type'] : [value['@type']];
          if (types.includes('Article') && !value.image) missingAfter++;
          queue.push(...Object.values(value));
        }
      }
    } catch {}
    return _whole;
  });
}
console.log(`Article entities: ${articleCount}; missing images after reconciliation: ${missingAfter}`);
if (missingAfter) process.exitCode = 2;
