import fs from 'node:fs';
import { chromium } from 'playwright';

const BASE = (process.argv[2] || 'https://answers.cleansceneinvestigators.com').replace(/\/$/, '');
const sitemap = await (await fetch(`${BASE}/sitemap.xml`)).text();
const urls = [...sitemap.matchAll(/<loc>(.*?)<\/loc>/g)].map(match => match[1].trim());
const issues = [];
const links = new Set();
const badText = /\u00e2\u20ac|\u00c2|\u00f0\u0178/;
const browser = await chromium.launch({ headless: true });

try {
  for (const url of urls) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const runtimeErrors = [];
    page.on('console', msg => { if (msg.type() === 'error') runtimeErrors.push(`console: ${msg.text()}`); });
    page.on('pageerror', error => runtimeErrors.push(`page: ${error.message}`));
    page.on('response', response => {
      if (response.status() >= 400 && new URL(response.url()).hostname === new URL(BASE).hostname) {
        runtimeErrors.push(`resource ${response.status()}: ${response.url()}`);
      }
    });
    const response = await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    if (response?.status() !== 200) issues.push({ severity: 'critical', url, type: 'status', detail: response?.status() });
    const result = await page.evaluate(() => {
      const schemas = [...document.querySelectorAll('script[type="application/ld+json"]')].map(el => el.textContent || '');
      return {
        canonical: document.querySelector('link[rel="canonical"]')?.href || '',
        text: document.documentElement.textContent || '',
        overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
        schemas,
        links: [...document.querySelectorAll('a[href]')].map(el => el.href),
        favicon: document.querySelector('link[rel~="icon"]')?.href || '',
      };
    });
    if (result.canonical !== url) issues.push({ severity: 'high', url, type: 'canonical', detail: result.canonical });
    if (badText.test(result.text) || result.schemas.some(schema => badText.test(schema))) issues.push({ severity: 'high', url, type: 'encoding' });
    if (result.overflow) issues.push({ severity: 'high', url, type: 'desktop-overflow' });
    if (!result.favicon) issues.push({ severity: 'medium', url, type: 'favicon' });
    for (const raw of result.schemas) {
      try {
        const root = JSON.parse(raw);
        const queue = [root];
        while (queue.length) {
          const value = queue.pop();
          if (Array.isArray(value)) queue.push(...value);
          else if (value && typeof value === 'object') {
            const types = Array.isArray(value['@type']) ? value['@type'] : [value['@type']];
            if (types.includes('Article') && !value.image) issues.push({ severity: 'medium', url, type: 'article-image' });
            queue.push(...Object.values(value));
          }
        }
      } catch (error) {
        issues.push({ severity: 'high', url, type: 'schema-json', detail: error.message });
      }
    }
    for (const href of result.links) if (href.startsWith(BASE)) links.add(href.split('#')[0]);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.reload({ waitUntil: 'domcontentloaded' });
    if (await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1)) {
      issues.push({ severity: 'high', url, type: 'mobile-overflow' });
    }
    for (const detail of runtimeErrors) issues.push({ severity: 'medium', url, type: 'runtime', detail });
    await context.close();
  }
  for (const url of links) {
    const response = await fetch(url, { redirect: 'follow' });
    if (!response.ok) issues.push({ severity: 'critical', url, type: 'broken-internal', detail: response.status });
  }
} finally {
  await browser.close();
}

const totals = {
  sitemapUrls: urls.length,
  internalTargets: links.size,
  critical: issues.filter(x => x.severity === 'critical').length,
  high: issues.filter(x => x.severity === 'high').length,
  medium: issues.filter(x => x.severity === 'medium').length,
};
fs.writeFileSync('knowledge-production-audit.json', JSON.stringify({ generatedAt: new Date().toISOString(), totals, issues }, null, 2));
console.log(JSON.stringify(totals, null, 2));
for (const issue of issues) console.log(`[${issue.severity}] ${issue.url} ${issue.type} ${issue.detail || ''}`);
if (urls.length !== 56 || totals.critical || totals.high || totals.medium) process.exitCode = 2;
