/**
 * Capture Content Strategy Mermaid Diagrams as PNG images
 * Usage: node scripts/capture_content_strategy.js
 */
// Run from frontend folder: cd frontend && node ../scripts/capture_content_strategy.js
const { chromium } = require('@playwright/test');
const path = require('path');

const wireframeDir = path.join(__dirname, '..', 'docs', 'wireframes', 'v2');

const diagrams = [
    { id: 'cs-diagram1', name: 'cs-core-content' },
    { id: 'cs-diagram-pie', name: 'cs-content-pie' },
    { id: 'cs-diagram2', name: 'cs-content-detail' },
    { id: 'cs-diagram3', name: 'cs-bracelet-structure' },
    { id: 'cs-diagram4', name: 'cs-main-event' },
    { id: 'cs-diagram5', name: 'cs-other-events' },
    { id: 'cs-diagram6', name: 'cs-youtube-wsoptv' },
    { id: 'cs-diagram7', name: 'cs-curation-roadmap' },
    { id: 'cs-diagram8', name: 'cs-season-calendar' }
];

(async () => {
    console.log('Starting Content Strategy diagram capture...');

    const browser = await chromium.launch();
    const page = await browser.newPage();

    const htmlPath = path.join(wireframeDir, 'content-strategy-diagrams.html');
    console.log(`Loading: ${htmlPath}`);

    await page.goto(`file:///${htmlPath.replace(/\\/g, '/')}`);

    // Wait for Mermaid to render
    await page.waitForTimeout(3000);

    for (const diagram of diagrams) {
        const pngPath = path.join(wireframeDir, `${diagram.name}.png`);
        try {
            const element = await page.locator(`#${diagram.id}`);
            await element.screenshot({ path: pngPath });
            console.log(`Captured: ${diagram.name}.png`);
        } catch (err) {
            console.error(`Failed to capture ${diagram.name}: ${err.message}`);
        }
    }

    await browser.close();
    console.log('\nAll Content Strategy diagrams captured!');
})();
