const { chromium } = require('@playwright/test');
const path = require('path');

const wireframeDir = path.join(__dirname, '..', 'docs', 'wireframes', 'v2');

const diagrams = [
    { id: 'diagram1', name: 'mermaid-youtube-entry' },
    { id: 'diagram2', name: 'mermaid-direct-entry' },
    { id: 'diagram3', name: 'mermaid-existing-user' }
];

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();

    const htmlPath = path.join(wireframeDir, 'mermaid-diagrams.html');
    console.log(`Loading: ${htmlPath}`);
    await page.goto(`file:///${htmlPath.replace(/\\/g, '/')}`);

    // Wait for Mermaid to render
    await page.waitForTimeout(3000);

    for (const diagram of diagrams) {
        const pngPath = path.join(wireframeDir, `${diagram.name}.png`);
        const element = await page.locator(`#${diagram.id}`);
        await element.screenshot({ path: pngPath });
        console.log(`Captured: ${diagram.name}.png`);
    }

    await browser.close();
    console.log('\nAll Mermaid diagrams captured!');
})();
