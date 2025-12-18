const { chromium } = require('@playwright/test');
const path = require('path');

const sections = [
  '01-header',
  '02-hero-banner',
  '03-continue-watching',
  '04-recently-added',
  '05-series-section',
  '06-footer'
];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  for (const section of sections) {
    const htmlPath = path.join('D:', 'AI', 'claude01', 'wsoptv_v2', 'docs', 'wireframes', 'v2', `${section}.html`);
    const pngPath = path.join('D:', 'AI', 'claude01', 'wsoptv_v2', 'docs', 'wireframes', 'v2', `${section}.png`);

    await page.goto(`file:///${htmlPath.replace(/\\/g, '/')}`);
    await page.waitForLoadState('networkidle');

    // Capture only the .capture-area element
    const element = await page.locator('.capture-area');
    await element.screenshot({ path: pngPath });

    console.log(`Captured: ${section}.png`);
  }

  await browser.close();
  console.log('\nAll screenshots completed!');
})();
