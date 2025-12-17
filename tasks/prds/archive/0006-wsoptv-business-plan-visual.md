# WSOPTV 사업 기획서

**포커 전문 OTT 스트리밍 서비스**

| 항목 | 내용 |
|------|------|
| 버전 | 1.0 |
| 작성일 | 2024년 12월 15일 |
| 대상 | 경영진, 투자자 |

---

## 1. Executive Summary

```mermaid
flowchart TB
    subgraph Summary["📋 한눈에 보기"]
        direction TB

        Vision["🎯 비전<br/>━━━━━━━━━━━━━━━━━━<br/>국내 1위 포커 전문 OTT<br/>스트리밍 플랫폼 구축"]

        subgraph Numbers["📊 핵심 지표"]
            direction LR
            N1["💹 시장 규모<br/>━━━━━━━━<br/>₩2,000억+<br/>(국내 홀덤)"]
            N2["💰 3년차 매출<br/>━━━━━━━━<br/>₩36억/년<br/>(목표)"]
            N3["📈 손익분기<br/>━━━━━━━━<br/>18개월<br/>(BEP)"]
        end

        subgraph Diff["💡 핵심 차별점"]
            direction LR
            D1["🏆 국내 유일<br/>━━━━━━━━<br/>포커 전문<br/>OTT 서비스"]
            D2["💵 가격 경쟁력<br/>━━━━━━━━<br/>₩9,900/월<br/>(60% 저렴)"]
            D3["📚 콘텐츠<br/>━━━━━━━━<br/>18TB+<br/>500편 이상"]
        end

        Vision --> Numbers
        Numbers --> Diff
    end
```

---

## 2. 시장 기회

### 2.1 시장 성장 추이

```mermaid
xychart-beta
    title "글로벌 포커 시장 성장 (조원)"
    x-axis ["2021", "2023", "2025E", "2028E"]
    y-axis "시장규모" 0 --> 200
    bar [50, 80, 120, 180]
    line [50, 80, 120, 180]
```

### 2.2 문제점 → 해결책

```mermaid
flowchart TB
    subgraph Problem["❌ 현재 시장의 문제점"]
        direction TB
        P1["📺 콘텐츠 분산<br/>━━━━━━━━━━━━━━<br/>포커 영상이 YouTube에<br/>산발적으로 흩어져 있음"]
        P2["💸 높은 가격<br/>━━━━━━━━━━━━━━<br/>해외 OTT PokerGO<br/>월 $15 (약 ₩20,000)"]
        P3["🌏 언어 장벽<br/>━━━━━━━━━━━━━━<br/>한글 자막/해설 없음<br/>영어만 지원"]
        P4["📉 낮은 품질<br/>━━━━━━━━━━━━━━<br/>끊김, 저화질<br/>불편한 UX"]
    end

    subgraph Solution["✅ WSOPTV 해결책"]
        direction TB
        S1["📁 체계적 정리<br/>━━━━━━━━━━━━━━<br/>시리즈별, 연도별<br/>카탈로그 구축"]
        S2["💰 합리적 가격<br/>━━━━━━━━━━━━━━<br/>₩9,900/월<br/>50% 이상 저렴"]
        S3["🇰🇷 한국어 지원<br/>━━━━━━━━━━━━━━<br/>한글 자막 제공<br/>한국어 해설"]
        S4["🎬 고품질 제공<br/>━━━━━━━━━━━━━━<br/>4K UHD 스트리밍<br/>끊김 없는 재생"]
    end

    P1 --> S1
    P2 --> S2
    P3 --> S3
    P4 --> S4
```

---

## 3. 비즈니스 모델

### 3.1 수익 구조 (3년차)

```mermaid
pie showData
    title "수익원 구성 비율"
    "Premium 구독 (45%)" : 45
    "VIP 구독 (25%)" : 25
    "Basic 구독 (15%)" : 15
    "라이브 이벤트 (10%)" : 10
    "광고 수익 (5%)" : 5
```

### 3.2 구독 플랜 체계

```mermaid
flowchart TB
    subgraph Plans["💳 구독 플랜 비교"]
        direction TB

        subgraph Free["🆓 무료 플랜"]
            F1["월 ₩0<br/>━━━━━━━━━━━━<br/>• 콘텐츠: 50편<br/>• 화질: 720p<br/>• 디바이스: 1대<br/>• 광고: 있음"]
        end

        subgraph Basic["📦 Basic 플랜"]
            B1["월 ₩5,900<br/>━━━━━━━━━━━━<br/>• 콘텐츠: 300편<br/>• 화질: 1080p<br/>• 디바이스: 2대<br/>• 광고: 없음"]
        end

        subgraph Premium["⭐ Premium 플랜"]
            P1["월 ₩9,900<br/>━━━━━━━━━━━━<br/>• 콘텐츠: 전체<br/>• 화질: 4K UHD<br/>• 디바이스: 4대<br/>• 다운로드: 20편"]
        end

        subgraph VIP["👑 VIP 플랜"]
            V1["월 ₩19,900<br/>━━━━━━━━━━━━<br/>• 콘텐츠: 전체+독점<br/>• 화질: 4K HDR<br/>• 디바이스: 6대<br/>• 라이브: 포함"]
        end

        Free --> Basic --> Premium --> VIP
    end
```

---

## 4. 고객 여정

### 4.1 가입부터 구독까지 플로우

```mermaid
flowchart TB
    subgraph Journey["🛤️ 고객 여정 (Customer Journey)"]
        direction TB

        Step1["1️⃣ 발견 단계<br/>━━━━━━━━━━━━━━━━<br/>광고, 검색, SNS를 통해<br/>WSOPTV 서비스 발견"]

        Step2["2️⃣ 가입 단계<br/>━━━━━━━━━━━━━━━━<br/>이메일 또는 소셜 로그인<br/>(Google/Apple/카카오)"]

        Step3["3️⃣ 인증 단계<br/>━━━━━━━━━━━━━━━━<br/>이메일 인증 완료<br/>프로필 설정"]

        Step4["4️⃣ 체험 단계<br/>━━━━━━━━━━━━━━━━<br/>무료 콘텐츠 시청 (50편)<br/>또는 7일 무료 체험"]

        Step5["5️⃣ 전환 단계<br/>━━━━━━━━━━━━━━━━<br/>유료 콘텐츠 결제 유도<br/>플랜 선택 및 결제"]

        Step6["6️⃣ 구독 단계<br/>━━━━━━━━━━━━━━━━<br/>전체 콘텐츠 이용<br/>매월 자동 갱신"]

        Step1 --> Step2 --> Step3 --> Step4 --> Step5 --> Step6
    end
```

### 4.2 전환율 퍼널

```mermaid
flowchart TB
    subgraph Funnel["📊 전환율 퍼널 분석"]
        direction TB

        F1["🌐 월간 방문자<br/>━━━━━━━━━━━━━━<br/>10,000명<br/>(100%)"]

        F2["📝 회원 가입자<br/>━━━━━━━━━━━━━━<br/>1,500명<br/>(15% 전환)"]

        F3["👀 체험 시작자<br/>━━━━━━━━━━━━━━<br/>600명<br/>(40% 전환)"]

        F4["💳 유료 구독자<br/>━━━━━━━━━━━━━━<br/>180명<br/>(30% 전환)"]

        F1 -->|"가입 전환율<br/>15%"| F2
        F2 -->|"체험 전환율<br/>40%"| F3
        F3 -->|"유료 전환율<br/>30%"| F4
    end
```

### 4.3 결제 수단

```mermaid
flowchart TB
    subgraph Payment["💳 지원 결제 수단"]
        direction TB

        subgraph Card["신용/체크카드"]
            C1["VISA<br/>Mastercard<br/>국내 전 카드사"]
        end

        subgraph Easy["간편결제"]
            E1["카카오페이<br/>네이버페이<br/>토스페이"]
        end

        subgraph Global["해외결제"]
            G1["PayPal<br/>Apple Pay<br/>Google Pay"]
        end

        Auto["🔄 자동결제 시스템<br/>━━━━━━━━━━━━━━━━<br/>매월 자동 갱신<br/>취소 전까지 유지"]

        Card --> Auto
        Easy --> Auto
        Global --> Auto
    end
```

---

## 5. 콘텐츠 전략

### 5.1 보유 콘텐츠 현황

```mermaid
pie showData
    title "시리즈별 콘텐츠 분포 (총 500+편)"
    "WSOP 시리즈 (156편)" : 48
    "HCL 시리즈 (89편)" : 27
    "GGMillions (45편)" : 14
    "기타 시리즈 (35편)" : 11
```

### 5.2 콘텐츠 윈도우 전략

```mermaid
flowchart TB
    subgraph Window["📅 콘텐츠 공개 타임라인"]
        direction TB

        W1["📺 라이브 방송<br/>━━━━━━━━━━━━━━<br/>실시간 중계<br/>(VIP 전용)"]

        W2["👑 VIP 조기접근<br/>━━━━━━━━━━━━━━<br/>방송 후 +7일<br/>(VIP 회원 전용)"]

        W3["⭐ Premium 공개<br/>━━━━━━━━━━━━━━<br/>방송 후 +30일<br/>(Premium 이상)"]

        W4["📦 Basic 공개<br/>━━━━━━━━━━━━━━<br/>방송 후 +6개월<br/>(Basic 이상)"]

        W5["🆓 무료 공개<br/>━━━━━━━━━━━━━━<br/>방송 후 +2년<br/>(전체 공개)"]

        W1 -->|"+7일"| W2
        W2 -->|"+23일"| W3
        W3 -->|"+5개월"| W4
        W4 -->|"+1.5년"| W5
    end
```

### 5.3 콘텐츠 티어 구분

```mermaid
flowchart TB
    subgraph Tier["🎬 콘텐츠 티어 시스템"]
        direction TB

        T1["🆓 무료 티어<br/>━━━━━━━━━━━━━━━━<br/>• 2년+ 지난 클래식<br/>• 예고편, 하이라이트<br/>• 초보자 교육 콘텐츠"]

        T2["📦 Basic 티어<br/>━━━━━━━━━━━━━━━━<br/>• 1~2년 된 시리즈<br/>• 시즌 아카이브<br/>• 풀 에피소드"]

        T3["⭐ Premium 티어<br/>━━━━━━━━━━━━━━━━<br/>• 1년 이내 최신작<br/>• 4K 리마스터<br/>• 프로 해설판"]

        T4["👑 VIP 전용 티어<br/>━━━━━━━━━━━━━━━━<br/>• WSOPTV 오리지널<br/>• 라이브 이벤트<br/>• 독점 인터뷰"]

        T1 --> T2 --> T3 --> T4
    end
```

---

## 6. 경쟁 분석

### 6.1 시장 포지셔닝 맵

```mermaid
quadrantChart
    title 경쟁사 포지셔닝 분석
    x-axis 저가격 --> 고가격
    y-axis 범용 콘텐츠 --> 전문 콘텐츠

    quadrant-1 프리미엄 니치
    quadrant-2 매스 프리미엄
    quadrant-3 매스 마켓
    quadrant-4 가성비 니치

    "Netflix": [0.65, 0.25]
    "YouTube": [0.15, 0.20]
    "PokerGO": [0.85, 0.90]
    "WSOPTV": [0.45, 0.92]
```

### 6.2 경쟁사 상세 비교

```mermaid
flowchart TB
    subgraph Compare["🏆 경쟁사 비교 분석"]
        direction TB

        subgraph PokerGO["PokerGO (미국)"]
            PG1["💰 가격: $14.99/월<br/>━━━━━━━━━━━━━━<br/>✅ WSOP 독점 계약<br/>❌ 한국어 미지원<br/>❌ 가격 부담"]
        end

        subgraph YouTube["YouTube (글로벌)"]
            YT1["💰 가격: 무료<br/>━━━━━━━━━━━━━━<br/>✅ 접근성 좋음<br/>❌ 콘텐츠 산발적<br/>❌ 광고 많음"]
        end

        subgraph WSOPTV["⭐ WSOPTV (한국)"]
            WS1["💰 가격: ₩9,900/월<br/>━━━━━━━━━━━━━━<br/>✅ 합리적 가격<br/>✅ 한국어 지원<br/>✅ 체계적 정리"]
        end

        PokerGO --> WSOPTV
        YouTube --> WSOPTV
    end
```

### 6.3 WSOPTV 핵심 차별점

```mermaid
flowchart TB
    subgraph Diff["💡 WSOPTV 4대 차별화 전략"]
        direction TB

        D1["💰 가격 경쟁력<br/>━━━━━━━━━━━━━━━━<br/>PokerGO 대비 50% 저렴<br/>넷플릭스 대비 40% 저렴<br/>국내 최저 가격 포지셔닝"]

        D2["🇰🇷 완벽한 한국화<br/>━━━━━━━━━━━━━━━━<br/>한글 자막 100% 제공<br/>한국어 해설 버전<br/>국내 결제 수단 완비"]

        D3["📚 체계적 큐레이션<br/>━━━━━━━━━━━━━━━━<br/>시리즈/연도별 정리<br/>AI 기반 개인화 추천<br/>넷플릭스급 UX"]

        D4["👥 커뮤니티 연계<br/>━━━━━━━━━━━━━━━━<br/>국내 포커 커뮤니티<br/>VIP 전용 토론방<br/>프로 선수 Q&A"]

        D1 --> D2 --> D3 --> D4
    end
```

---

## 7. 재무 계획

### 7.1 매출 전망

```mermaid
xychart-beta
    title "연도별 매출 전망 (억원)"
    x-axis ["1년차", "2년차", "3년차", "5년차"]
    y-axis "매출(억원)" 0 --> 40
    bar [2.4, 6, 18, 36]
```

### 7.2 구독자 성장 전망

```mermaid
xychart-beta
    title "유료 구독자 성장 추이"
    x-axis ["1년차", "2년차", "3년차", "5년차"]
    y-axis "구독자(명)" 0 --> 130000
    line [2000, 12000, 30000, 120000]
```

### 7.3 비용 구조 (3년차)

```mermaid
pie showData
    title "연간 비용 구조 (총 12억원)"
    "인프라/CDN (35%)" : 35
    "콘텐츠/라이선스 (30%)" : 30
    "인건비 (20%)" : 20
    "마케팅 (10%)" : 10
    "기타 비용 (5%)" : 5
```

### 7.4 손익분기점 분석

```mermaid
flowchart TB
    subgraph BEP["📈 손익분기점 (BEP) 분석"]
        direction TB

        Target["🎯 손익분기 달성<br/>━━━━━━━━━━━━━━━━<br/>시점: 18개월<br/>필요 구독자: 8,000명"]

        subgraph Metrics["💹 핵심 재무 지표"]
            direction LR
            M1["CAC<br/>고객획득비용<br/>━━━━━━━━<br/>₩15,000"]
            M2["LTV<br/>고객생애가치<br/>━━━━━━━━<br/>₩120,000"]
            M3["LTV/CAC<br/>건전성 비율<br/>━━━━━━━━<br/>8배"]
        end

        Result["✅ 평가 결과<br/>━━━━━━━━━━━━━━━━<br/>LTV/CAC 8배는<br/>매우 건전한 수준"]

        Target --> Metrics --> Result
    end
```

---

## 8. 실행 계획

### 8.1 2025년 로드맵

```mermaid
flowchart TB
    subgraph Roadmap["🗓️ 2025년 실행 로드맵"]
        direction TB

        Q1["📍 1분기: MVP 출시<br/>━━━━━━━━━━━━━━━━<br/>• 웹 서비스 정식 오픈<br/>• 결제 시스템 구축<br/>• 3개 플랜 운영 시작"]

        Q2["📍 2분기: 성장 단계<br/>━━━━━━━━━━━━━━━━<br/>• 마케팅 본격 집행<br/>• 추천 알고리즘 도입<br/>• iOS 앱 출시"]

        Q3["📍 3분기: 확장 단계<br/>━━━━━━━━━━━━━━━━<br/>• Android 앱 출시<br/>• 스마트TV 앱 개발<br/>• 첫 라이브 중계"]

        Q4["📍 4분기: 고도화 단계<br/>━━━━━━━━━━━━━━━━<br/>• 오리지널 콘텐츠 제작<br/>• 커뮤니티 기능 추가<br/>• 해외 진출 검토"]

        Q1 --> Q2 --> Q3 --> Q4
    end
```

### 8.2 조직 구성 (3년차)

```mermaid
flowchart TB
    subgraph Org["👥 조직 구성도 (총 12명)"]
        direction TB

        CEO["👔 CEO<br/>━━━━━━━━━━"]

        subgraph Dev["💻 개발팀 (5명)"]
            D1["Backend 2명<br/>Frontend 2명<br/>Infra 1명"]
        end

        subgraph Content["🎬 콘텐츠팀 (3명)"]
            C1["영상편집 2명<br/>자막제작 1명"]
        end

        subgraph Ops["📊 운영팀 (3명)"]
            O1["마케팅 2명<br/>고객지원 1명"]
        end

        CEO --> Dev
        CEO --> Content
        CEO --> Ops
    end
```

---

## 9. 리스크 관리

### 9.1 리스크 매트릭스

```mermaid
quadrantChart
    title 리스크 평가 매트릭스
    x-axis 낮은 영향도 --> 높은 영향도
    y-axis 낮은 발생확률 --> 높은 발생확률

    quadrant-1 적극 관리
    quadrant-2 모니터링
    quadrant-3 수용 가능
    quadrant-4 대비 계획

    "경쟁사 진입": [0.55, 0.70]
    "이탈률 증가": [0.65, 0.55]
    "서버 장애": [0.75, 0.35]
    "저작권 분쟁": [0.90, 0.20]
```

### 9.2 리스크별 대응 전략

```mermaid
flowchart TB
    subgraph Risk["⚠️ 리스크 대응 전략"]
        direction TB

        R1["🏢 경쟁사 진입 리스크<br/>━━━━━━━━━━━━━━━━<br/>• 독점 콘텐츠 선점<br/>• 커뮤니티 락인 효과<br/>• 가격 경쟁력 유지"]

        R2["📉 이탈률 증가 리스크<br/>━━━━━━━━━━━━━━━━<br/>• 신규 콘텐츠 지속<br/>• 개인화 추천 강화<br/>• 연간 구독 할인"]

        R3["🔧 서버 장애 리스크<br/>━━━━━━━━━━━━━━━━<br/>• 이중화 인프라<br/>• 24시간 모니터링<br/>• 자동 복구 시스템"]

        R4["⚖️ 저작권 분쟁 리스크<br/>━━━━━━━━━━━━━━━━<br/>• 법무 사전 검토<br/>• 라이선스 명확화<br/>• 분쟁 대비 보험"]

        R1 --> R2 --> R3 --> R4
    end
```

---

## 10. KPI 대시보드

```mermaid
flowchart TB
    subgraph KPI["📊 핵심 성과 지표 (3년차 목표)"]
        direction TB

        subgraph Growth["📈 성장 지표"]
            G1["MAU (월간활성)<br/>━━━━━━━━━━<br/>목표: 100,000명"]
            G2["신규 가입<br/>━━━━━━━━━━<br/>목표: 5,000/월"]
            G3["유료 전환율<br/>━━━━━━━━━━<br/>목표: 30%"]
        end

        subgraph Revenue["💰 수익 지표"]
            R1["MRR (월매출)<br/>━━━━━━━━━━<br/>목표: 3억원"]
            R2["ARPU (객단가)<br/>━━━━━━━━━━<br/>목표: ₩10,000"]
            R3["LTV (생애가치)<br/>━━━━━━━━━━<br/>목표: ₩120,000"]
        end

        subgraph Retention["🎯 유지 지표"]
            RT1["월간 이탈률<br/>━━━━━━━━━━<br/>목표: < 5%"]
            RT2["DAU/MAU<br/>━━━━━━━━━━<br/>목표: > 40%"]
            RT3["시청시간<br/>━━━━━━━━━━<br/>목표: 60분/일"]
        end

        Growth --> Revenue --> Retention
    end
```

---

## 11. 결론

### 11.1 사업 요약

```mermaid
flowchart TB
    subgraph Summary["📋 WSOPTV 사업 요약"]
        direction TB

        S1["🎯 비전<br/>━━━━━━━━━━━━━━━━━━<br/>국내 1위 포커 전문<br/>OTT 플랫폼 구축"]

        S2["💡 핵심 가치 제안<br/>━━━━━━━━━━━━━━━━━━<br/>• 합리적 가격: ₩9,900/월<br/>• 체계적 콘텐츠: 500+편<br/>• 완벽한 한국어 지원"]

        S3["📊 3년 목표<br/>━━━━━━━━━━━━━━━━━━<br/>• 유료 구독자: 30,000명<br/>• 연간 매출: 36억원<br/>• 영업이익률: 30%+"]

        S4["⏱️ 주요 마일스톤<br/>━━━━━━━━━━━━━━━━━━<br/>• 2025 Q1: MVP 출시<br/>• 2025 Q3: 모바일 앱<br/>• 2026 Q2: 손익분기점"]

        S1 --> S2 --> S3 --> S4
    end
```

### 11.2 승인 요청 사항

```mermaid
flowchart TB
    subgraph Approval["✅ 의사결정 요청 사항"]
        direction TB

        A1["☐ 사업 추진 승인<br/>━━━━━━━━━━━━━━━━━━<br/>WSOPTV OTT 서비스<br/>사업 추진 승인 요청"]

        A2["☐ 1차 투자 승인<br/>━━━━━━━━━━━━━━━━━━<br/>MVP 개발: 2억원<br/>• 개발 인력 확보<br/>• 인프라 구축<br/>• 초기 마케팅"]

        A3["☐ 인력 채용 승인<br/>━━━━━━━━━━━━━━━━━━<br/>초기 인원: 5명<br/>• 개발 3명<br/>• 콘텐츠 1명<br/>• 운영 1명"]

        A4["☐ 일정 승인<br/>━━━━━━━━━━━━━━━━━━<br/>MVP 출시 목표<br/>2025년 1분기"]

        Next["📌 다음 단계<br/>━━━━━━━━━━━━━━━━━━<br/>승인 시: 2주 내 상세 계획<br/>검토 시: 추가 자료 준비"]

        A1 --> A2 --> A3 --> A4 --> Next
    end
```

---

## 부록

### A. 용어 정의

| 용어 | 설명 |
|------|------|
| OTT | Over-The-Top, 인터넷 기반 영상 서비스 |
| MAU | Monthly Active Users, 월간 활성 사용자 |
| MRR | Monthly Recurring Revenue, 월간 반복 매출 |
| ARPU | Average Revenue Per User, 사용자당 평균 매출 |
| LTV | Lifetime Value, 고객 생애 가치 |
| CAC | Customer Acquisition Cost, 고객 획득 비용 |
| BEP | Break-Even Point, 손익분기점 |

### B. 관련 문서

| 문서 | 설명 |
|------|------|
| PRD-0003 | 기술 아키텍처 상세 |
| PRD-0004 | 상용 OTT 기술 사양서 |
| PRD-0005 | ASCII 버전 기획서 |

---

**문서 끝**
