/**
 * Mermaid 다이어그램을 PNG 이미지로 변환하는 스크립트
 * Usage: node capture_mermaid_diagrams.js
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const DIAGRAMS = [
  {
    name: '01-mindmap-core-metrics',
    code: `mindmap
  root((WSOPTV))
    18TB+ 아카이브
      50년 역사
      1973~현재
    80+ 브레이슬릿
      연간 콘텐츠
      세계 최대
    10,000명+
      메인 이벤트
      2024 기준
    $12.1M
      최대 우승상금
      2023`
  },
  {
    name: '02-xychart-bracelet-legends',
    code: `xychart-beta
    title "역대 브레이슬릿 레전드"
    x-axis ["Phil Hellmuth", "Phil Ivey", "Doyle Brunson", "Johnny Chan", "Daniel Negreanu"]
    y-axis "브레이슬릿 개수" 0 --> 20
    bar [17, 11, 10, 10, 7]`
  },
  {
    name: '03-journey-moneymaker',
    code: `journey
    title Chris Moneymaker의 여정 (2003)
    section 온라인 예선
      $86 위성 토너먼트: 3: Moneymaker
      예선 통과: 5: Moneymaker
    section WSOP 메인 이벤트
      $10K 시드 획득: 5: Moneymaker
      839명 중 생존: 7: Moneymaker
      파이널 테이블: 8: Moneymaker
    section 우승
      $2.5M 우승: 10: Moneymaker
      포커 붐 촉발: 10: Poker Industry`
  },
  {
    name: '04-xychart-participants',
    code: `xychart-beta
    title "WSOP 메인 이벤트 참가자 추이 (Moneymaker Effect)"
    x-axis [2003, 2006, 2010, 2015, 2020, 2024]
    y-axis "참가자 수" 0 --> 12000
    bar [839, 8773, 7319, 6420, 0, 10117]`
  },
  {
    name: '05-pie-content-composition',
    code: `pie showData
    title WSOPTV 콘텐츠 구성
    "WSOP Las Vegas" : 80
    "기타 대회" : 10
    "오리지널 콘텐츠" : 10`
  },
  {
    name: '06-pie-wsop-lv-content',
    code: `pie showData
    title WSOP Las Vegas 콘텐츠 비중
    "Main Event" : 35
    "Bracelet Events" : 30
    "Best Hands 큐레이션" : 15
    "Classics (역대 명경기)" : 5
    "기타" : 15`
  },
  {
    name: '07-flowchart-main-event',
    code: `flowchart LR
    subgraph Day1["Day 1 (8,000~10,000명)"]
        D1A["1A"]
        D1B["1B"]
        D1C["1C"]
    end

    D1A --> D2["Day 2-5<br/>(필드 압축)"]
    D1B --> D2
    D1C --> D2
    D2 --> FT["Final Table<br/>(9명)"]
    FT --> CHAMP["🏆 Champion"]

    style CHAMP fill:#ffd700,stroke:#b8860b,stroke-width:3px`
  },
  {
    name: '08-flowchart-bracelet-events',
    code: `flowchart TB
    WSOP["🎰 WSOP Las Vegas<br/>80+ Bracelet Events"]

    WSOP --> NLH["♠️ No-Limit Hold'em"]
    WSOP --> PLO["♦️ Pot-Limit Omaha"]
    WSOP --> MIX["♣️ Mixed Games"]
    WSOP --> SP["♥️ Special Events"]

    NLH --> NLH1["$1,500 NLH"]
    NLH --> NLH2["$3,000 NLH"]
    NLH --> NLH3["$5,000 NLH"]

    PLO --> PLO1["$1,500 PLO"]
    PLO --> PLO2["$10K PLO Championship"]

    MIX --> MIX1["$50K PPC"]
    MIX --> MIX2["HORSE"]

    SP --> SP1["Ladies"]
    SP --> SP2["Seniors"]
    SP --> SP3["Tag Team"]`
  },
  {
    name: '09-flowchart-best-hands',
    code: `flowchart LR
    subgraph BH["🎬 Best Hands 컬렉션"]
        direction TB
        A["All-in Showdowns<br/>올인 런아웃 드라마"]
        B["Bluff Catches<br/>블러프 잡아내기"]
        C["Hero Calls/Folds<br/>역사적 명장면"]
        D["Monster Pots<br/>$500K+ 거액 팟"]
    end`
  },
  {
    name: '10-flowchart-other-events',
    code: `flowchart LR
    subgraph OTHER["🌍 기타 WSOP 대회"]
        direction TB
        PAR["🏝️ WSOP Paradise<br/>12월, 바하마<br/>$25K Buy-in"]
        EUR["🇪🇺 WSOP Europe<br/>4월, 유럽<br/>유럽 메이저"]
        CIR["🌐 Super Circuit<br/>연중, 전세계<br/>Cyprus, Canada"]
    end`
  },
  {
    name: '11-flowchart-youtube-vs-wsoptv',
    code: `flowchart LR
    subgraph YT["📺 YouTube (무료)"]
        direction TB
        Y1["🔴 생방송"]
        Y2["📱 쇼츠/클립"]
        Y3["🎯 관심 유도"]
    end

    subgraph WS["🎬 WSOPTV (구독)"]
        direction TB
        W1["📺 풀 에피소드"]
        W2["⏭️ Hand Skip"]
        W3["🏆 Best Hands"]
        W4["📀 4K Remaster"]
    end

    YT -->|"전환"| WS

    style WS fill:#1a1a2e,stroke:#ffd700,stroke-width:2px
    style YT fill:#ff0000,stroke:#cc0000,stroke-width:2px`
  },
  {
    name: '12-flowchart-exclusive-features',
    code: `flowchart TB
    subgraph FEATURES["⭐ WSOPTV 독점 기능"]
        direction LR

        subgraph HS["⏭️ Hand Skip"]
            HS1["3시간 에피소드"]
            HS2["45분 액션만"]
        end

        subgraph BH["🏆 Best Hands"]
            BH1["50년 역사"]
            BH2["극적인 순간"]
        end

        subgraph REM["📀 4K Remaster"]
            REM1["1973-2010 클래식"]
            REM2["AI 업스케일링"]
        end
    end`
  },
  {
    name: '13-pie-best-hands-criteria',
    code: `pie showData
    title Best Hands 선정 기준
    "Pot Size" : 25
    "Drama" : 25
    "Skill Display" : 20
    "Player Fame" : 15
    "Outcome" : 15`
  },
  {
    name: '14-gantt-annual-calendar',
    code: `gantt
    title WSOP 연간 시즌 캘린더
    dateFormat  YYYY-MM
    axisFormat %b

    section Q1
    Super Circuit Cyprus    :2025-03, 1M

    section Q2
    WSOP Europe            :2025-04, 1M
    WSOP Las Vegas (80%)   :crit, 2025-05, 3M

    section Q3
    (비시즌)               :2025-08, 2M

    section Q4
    Super Circuit Canada   :2025-10, 1M
    WSOP Paradise          :2025-12, 1M`
  },
  {
    name: '15-timeline-global-expansion',
    code: `timeline
    title WSOP 글로벌 확장 로드맵
    2025 : Las Vegas (Core)
         : Europe, Paradise, Circuit
    2026 : WSOP Asia 런칭
         : WSOP Brazil 런칭
    2027 : WSOP India 런칭
         : 글로벌 확장 완료`
  },
  {
    name: '16-timeline-service-evolution',
    code: `timeline
    title WSOPTV 서비스 진화 로드맵
    section Phase 1 - MVP
        전체 볼륨 OTT : 서비스 런칭
        이어보기 : 기본 기능
    section Phase 2 - 개인화
        프로필 추천 : 시청 이력 기반
        카테고리 추천 : 플레이어/이벤트별
    section Phase 3 - 차별화
        Hand Skip : 핵심 핸드만 시청
        Best Hands : 큐레이션 컬렉션
    section Phase 4 - 프리미엄
        4K Remaster : AI 업스케일링
        독점 다큐 : 오리지널 시리즈`
  },
  {
    name: '17-quadrant-feature-phases',
    code: `quadrantChart
    title 기능별 Phase 도입 시점
    x-axis 초기 도입 --> 후기 도입
    y-axis 기본 기능 --> 프리미엄 기능
    quadrant-1 Phase 4 (프리미엄)
    quadrant-2 Phase 3 (차별화)
    quadrant-3 Phase 1 (MVP)
    quadrant-4 Phase 2 (개인화)
    "전체 볼륨 OTT": [0.1, 0.2]
    "이어보기": [0.2, 0.3]
    "프로필 추천": [0.4, 0.4]
    "카테고리 추천": [0.5, 0.5]
    "Hand Skip": [0.6, 0.7]
    "Best Hands": [0.7, 0.75]
    "4K Remaster": [0.9, 0.9]`
  },
  {
    name: '18-timeline-archive-eras',
    code: `timeline
    title WSOP 아카이브 시대 구분
    section CLASSIC (1973-2002)
        포커 초창기 : SD 화질
        전설의 탄생 : 희귀 영상
    section BOOM (2003-2010)
        Moneymaker Effect : 포커 황금기
        산업 혁명 : 온라인 포커 폭발
    section HD (2011-2025)
        HD/4K 시대 : 현대 포커
        고화질 풀 에피소드 : 프로 수준 제작
    section WSOPTV (2026~)
        오리지널 콘텐츠 : 독점 다큐멘터리
        WSOPTV 시대 : 플랫폼 시대`
  }
];

async function generateMermaidImage(diagram, outputDir) {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({
      startOnLoad: true,
      theme: 'default',
      fontFamily: 'Malgun Gothic, sans-serif'
    });
  </script>
  <style>
    body {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
      padding: 40px;
      background: white;
      box-sizing: border-box;
    }
    .mermaid {
      max-width: 100%;
    }
  </style>
</head>
<body>
  <pre class="mermaid">
${diagram.code}
  </pre>
</body>
</html>`;

  await page.setContent(html);
  await page.waitForTimeout(3000); // Mermaid 렌더링 대기

  const element = await page.$('.mermaid');
  if (element) {
    const outputPath = path.join(outputDir, `${diagram.name}.png`);
    await element.screenshot({ path: outputPath, scale: 'css' });
    console.log(`Generated: ${outputPath}`);
  } else {
    console.error(`Failed to render: ${diagram.name}`);
  }

  await browser.close();
}

async function main() {
  const outputDir = path.join(__dirname, '..', 'tasks', 'prds', '0010-prd-wsoptv', 'images');

  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  console.log(`Output directory: ${outputDir}`);
  console.log(`Total diagrams: ${DIAGRAMS.length}`);

  for (const diagram of DIAGRAMS) {
    try {
      await generateMermaidImage(diagram, outputDir);
    } catch (error) {
      console.error(`Error processing ${diagram.name}:`, error.message);
    }
  }

  console.log('Done!');
}

main().catch(console.error);
