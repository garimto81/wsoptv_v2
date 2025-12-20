# WSOPTV 콘텐츠 전략

**Version**: 4.1.0 | **Parent**: [00-master.md](./00-master.md)

---

## Executive Summary

WSOPTV는 **WSOP 아카이브** (현재 17.96TB, 1,056개 파일 → 향후 1PB+ 확장)를 기반으로 포커 팬 대상 OTT 서비스를 제공합니다.

**투트랙 전략**으로 수익을 극대화합니다:
- **YouTube**: 무료 콘텐츠로 신규 팬 유입
- **WSOPTV**: 유료 구독으로 열성 팬 전환

```mermaid
flowchart LR
    subgraph FREE["YouTube (무료)"]
        Y1["쇼츠/클립"]
        Y2["생방송"]
        Y3["하이라이트"]
    end

    subgraph PAID["WSOPTV ($9.99/월)"]
        W1["풀 에피소드"]
        W2["Hand Skip"]
        W3["Best Hands"]
        W4["4K Remaster"]
    end

    FREE -->|"전환"| PAID

    style PAID fill:#1a1a2e,stroke:#ffd700,stroke-width:2px
    style FREE fill:#ff0000,stroke:#cc0000
```

---

## 1. 투트랙 수익화 전략

### 1.1 채널별 역할

| 채널 | 역할 | 목표 |
|------|------|------|
| **YouTube** | 유입 게이트웨이 | 포커 관심층 확보, WSOPTV 인지도 |
| **WSOPTV** | 수익 엔진 | 구독 전환, 리텐션 |

### 1.2 콘텐츠 배분 원칙

```mermaid
flowchart TB
    subgraph CONTENT["콘텐츠 배분"]
        direction LR

        subgraph YT["YouTube"]
            Y1["쇼츠 (60초)"]
            Y2["하이라이트 (5-10분)"]
            Y3["생방송"]
            Y4["Best Hands 티저"]
        end

        subgraph WS["WSOPTV"]
            W1["풀 에피소드"]
            W2["Best Hands 전체"]
            W3["4K Remaster"]
            W4["생방송 + VOD"]
        end
    end
```

| 콘텐츠 유형 | YouTube | WSOPTV | 배분 의도 |
|-------------|:-------:|:------:|-----------|
| **풀 에피소드** | X | O | 유료 전환 핵심 콘텐츠 |
| **쇼츠 (60초)** | O | X | 바이럴, 신규 유입 |
| **하이라이트 (5-10분)** | O | X | 관심 유발 |
| **Best Hands 클립** | 일부 (티저) | 전체 | 맛보기 → 전환 유도 |
| **생방송** | O | O | 동시 송출 |
| **4K Remaster** | 프로모션만 | 전체 | 프리미엄 독점 |

### 1.3 전환 퍼널

```mermaid
flowchart LR
    A["YouTube 시청자"] --> B["쇼츠/클립 소비"]
    B --> C["풀 영상 관심"]
    C --> D["WSOPTV 랜딩"]
    D --> E["30초 미리보기"]
    E --> F["구독 전환"]
```

| 단계 | 트리거 | 액션 | KPI |
|------|--------|------|-----|
| 인지 | YouTube 알고리즘 | 쇼츠/클립 시청 | 조회수 |
| 관심 | "풀 영상 보기" CTA | WSOPTV 랜딩 클릭 | CTR |
| 결정 | 30초 미리보기 | Paywall 노출 | 미리보기 완료율 |
| 전환 | 구독 버튼 클릭 | 결제 완료 | 전환율 |

---

## 2. 콘텐츠 분류 체계

> **Data Source**: [NAS Asset Management (Google Sheets)](https://docs.google.com/spreadsheets/d/1h27Ha7pR-iYK_Gik8F4FfSvsk4s89sxk49CsU3XP_m4)

### 2.1 현재 보유량

| 구분 | 수치 |
|------|------|
| **총 파일 수** | 1,056개 |
| **총 용량** | 17.96 TB |
| **연도 범위** | 1973-2025 |
| **PRIMARY** | 872개 (82.6%) |
| **BACKUP** | 184개 (17.4%) |

### 2.2 Era (시대별 분류)

```mermaid
pie showData
    title Era별 용량 분포 (TB)
    "CLASSIC (1973-2002)" : 1.13
    "BOOM (2003-2010)" : 10.14
    "HD (2011-2025)" : 6.69
```

| Era | 연도 | 파일 수 | 용량 | 특징 |
|-----|------|---------|------|------|
| **CLASSIC** | 1973-2002 | 42 | 1.13 TB | SD, 희귀 영상, 4K Remaster 대상 |
| **BOOM** | 2003-2010 | 341 | 10.14 TB | Moneymaker 이후 황금기 |
| **HD** | 2011-2025 | 673 | 6.69 TB | HD/4K 현대 영상 |

### 2.3 Event Type (이벤트 유형)

```mermaid
pie showData
    title Event Type 분포
    "ME (Main Event)" : 505
    "BR (Bracelet)" : 308
    "OTHER" : 91
    "기타" : 152
```

| 코드 | 설명 | 파일 수 | 비중 |
|------|------|---------|------|
| **ME** | Main Event | 505 | 47.8% |
| **BR** | Bracelet Events | 308 | 29.2% |
| **OTHER** | 기타 | 91 | 8.6% |
| **COVERAGE** | 방송 커버리지 | 34 | 3.2% |
| **MXF** | Masters | 26 | 2.5% |
| **GOG** | Game of Gold | 24 | 2.3% |
| **TOC** | Tournament of Champions | 14 | 1.3% |
| **BEST** | Best Hands | 8 | 0.8% |
| 기타 | EU, APAC, CIRCUIT 등 | 46 | 4.3% |

### 2.4 Region (지역)

| 코드 | 지역 | 파일 수 | 비중 |
|------|------|---------|------|
| **LV** | Las Vegas | 933 | 88.4% |
| **EU** | Europe | 100 | 9.5% |
| **CYPRUS** | Cyprus | 11 | 1.0% |
| **APAC** | Asia Pacific | 6 | 0.6% |
| **CIRCUIT** | Super Circuit | 6 | 0.6% |

### 2.5 메타데이터 스키마

**Master_Catalog 컬럼**

| 필드 | 설명 | 예시 |
|------|------|------|
| `Entry Key` | 고유 식별자 | `WSOP_2024_ME_D5` |
| `Category` | 카테고리 | `WSOP 2024 Main Event` |
| `Title` | 에피소드 제목 | `Main Event Day 5` |
| `Event Type` | 이벤트 유형 | `ME`, `BR`, `GOG` |
| `Region` | 지역 | `LV`, `EU`, `APAC` |
| `Day` | 방송일차 | `D1`, `D2`, `FT` |
| `Part` | 파트 | `P1`, `P2` |
| `Size (GB)` | 파일 크기 | `15.3` |

**Category 명명 규칙**

```
WSOP {YEAR} Main Event
WSOP {YEAR} Bracelet Events
WSOP Europe {YEAR} - Main Event
WSOP Europe {YEAR} - Bracelet Events
Game of Gold {YEAR}
```

**핸드 메타데이터 (GGP Archive 제공)**

> **외부 의존성**: 핸드 타임스탬프와 Best Hands 선정은 **GGP Archive 팀**에서 제공합니다.

| 필드 | 설명 |
|------|------|
| `start_time` | 핸드 시작 타임스탬프 |
| `end_time` | 핸드 종료 타임스탬프 |
| `is_best` | Best Hand 여부 |
| `hand_type` | all_in, bluff, hero_call 등 |
| `players` | 참여 플레이어 목록 |
| `pot_size` | 팟 규모 |

---

## 3. 콘텐츠 캘린더

### 3.1 연간 흐름

```mermaid
gantt
    title WSOP 연간 콘텐츠 캘린더
    dateFormat  YYYY-MM
    axisFormat %b

    section 메인 시즌
    WSOP Las Vegas (80%)   :crit, 2025-05, 3M

    section 서브 시즌
    WSOP Europe            :2025-04, 1M
    Super Circuit          :2025-03, 1M
    WSOP Paradise          :2025-12, 1M

    section 비시즌
    4K Remaster 릴리스     :2025-08, 2M
    Best Hands 큐레이션    :2025-01, 2M
```

| 시기 | 이벤트 | 콘텐츠 집중도 | 운영 전략 |
|------|--------|:------------:|-----------|
| **5-7월** | WSOP Las Vegas | 80% | 신규 에피소드 집중 업로드 |
| 3월 | Super Circuit | 5% | 글로벌 확장 콘텐츠 |
| 4월 | WSOP Europe | 5% | 유럽 시장 타겟 |
| 10월 | Super Circuit | 5% | 글로벌 순회 |
| 12월 | WSOP Paradise | 5% | 연말 프리미엄 |

### 3.2 비시즌 운영

| 비시즌 | 콘텐츠 전략 |
|--------|-------------|
| **8-9월** | 4K Remaster 신규 릴리스, 시즌 하이라이트 |
| **1-2월** | 클래식 시리즈 재조명, Best Hands 연간 베스트 |
| **10-11월** | 다음 시즌 프리뷰, 플레이어 프로파일 |

---

## 4. 차별화 기능 연동

### 4.1 Hand Skip

> 핸드와 핸드 사이 대기 시간을 자동 건너뛰어 **액션만 시청**

```mermaid
flowchart LR
    subgraph BEFORE["Hand Skip OFF"]
        A1["핸드 #1<br/>5분"] --> W1["대기<br/>8분"]
        W1 --> A2["핸드 #2<br/>4분"] --> W2["대기<br/>10분"]
    end

    subgraph AFTER["Hand Skip ON"]
        B1["핸드 #1"] --> B2["핸드 #2"] --> B3["핸드 #3"]
    end

    BEFORE -.->|"2시간 → 45분"| AFTER
```

| 항목 | 내용 |
|------|------|
| 대상 | 모든 풀 에피소드 |
| 의존성 | GGP Archive 핸드 타임스탬프 |
| 효과 | 평균 63% 시청 시간 단축 |

### 4.2 Best Hands

> 풀 에피소드 내에서 **베스트 핸드 구간만 점프 재생**

| 카테고리 | 설명 |
|----------|------|
| **All-in Showdowns** | 올인 후 런아웃 대결 |
| **Bluff Catches** | 블러프 잡아낸 명콜 |
| **Hero Calls** | 용감한 콜로 승리 |
| **Hero Folds** | 큰 핸드 폴드한 명판단 |
| **Bad Beats** | 역전당한 불운의 핸드 |
| **Monster Pots** | $500K+ 거액 팟 |

| 항목 | 내용 |
|------|------|
| 대상 | 모든 풀 에피소드 |
| 의존성 | GGP Archive 베스트 핸드 선정 |
| 효과 | 10시간 → 45분 (Best만 시청) |

### 4.3 4K Remaster

> 2003-2015 클래식 영상을 **AI 업스케일링으로 4K 화질 복원**

| 대상 연도 | 원본 화질 | 리마스터 |
|-----------|----------|----------|
| 2003-2005 | 480p SD | 4K UHD |
| 2006-2010 | 720p HD | 4K UHD |
| 2011-2015 | 1080p FHD | 4K UHD |

**마케팅 활용**
- Before/After 프로모션: YouTube 티저 → WSOPTV 전환
- "4K로 다시 보는 Moneymaker 우승" 캠페인

---

## 5. 진화 로드맵

```mermaid
timeline
    title WSOPTV 콘텐츠 진화
    section Phase 1 - MVP
        전체 아카이브 업로드 : 기본 시청
        이어보기 : 시청 위치 저장
    section Phase 2 - 개인화
        카테고리 정비 : 시리즈/이벤트별
        검색 + 추천 : MeiliSearch 연동
    section Phase 3 - 차별화
        Hand Skip : GGP 메타데이터 연동
        Best Hands : 타임스탬프 점프
    section Phase 4 - 프리미엄
        4K Remaster 확대 : 클래식 전체
        오리지널 다큐 : 독점 콘텐츠
```

| Phase | 콘텐츠 | 기능 | KPI |
|:-----:|--------|------|-----|
| **P1** | 전체 아카이브 | 이어보기 | MAU, 시청 시간 |
| **P2** | 카테고리 정비 | 검색, 추천 | 검색 사용률, CTR |
| **P3** | GGP 메타데이터 연동 | Hand Skip, Best Hands | 기능 사용률, 리텐션 |
| **P4** | 4K Remaster 확대 | 프리미엄 티어 | ARPU, LTV |

---

## 부록: GGP Archive 의존성

> Hand Skip과 Best Hands는 GGP Archive 팀의 메타데이터에 의존합니다.

```mermaid
flowchart LR
    GGP["GGP Archive 팀"] -->|"메타데이터"| API["WSOPTV API"]

    API --> HS["Hand Skip"]
    API --> BH["Best Hands"]
    API --> SEARCH["검색 필터"]
```

| 의존 항목 | 제공 팀 | WSOPTV 활용 |
|----------|---------|-------------|
| 핸드 타임스탬프 | GGP Archive | Hand Skip 자동 건너뛰기 |
| 베스트 핸드 선정 | GGP Archive | Best Hands 타임스탬프 점프 |
| 핸드 카테고리 | GGP Archive | 검색 필터링 |
| 플레이어 정보 | GGP Archive | 플레이어별 검색 |

---

*이전: [02-user-experience.md](./02-user-experience.md) | 메인: [README.md](./README.md)*
