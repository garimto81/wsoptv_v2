const { chromium } = require('@playwright/test');
const path = require('path');

const baseDir = path.join('D:', 'AI', 'claude01', 'wsoptv_v2', 'docs', 'wireframes', 'v2');

const captures = [
  {
    html: 'nav-sitemap.html',
    png: 'nav-sitemap.png',
    selector: '.mermaid',
    fullPage: false,
    viewport: { width: 600, height: 500 }
  }
];

(async () => {
  const browser = await chromium.launch();

  for (const capture of captures) {
    const page = await browser.newPage();
    await page.setViewportSize(capture.viewport);

    const htmlPath = path.join(baseDir, capture.html);
    const pngPath = path.join(baseDir, capture.png);

    console.log(`Loading: ${capture.html}`);
    await page.goto(`file:///${htmlPath.replace(/\\/g, '/')}`);

    // Wait for Mermaid diagrams to render
    await page.waitForTimeout(2000);
    await page.waitForLoadState('networkidle');

    if (capture.fullPage) {
      await page.screenshot({ path: pngPath, fullPage: true });
    } else if (capture.selector) {
      const element = await page.locator(capture.selector).first();
      await element.screenshot({ path: pngPath });
    }

    console.log(`Captured: ${capture.png}`);
    await page.close();
  }

  await browser.close();
  console.log('\nNavigation map screenshots completed!');
})();
