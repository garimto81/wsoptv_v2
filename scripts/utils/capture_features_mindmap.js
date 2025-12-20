const { chromium } = require('@playwright/test');
const path = require('path');

const wireframeDir = path.join(__dirname, '..', 'docs', 'wireframes', 'v2');

(async () => {
    console.log('Launching browser...');
    const browser = await chromium.launch();
    const page = await browser.newPage({
        viewport: { width: 1200, height: 900 }
    });

    const htmlPath = path.join(wireframeDir, 'features-mindmap.html');
    console.log(`Loading: ${htmlPath}`);
    await page.goto(`file:///${htmlPath.replace(/\\/g, '/')}`);

    // Wait for Mermaid to render
    console.log('Waiting for Mermaid to render...');
    await page.waitForTimeout(3000);

    // Screenshot the entire page
    const pngPath = path.join(wireframeDir, 'features-mindmap.png');
    await page.screenshot({
        path: pngPath,
        fullPage: true
    });
    console.log(`Captured: features-mindmap.png`);

    await browser.close();
    console.log('Done!');
})();
