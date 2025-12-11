import { chromium } from '@playwright/test';

async function captureScreenshots() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  // Screenshots directory
  const screenshotDir = './screenshots';

  // Use environment variable or default port
  const PORT = process.env.PORT || 3001;
  const BASE_URL = `http://localhost:${PORT}`;

  console.log(`Connecting to ${BASE_URL}...`);

  // First, login to get access to protected pages
  console.log('Logging in...');
  await page.goto(`${BASE_URL}/login`, { timeout: 60000, waitUntil: 'load' });
  await page.waitForTimeout(2000);

  // Fill login form (default admin credentials)
  await page.fill('input[placeholder="Username"]', 'garimto');
  await page.fill('input[placeholder="Password"]', '1234');
  await page.click('button:has-text("Sign In")');
  await page.waitForTimeout(3000);
  console.log('  ✓ Logged in');

  const pages = [
    { name: 'catalog', path: '/catalog' },
    { name: 'search', path: '/search' },
    { name: 'admin', path: '/admin' },
  ];

  for (let i = 0; i < pages.length; i++) {
    const { name, path } = pages[i];
    const num = String(i + 1).padStart(2, '0');

    try {
      console.log(`Capturing ${name} page...`);
      await page.goto(`${BASE_URL}${path}`, { timeout: 60000, waitUntil: 'load' });
      await page.waitForTimeout(3000); // Wait for React hydration + API calls
      await page.screenshot({ path: `${screenshotDir}/${num}-${name}.png`, fullPage: true });
      console.log(`  ✓ Saved ${num}-${name}.png`);
    } catch (error) {
      console.error(`  ✗ Failed ${name}: ${error.message}`);
      try {
        await page.screenshot({ path: `${screenshotDir}/${num}-${name}-error.png` });
      } catch (e) {}
    }
  }

  console.log(`\nScreenshots saved to ./screenshots/`);
  await browser.close();
}

captureScreenshots();
