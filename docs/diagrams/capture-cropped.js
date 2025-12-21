/**
 * HTML 다이어그램 캡처 스크립트 (크롭 + 18cm 고정)
 *
 * Issue #8: HTML 다이어그램 캡처 시 불필요한 여백 포함 및 크기 미지정
 *
 * 기능:
 * - SVG 영역만 정확히 크롭
 * - 가로 크기 680px (18cm @96dpi) 고정
 * - 최소 여백 (10px)
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// 18cm = 680px @96dpi
const TARGET_WIDTH = 680;
const PADDING = 10;

const DIAGRAMS = [
    { file: '01-two-track-strategy.html', output: '01-two-track-strategy.png' },
    { file: '02-content-pipeline.html', output: '02-content-pipeline.png' },
    { file: '03-conversion-funnel.html', output: '03-conversion-funnel.png' },
    { file: '04-calendar-2025.html', output: '04-calendar-2025.png' },
    { file: '05-hand-skip.html', output: '05-hand-skip.png' },
    { file: '06-roadmap.html', output: '06-roadmap.png' },
    { file: '07-ggp-dependency.html', output: '07-ggp-dependency.png' },
];

async function captureDiagram(page, htmlPath, outputPath) {
    // HTML 파일 로드
    await page.goto(`file://${htmlPath}`);

    // Mermaid 렌더링 대기
    await page.waitForSelector('.mermaid svg', { timeout: 10000 });
    await page.waitForTimeout(500); // 추가 렌더링 대기

    // SVG 요소의 실제 크기 가져오기
    const svgBox = await page.evaluate(() => {
        const svg = document.querySelector('.mermaid svg');
        if (!svg) return null;

        const rect = svg.getBoundingClientRect();
        return {
            x: rect.x,
            y: rect.y,
            width: rect.width,
            height: rect.height
        };
    });

    if (!svgBox) {
        console.error(`  ERROR: SVG not found in ${htmlPath}`);
        return false;
    }

    // 스케일 계산 (목표 너비에 맞추기)
    const contentWidth = svgBox.width + (PADDING * 2);
    const scale = TARGET_WIDTH / contentWidth;
    const scaledHeight = Math.ceil((svgBox.height + (PADDING * 2)) * scale);

    // 뷰포트 크기 설정 (스케일 적용)
    await page.setViewportSize({
        width: TARGET_WIDTH,
        height: Math.max(scaledHeight, 200)
    });

    // CSS로 SVG 크기 조정
    await page.evaluate(({ targetWidth, padding }) => {
        const body = document.body;
        body.style.margin = '0';
        body.style.padding = `${padding}px`;
        body.style.background = 'white';
        body.style.display = 'flex';
        body.style.justifyContent = 'center';
        body.style.alignItems = 'flex-start';
        body.style.minHeight = 'auto';

        const mermaidDiv = document.querySelector('.mermaid');
        if (mermaidDiv) {
            mermaidDiv.style.width = `${targetWidth - (padding * 2)}px`;
            mermaidDiv.style.display = 'flex';
            mermaidDiv.style.justifyContent = 'center';
        }

        const svg = document.querySelector('.mermaid svg');
        if (svg) {
            svg.style.maxWidth = '100%';
            svg.style.height = 'auto';
        }
    }, { targetWidth: TARGET_WIDTH, padding: PADDING });

    // 다시 크기 측정
    await page.waitForTimeout(300);

    const finalBox = await page.evaluate(() => {
        const svg = document.querySelector('.mermaid svg');
        if (!svg) return null;
        const rect = svg.getBoundingClientRect();
        return {
            width: rect.width,
            height: rect.height
        };
    });

    // 최종 뷰포트 높이 조정
    const finalHeight = Math.ceil(finalBox.height + (PADDING * 2));
    await page.setViewportSize({
        width: TARGET_WIDTH,
        height: finalHeight
    });

    // 스크린샷 캡처 (전체 페이지 - 이제 딱 맞는 크기)
    await page.screenshot({
        path: outputPath,
        clip: {
            x: 0,
            y: 0,
            width: TARGET_WIDTH,
            height: finalHeight
        }
    });

    return { width: TARGET_WIDTH, height: finalHeight };
}

async function main() {
    console.log('=' .repeat(60));
    console.log('HTML 다이어그램 캡처 (크롭 + 18cm 고정)');
    console.log('=' .repeat(60));
    console.log(`Target width: ${TARGET_WIDTH}px (18cm @96dpi)`);
    console.log(`Padding: ${PADDING}px`);
    console.log('');

    const browser = await chromium.launch();
    const page = await browser.newPage();

    const results = [];

    for (const diagram of DIAGRAMS) {
        const htmlPath = path.join(__dirname, diagram.file);
        const outputPath = path.join(__dirname, diagram.output);

        // HTML 파일 존재 확인
        if (!fs.existsSync(htmlPath)) {
            console.log(`  SKIP: ${diagram.file} (not found)`);
            continue;
        }

        console.log(`Capturing: ${diagram.file}`);

        try {
            const size = await captureDiagram(page, htmlPath, outputPath);
            if (size) {
                console.log(`  OK: ${diagram.output} (${size.width}x${size.height})`);
                results.push({ name: diagram.output, ...size, status: 'OK' });
            } else {
                results.push({ name: diagram.output, status: 'FAILED' });
            }
        } catch (error) {
            console.log(`  ERROR: ${error.message}`);
            results.push({ name: diagram.output, status: 'ERROR', error: error.message });
        }
    }

    await browser.close();

    // 결과 요약
    console.log('');
    console.log('=' .repeat(60));
    console.log('결과 요약');
    console.log('=' .repeat(60));

    const success = results.filter(r => r.status === 'OK').length;
    const failed = results.length - success;

    console.log(`성공: ${success}/${results.length}`);
    if (failed > 0) {
        console.log(`실패: ${failed}`);
        results.filter(r => r.status !== 'OK').forEach(r => {
            console.log(`  - ${r.name}: ${r.status}`);
        });
    }

    console.log('');
    console.log('캡처된 이미지:');
    results.filter(r => r.status === 'OK').forEach(r => {
        console.log(`  ${r.name}: ${r.width}x${r.height}px`);
    });
}

main().catch(console.error);
