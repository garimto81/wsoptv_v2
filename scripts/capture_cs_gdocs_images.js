/**
 * Capture Content Strategy diagrams for Google Docs
 * Usage: cd frontend && node ../scripts/capture_cs_gdocs_images.js
 */
const { chromium } = require('@playwright/test');
const path = require('path');

const wireframeDir = path.join(__dirname, '..', 'docs', 'wireframes', 'v2');

const diagrams = [
    { file: 'cs-content-composition.html', output: 'cs-content-composition.png' },
    { file: 'cs-youtube-vs-wsoptv.html', output: 'cs-youtube-vs-wsoptv.png' },
    { file: 'cs-season-calendar.html', output: 'cs-season-calendar.png' }
];

(async () => {
    console.log('Starting Content Strategy Google Docs image capture...\n');

    const browser = await chromium.launch();
    const page = await browser.newPage({
        viewport: { width: 1200, height: 800 }
    });

    for (const diagram of diagrams) {
        const htmlPath = path.join(wireframeDir, diagram.file);
        const pngPath = path.join(wireframeDir, diagram.output);

        try {
            console.log(`Loading: ${diagram.file}`);
            await page.goto(`file:///${htmlPath.replace(/\\/g, '/')}`);

            // Wait for styles to render
            await page.waitForTimeout(1000);

            // Capture the container element
            const container = await page.locator('.container');
            await container.screenshot({ path: pngPath });

            console.log(`  -> Captured: ${diagram.output}`);
        } catch (err) {
            console.error(`  -> Failed: ${diagram.file} - ${err.message}`);
        }
    }

    await browser.close();
    console.log('\nAll Content Strategy images captured!');
    console.log(`Output directory: ${wireframeDir}`);
})();
