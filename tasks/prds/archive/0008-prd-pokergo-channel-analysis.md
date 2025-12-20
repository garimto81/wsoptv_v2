# PokerGO 스트림 채널 분석 PRD

**문서 번호**: PRD-0008
**버전**: 1.0.0
**작성일**: 2025-12-15
**목적**: PokerGO 스트리밍 서비스 분석 및 WSOPTV 벤치마킹

---

## 1. PokerGO 서비스 개요

### 1.1 서비스 정의

```mermaid
flowchart TB
    subgraph Overview["PokerGO 서비스 개요"]
        direction TB
        O1["서비스명<br/>━━━━━━━━━━━━━━━━━━━━<br/>PokerGO<br/>세계 #1 포커 스트리밍"]
        O2["핵심 가치<br/>━━━━━━━━━━━━━━━━━━━━<br/>100+ 일 라이브 중계/년<br/>2,400+ VOD 콘텐츠<br/>3,800+ 시간 라이브러리"]
        O3["운영 주체<br/>━━━━━━━━━━━━━━━━━━━━<br/>Poker Central LLC<br/>설립: 2015년<br/>본사: Las Vegas, NV"]
        O1 --> O2 --> O3
    end
```

### 1.2 사업 모델

```mermaid
flowchart TB
    subgraph Business["PokerGO 사업 모델"]
        direction TB
        B1["수익원 1: 구독료<br/>━━━━━━━━━━━━━━━━━━━━<br/>월간: $19.99<br/>분기: $39.99<br/>연간: $99.99<br/>VIP: $299.99"]
        B2["수익원 2: 광고/파트너십<br/>━━━━━━━━━━━━━━━━━━━━<br/>FAST 채널 (무료+광고)<br/>CBS Sports 파트너십<br/>스폰서 토너먼트"]
        B3["수익원 3: 배포 라이선스<br/>━━━━━━━━━━━━━━━━━━━━<br/>DIRECTV<br/>Fubo<br/>YouTube TV"]
        B1 --> B2 --> B3
    end
```

---

## 2. 콘텐츠 구조 분석

### 2.1 콘텐츠 카테고리

```mermaid
flowchart TB
    subgraph Content["PokerGO 콘텐츠 구조"]
        direction TB
        C1["Featured Shows<br/>━━━━━━━━━━━━━━━━━━━━<br/>메인 홈 노출 콘텐츠<br/>최신/인기 콘텐츠<br/>에디터 추천"]
        C2["Original Series<br/>━━━━━━━━━━━━━━━━━━━━<br/>Pokerography (23편)<br/>Super High Roller Club<br/>Real Talk<br/>The Big Blind<br/>Legends of the Game"]
        C3["Event Replays<br/>━━━━━━━━━━━━━━━━━━━━<br/>WSOP Final Tables<br/>토너먼트 리플레이<br/>하이라이트 클립"]
        C4["The Vault (아카이브)<br/>━━━━━━━━━━━━━━━━━━━━<br/>Poker After Dark<br/>Face the Ace<br/>다큐멘터리<br/>클래식 영상"]
        C1 --> C2 --> C3 --> C4
    end
```

### 2.2 콘텐츠 상세 분류

| 카테고리 | 콘텐츠 유형 | 설명 | 콘텐츠 수 |
|---------|-----------|------|----------|
| **Live Events** | 라이브 스트림 | 실시간 토너먼트 중계 | 100+ 일/년 |
| **Tournaments** | VOD | WSOP, SHRB, Poker Masters | 다수 |
| **Cash Games** | VOD | High Stakes Poker, Poker After Dark | 다수 |
| **Original Series** | VOD | 자체 제작 시리즈 | 6개 시리즈 |
| **Documentaries** | VOD | 선수 다큐, 역사 | 다수 |
| **Educational** | VOD | PokerU (VIP 전용) | 강좌 |

### 2.3 주요 쇼 프로그램

```mermaid
flowchart TB
    subgraph Shows["PokerGO 주요 프로그램"]
        direction TB
        S1["High Stakes Poker<br/>━━━━━━━━━━━━━━━━━━━━<br/>장르: 캐시 게임<br/>시즌: 14+<br/>형식: 레전드 캐시 게임<br/>인기도: 최상"]
        S2["Poker After Dark<br/>━━━━━━━━━━━━━━━━━━━━<br/>장르: 캐시 게임<br/>시즌: 다수<br/>형식: 심야 캐시 게임<br/>인기도: 상"]
        S3["No Gamble, No Future<br/>━━━━━━━━━━━━━━━━━━━━<br/>장르: 리얼리티<br/>시즌: 진행 중<br/>형식: 엔터테인먼트<br/>인기도: 상"]
        S4["High Stakes Duel<br/>━━━━━━━━━━━━━━━━━━━━<br/>장르: 헤즈업 대결<br/>시즌: 다수<br/>형식: 1:1 토너먼트<br/>인기도: 상"]
        S5["Super High Roller Bowl<br/>━━━━━━━━━━━━━━━━━━━━<br/>장르: 토너먼트<br/>바이인: $300K+<br/>형식: 하이롤러 대회<br/>인기도: 최상"]
        S6["Pokerography<br/>━━━━━━━━━━━━━━━━━━━━<br/>장르: 다큐멘터리<br/>에피소드: 23편<br/>형식: 선수 전기<br/>인기도: 중"]
    end
```

---

## 3. 라이브 중계 구조

### 3.1 연간 라이브 일정

```mermaid
flowchart TB
    subgraph LiveSchedule["PokerGO 연간 라이브 일정"]
        direction TB
        L1["Q1: PGT Kickoff<br/>━━━━━━━━━━━━━━━━━━━━<br/>1-2월<br/>PokerGO Cup<br/>U.S. Poker Open<br/>SHRB Mixed Games"]
        L2["Q2: WSOP 시즌<br/>━━━━━━━━━━━━━━━━━━━━<br/>5-7월<br/>WSOP 전체 (51일)<br/>Main Event (7/2-16)<br/>30+ 브라켓 이벤트"]
        L3["Q3: 하계 투어<br/>━━━━━━━━━━━━━━━━━━━━<br/>8-9월<br/>Poker Masters<br/>추가 이벤트"]
        L4["Q4: 시즌 피날레<br/>━━━━━━━━━━━━━━━━━━━━<br/>10-11월<br/>PGT Championship<br/>$1M 메인 이벤트"]
        L1 --> L2 --> L3 --> L4
    end
```

### 3.2 2025 WSOP 중계 일정

| 날짜 | 이벤트 | 형식 | 바이인 |
|------|-------|------|--------|
| 5/31~ | WSOP 시작 | Daily Coverage | Various |
| 7/2-16 | Main Event | Full Coverage | $10,000 |
| TBD | Poker Players Championship | Final Table | $50,000 |
| TBD | High Roller | Final Table | $250,000 |
| TBD | Heads-Up Championship | Full | $25,000 |
| TBD | Ladies Championship | Full | $1,000 |

---

## 4. 배포 채널 구조

### 4.1 멀티 플랫폼 배포

```mermaid
flowchart TB
    subgraph Distribution["PokerGO 배포 채널"]
        direction TB
        D1["Direct (OTT)<br/>━━━━━━━━━━━━━━━━━━━━<br/>PokerGO.com<br/>iOS/Android 앱<br/>Smart TV 앱<br/>구독 기반"]
        D2["Linear TV (vMVPD)<br/>━━━━━━━━━━━━━━━━━━━━<br/>DIRECTV<br/>Fubo<br/>YouTube TV<br/>채널 번들"]
        D3["FAST Channels<br/>━━━━━━━━━━━━━━━━━━━━<br/>Pluto TV<br/>Samsung TV Plus<br/>Roku Channel<br/>Tubi TV<br/>광고 기반 무료"]
        D4["Social/Free<br/>━━━━━━━━━━━━━━━━━━━━<br/>YouTube 채널<br/>Twitch<br/>일부 무료 콘텐츠"]
        D1 --> D2 --> D3 --> D4
    end
```

### 4.2 디바이스 지원 현황

| 플랫폼 | 지원 | 앱 유형 | 비고 |
|--------|------|---------|------|
| **iOS (iPhone/iPad)** | O | Native | App Store |
| **Android** | O | Native | Play Store |
| **Apple TV** | O | tvOS | App Store |
| **Amazon Fire TV** | O | Native | Amazon Appstore |
| **Roku** | O | Channel | Roku Channel Store |
| **Android TV** | O | Native | - |
| **Google Chromecast** | O | Cast | - |
| **Samsung Smart TV** | O | Tizen | - |
| **Sony Smart TV** | O | - | - |
| **VIZIO Smart TV** | O | - | - |
| **Mac/Windows** | O | Web | PokerGO.com |
| **PlayStation** | X | - | 미지원 |
| **Xbox** | X | - | 미지원 |

### 4.3 기술 인프라

```mermaid
flowchart TB
    subgraph Tech["PokerGO 기술 인프라"]
        direction TB
        T1["스트리밍 플랫폼<br/>━━━━━━━━━━━━━━━━━━━━<br/>NeuLion/Endeavor Streaming<br/>OTT 전문 솔루션<br/>스포츠 스트리밍 특화"]
        T2["CDN/인프라<br/>━━━━━━━━━━━━━━━━━━━━<br/>글로벌 CDN<br/>적응형 비트레이트<br/>HD 품질"]
        T3["FAST 배포<br/>━━━━━━━━━━━━━━━━━━━━<br/>Frequency Studio<br/>250M+ Connected TV<br/>멀티 플랫폼 배포"]
    end
```

---

## 5. 구독 모델 분석

### 5.1 가격 체계

```mermaid
flowchart TB
    subgraph Pricing["PokerGO 가격 체계"]
        direction TB
        P1["Monthly<br/>━━━━━━━━━━━━━━━━━━━━<br/>$19.99/월<br/>월 환산: $19.99<br/>할인율: 0%<br/>유연한 취소"]
        P2["Quarterly<br/>━━━━━━━━━━━━━━━━━━━━<br/>$39.99/3개월<br/>월 환산: $13.33<br/>할인율: 33%<br/>3개월 약정"]
        P3["Annual<br/>━━━━━━━━━━━━━━━━━━━━<br/>$99.99/년<br/>월 환산: $8.33<br/>할인율: 58%<br/>최고 가성비"]
        P4["VIP<br/>━━━━━━━━━━━━━━━━━━━━<br/>$299.99/년<br/>월 환산: $25.00<br/>PokerU 포함<br/>$25 상품권"]
        P1 --> P2 --> P3 --> P4
    end
```

### 5.2 경쟁 OTT 가격 비교

| 서비스 | 월 가격 | 콘텐츠 범위 | 대상 |
|--------|---------|------------|------|
| **PokerGO** | $8.33~$19.99 | 포커 전문 | 니치 |
| Netflix (Basic) | $6.99 | 범용 | 대중 |
| Disney+ | $7.99 | 범용 | 대중 |
| ESPN+ | $10.99 | 스포츠 전문 | 스포츠팬 |
| DAZN | $14.99 | 스포츠 전문 | 스포츠팬 |

### 5.3 구독 혜택

```mermaid
flowchart TB
    subgraph Benefits["구독 혜택"]
        direction TB
        BF1["기본 혜택 (전 플랜)<br/>━━━━━━━━━━━━━━━━━━━━<br/>광고 없음<br/>100+ 일 라이브<br/>2,400+ VOD<br/>멀티 디바이스"]
        BF2["연간 구독자 혜택<br/>━━━━━━━━━━━━━━━━━━━━<br/>Dream Seat 추첨<br/>PGT Championship<br/>$300 여행 상품권<br/>3박 호텔 숙박"]
        BF3["VIP 혜택<br/>━━━━━━━━━━━━━━━━━━━━<br/>PokerU 교육 콘텐츠<br/>$25 상품 크레딧<br/>독점 이벤트"]
    end
```

---

## 6. UI/UX 분석

### 6.1 홈 화면 구조

```mermaid
flowchart TB
    subgraph HomeUI["PokerGO 홈 화면 구조"]
        direction TB
        H1["Hero Banner<br/>━━━━━━━━━━━━━━━━━━━━<br/>추천 라이브/VOD<br/>대형 비주얼<br/>재생 버튼"]
        H2["Live Now Section<br/>━━━━━━━━━━━━━━━━━━━━<br/>현재 라이브 중계<br/>시청자 수<br/>실시간 배지"]
        H3["Continue Watching<br/>━━━━━━━━━━━━━━━━━━━━<br/>이어보기 목록<br/>진행률 표시<br/>개인화"]
        H4["Featured Shows<br/>━━━━━━━━━━━━━━━━━━━━<br/>인기 프로그램<br/>카테고리별 Row<br/>가로 스크롤"]
        H5["Browse Categories<br/>━━━━━━━━━━━━━━━━━━━━<br/>Tournaments<br/>Cash Games<br/>Original Series"]
        H1 --> H2 --> H3 --> H4 --> H5
    end
```

### 6.2 콘텐츠 상세 페이지

```mermaid
flowchart TB
    subgraph DetailUI["콘텐츠 상세 페이지"]
        direction TB
        DT1["Video Player<br/>━━━━━━━━━━━━━━━━━━━━<br/>HD 플레이어<br/>전체화면 지원<br/>재생 컨트롤"]
        DT2["Title & Metadata<br/>━━━━━━━━━━━━━━━━━━━━<br/>프로그램명<br/>시즌/에피소드<br/>방영일/런타임"]
        DT3["Description<br/>━━━━━━━━━━━━━━━━━━━━<br/>에피소드 설명<br/>출연자 정보<br/>태그"]
        DT4["Related Content<br/>━━━━━━━━━━━━━━━━━━━━<br/>같은 시리즈<br/>비슷한 콘텐츠<br/>추천"]
    end
```

### 6.3 네비게이션 구조

| 메뉴 | 기능 | 하위 메뉴 |
|------|------|----------|
| **Home** | 메인 홈 | - |
| **Live** | 라이브 중계 | 현재 라이브, 일정 |
| **Shows** | VOD 브라우즈 | Tournaments, Cash Games, Originals |
| **Schedule** | 라이브 일정 | 월별 캘린더 |
| **Search** | 검색 | 제목, 선수, 이벤트 |
| **Account** | 계정 관리 | 프로필, 구독, 설정 |

---

## 7. 문제점 분석

### 7.1 사용자 불만 사항

```mermaid
flowchart TB
    subgraph Issues["PokerGO 주요 문제점"]
        direction TB
        I1["기술적 문제<br/>━━━━━━━━━━━━━━━━━━━━<br/>스트림 프리징<br/>버퍼링 빈번<br/>화질 저하<br/>App Store 평점: 3.3/5"]
        I2["UX 문제<br/>━━━━━━━━━━━━━━━━━━━━<br/>시청 위치 미저장<br/>에피소드 추적 불가<br/>검색 기능 미흡<br/>UI 개선 역행"]
        I3["콘텐츠 문제<br/>━━━━━━━━━━━━━━━━━━━━<br/>해설자 스포일러<br/>60%+ 오래된 콘텐츠<br/>무료 대안 존재"]
        I4["가격/결제 문제<br/>━━━━━━━━━━━━━━━━━━━━<br/>Netflix보다 비쌈<br/>무단 결제 사례<br/>가격 인상 이슈<br/>Trustpilot: 2.1/5"]
    end
```

### 7.2 경쟁 위협

| 위협 | 내용 | 심각도 |
|------|------|--------|
| **무료 YouTube** | Hustler Casino Live, PokerStars 채널 | 높음 |
| **무료 Twitch** | 월 142만 시청 시간 | 높음 |
| **FAST 채널** | 자체 Pluto TV 채널이 무료로 제공 | 중간 |
| **가격 저항** | 니치 콘텐츠에 높은 가격 | 중간 |

---

## 8. WSOPTV 벤치마킹 포인트

### 8.1 채택할 요소

```mermaid
flowchart TB
    subgraph Adopt["WSOPTV 채택 요소"]
        direction TB
        A1["콘텐츠 구조<br/>━━━━━━━━━━━━━━━━━━━━<br/>4개 카테고리 분류<br/>Featured/Original/Replay/Vault<br/>명확한 계층"]
        A2["멀티 플랫폼 배포<br/>━━━━━━━━━━━━━━━━━━━━<br/>OTT + Linear + FAST<br/>다양한 접점 확보<br/>무료 티어 제공"]
        A3["연간 구독자 혜택<br/>━━━━━━━━━━━━━━━━━━━━<br/>추첨 이벤트<br/>토너먼트 참가권<br/>락인 전략"]
        A4["라이브 일정 공개<br/>━━━━━━━━━━━━━━━━━━━━<br/>연간 스케줄 공개<br/>사전 프로모션<br/>기대감 조성"]
    end
```

### 8.2 개선할 요소

```mermaid
flowchart TB
    subgraph Improve["WSOPTV 개선 요소"]
        direction TB
        IM1["스트리밍 안정성<br/>━━━━━━━━━━━━━━━━━━━━<br/>99.9% 가용성 목표<br/>글로벌 CDN 강화<br/>적응형 비트레이트"]
        IM2["시청 경험<br/>━━━━━━━━━━━━━━━━━━━━<br/>시청 위치 자동 저장<br/>에피소드 추적<br/>스포일러 방지 모드"]
        IM3["가격 경쟁력<br/>━━━━━━━━━━━━━━━━━━━━<br/>PokerGO 대비 저렴<br/>무료 티어 제공<br/>지역별 가격 차등"]
        IM4["결제 투명성<br/>━━━━━━━━━━━━━━━━━━━━<br/>명확한 정책<br/>갱신 전 알림<br/>원클릭 취소"]
    end
```

### 8.3 차별화 요소

```mermaid
flowchart TB
    subgraph Differentiate["WSOPTV 차별화 요소"]
        direction TB
        DF1["콘텐츠 소유권<br/>━━━━━━━━━━━━━━━━━━━━<br/>WSOP 브랜드 소유<br/>18TB+ 원본 마스터<br/>라이선스 비용 0"]
        DF2["AI 분석 기능<br/>━━━━━━━━━━━━━━━━━━━━<br/>실시간 핸드 분석<br/>EV 계산기<br/>학습 추천"]
        DF3["인터랙티브 기능<br/>━━━━━━━━━━━━━━━━━━━━<br/>실시간 예측 게임<br/>커뮤니티 채팅<br/>팬 투표"]
        DF4["아시아 전문<br/>━━━━━━━━━━━━━━━━━━━━<br/>한국어/일본어 지원<br/>아시아 토너먼트<br/>현지 결제"]
    end
```

---

## 9. 콘텐츠 운영 전략 비교

### 9.1 PokerGO vs WSOPTV 콘텐츠 전략

| 항목 | PokerGO | WSOPTV (제안) |
|------|---------|---------------|
| **라이브 중계** | 100+ 일/년 | Phase별 확대 |
| **VOD 라이브러리** | 3,800+ 시간 | 18TB+ 아카이브 |
| **오리지널 시리즈** | 6개 시리즈 | 아시아 오리지널 |
| **교육 콘텐츠** | VIP 전용 (PokerU) | 전 플랜 AI 분석 |
| **무료 콘텐츠** | YouTube 일부 | 무료 티어 제공 |
| **FAST 채널** | 4개 플랫폼 | 검토 필요 |

### 9.2 배포 전략 비교

| 채널 | PokerGO | WSOPTV (제안) |
|------|---------|---------------|
| **Direct OTT** | O | O (필수) |
| **iOS/Android** | O | O (필수) |
| **Smart TV** | O (6개+) | O (주요 플랫폼) |
| **vMVPD** | O (3개) | 검토 |
| **FAST** | O (4개) | Phase 2 |
| **YouTube** | O (부분 무료) | O (프로모션) |

---

## 10. 결론

### 10.1 핵심 인사이트

```mermaid
flowchart TB
    subgraph Insights["핵심 인사이트"]
        direction TB
        IN1["시장 포지션<br/>━━━━━━━━━━━━━━━━━━━━<br/>PokerGO = 독점적 지위<br/>but 사용자 불만 다수<br/>무료 대안 성장 중"]
        IN2["기술 품질<br/>━━━━━━━━━━━━━━━━━━━━<br/>스트리밍 불안정<br/>UX 문제 미해결<br/>개선 기회 존재"]
        IN3["가격 민감도<br/>━━━━━━━━━━━━━━━━━━━━<br/>니치 콘텐츠에 고가<br/>가격 저항 존재<br/>경쟁 가격 전략 유효"]
        IN4["WSOPTV 기회<br/>━━━━━━━━━━━━━━━━━━━━<br/>콘텐츠 소유주 우위<br/>기술 품질 차별화<br/>가격 경쟁력 확보"]
    end
```

### 10.2 WSOPTV 액션 아이템

| 우선순위 | 액션 | 상세 |
|---------|------|------|
| **P0** | 스트리밍 안정성 확보 | 99.9% 가용성, CDN 최적화 |
| **P0** | 시청 경험 개선 | 진행률 저장, 에피소드 추적 |
| **P1** | 가격 경쟁력 | PokerGO 대비 30-40% 저렴 |
| **P1** | 무료 티어 제공 | 일부 콘텐츠 무료 공개 |
| **P2** | AI 분석 기능 | 핸드 분석, 학습 추천 |
| **P2** | 멀티 플랫폼 확장 | Smart TV, FAST 채널 |

---

## 참고 자료

### 공식 사이트
- [PokerGO 공식](https://www.pokergo.com/)
- [PokerGO Schedule](https://www.pokergo.com/schedule)
- [PGT.com](https://www.pgt.com/)

### 리뷰/분석
- [The Streamable - PokerGO Review](https://thestreamable.com/video-streaming/pokergo)
- [Pokerfuse - PokerGO Subscription Guide](https://pokerfuse.com/live-poker/coverage/pokergo/)
- [Pokerfuse - Best Poker Shows 2025](https://pokerfuse.com/live-poker/coverage/best-poker-shows-streams-2025/)

### 뉴스/보도자료
- [PokerGO 2025 WSOP Streaming Plans](https://www.pgt.com/press-releases/pokergo-announces-2025-wsop-livestreaming-plans-featuring-daily-coverage-of-the-main-event-and-more)
- [PokerGO YouTube TV Expansion](https://www.pgt.com/press-releases/pokergo-expands-distribution-with-new-youtubetv-and-primetime-channel-offering)
- [PokerGO FAST Channel Expansion](https://www.pgt.com/press-releases/pokergo%C2%AE-turns-to-frequency-to-expand-fast-channel-presence)

### 앱 스토어
- [Apple App Store - PokerGO](https://apps.apple.com/us/app/pokergo-stream-poker-tv/id1235783484) - 3.3/5.0
- [Google Play Store - PokerGO](https://play.google.com/store/apps/details?id=com.pokercentral.poker)

---

*문서 끝*
