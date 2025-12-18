const { chromium } = require('@playwright/test');
const path = require('path');

const wireframeDir = path.join(__dirname, '..', 'docs', 'wireframes', 'v2');

const files = [
  '00-full-page',
  '01-header',
  '02-hero-banner',
  '03-continue-watching',
  '04-recently-added',
  '05-series-section',
  '06-footer',
  '07-navigation',
  '08-content-cards',
  '09-subscription',
  '10-responsive',
  '11-accessibility',
  '12-browse',
  '13-player',
  '14-account',
  '15-auth',
  // Individual card images for section 3
  'card-episode',
  'card-besthand',
  'card-continue',
  'card-badges',
  // Individual images for section 4
  'subscription-paywall',
  'subscription-plans'
];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  for (const file of files) {
    const htmlPath = path.join(wireframeDir, `${file}.html`);
    const pngPath = path.join(wireframeDir, `${file}.png`);

    await page.goto(`file:///${htmlPath.replace(/\\/g, '/')}`);
    await page.waitForLoadState('networkidle');

    const element = await page.locator('.capture-area');
    await element.screenshot({ path: pngPath });

    console.log(`Captured: ${file}.png`);
  }

  await browser.close();
  console.log('\nAll screenshots completed!');
})();
