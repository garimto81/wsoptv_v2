# PRD-0004: WSOPTV 상용 OTT 플랫폼 비즈니스 모델

**Version**: 1.0.0
**Status**: Draft
**Author**: Claude Code (AI)
**Created**: 2024-12-15
**Last Updated**: 2024-12-15
**Business Type**: B2C Subscription OTT Service

---

## 1. Executive Summary

### 1.1 비전

**WSOPTV**를 넷플릭스, 디즈니+ 수준의 정식 포커 전문 OTT 스트리밍 서비스로 전환합니다.

```mermaid
mindmap
  root((WSOPTV OTT))
    비즈니스
      구독 모델
      광고 수익
      PPV 이벤트
    사용자
      무료 회원
      프리미엄 회원
      VIP 회원
    콘텐츠
      무료 라이브러리
      프리미엄 전용
      독점 콘텐츠
    기술
      글로벌 CDN
      4K 스트리밍
      다중 디바이스
```

### 1.2 비즈니스 목표

| 목표 | 1년차 | 3년차 | 5년차 |
|------|-------|-------|-------|
| **MAU (Monthly Active Users)** | 10,000 | 100,000 | 500,000 |
| **유료 구독자** | 2,000 | 30,000 | 150,000 |
| **월간 매출 (KRW)** | 2천만 | 3억 | 15억 |
| **콘텐츠 라이브러리** | 500+ | 2,000+ | 5,000+ |

### 1.3 경쟁 분석

```mermaid
quadrantChart
    title OTT 포지셔닝 맵
    x-axis 저가 --> 고가
    y-axis 범용 콘텐츠 --> 전문 콘텐츠
    quadrant-1 프리미엄 니치
    quadrant-2 매스 프리미엄
    quadrant-3 매스 마켓
    quadrant-4 전문 저가

    "Netflix": [0.7, 0.3]
    "Disney+": [0.6, 0.4]
    "YouTube Premium": [0.4, 0.2]
    "PokerGO": [0.8, 0.9]
    "WSOPTV": [0.5, 0.95]
```

---

## 2. 사용자 여정 (User Journey)

### 2.1 전체 사용자 플로우

```mermaid
flowchart TB
    subgraph Acquisition["획득 단계"]
        Landing["랜딩 페이지<br/>wsoptv.com"]
        Marketing["마케팅 채널<br/>YouTube/SNS/검색"]
    end

    subgraph Registration["가입 단계"]
        SignUp["회원가입"]
        EmailVerify["이메일 인증"]
        Profile["프로필 설정"]
    end

    subgraph FreeTier["무료 체험"]
        FreeContent["무료 콘텐츠<br/>(제한된 라이브러리)"]
        FreeTrial["7일 무료 체험<br/>(프리미엄 전체)"]
    end

    subgraph Conversion["전환 단계"]
        PayWall["결제 유도 화면"]
        PlanSelect["플랜 선택"]
        Payment["결제"]
    end

    subgraph Premium["프리미엄 경험"]
        FullAccess["전체 콘텐츠"]
        Exclusive["독점 콘텐츠"]
        Features["프리미엄 기능"]
    end

    subgraph Retention["유지 단계"]
        Engagement["시청 활동"]
        Recommendation["추천 알고리즘"]
        Renewal["자동 갱신"]
    end

    Marketing --> Landing
    Landing --> SignUp
    SignUp --> EmailVerify
    EmailVerify --> Profile
    Profile --> FreeContent
    Profile --> FreeTrial

    FreeContent -->|"유료 콘텐츠 클릭"| PayWall
    FreeTrial -->|"7일 후"| PayWall

    PayWall --> PlanSelect
    PlanSelect --> Payment
    Payment --> FullAccess

    FullAccess --> Exclusive
    FullAccess --> Features
    FullAccess --> Engagement
    Engagement --> Recommendation
    Recommendation --> Renewal
    Renewal -->|"매월"| FullAccess
```

### 2.2 회원가입 상세 플로우

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as Frontend
    participant API as API Server
    participant Auth as Auth Service
    participant Email as Email Service
    participant DB as Database

    rect rgb(240, 248, 255)
        Note over User, DB: Step 1: 회원가입
        User->>FE: 1. 가입 버튼 클릭
        FE->>FE: 가입 모달 표시

        alt 이메일 가입
            User->>FE: 이메일/비밀번호 입력
            FE->>API: POST /auth/register
        else 소셜 로그인
            User->>FE: Google/Apple/Kakao 클릭
            FE->>API: POST /auth/oauth/{provider}
        end

        API->>Auth: 계정 생성
        Auth->>DB: INSERT user (status: UNVERIFIED)
        Auth->>Email: 인증 이메일 발송
        Email-->>User: 인증 링크 이메일
        API-->>FE: {user_id, needs_verification: true}
        FE-->>User: "이메일을 확인해주세요"
    end

    rect rgb(255, 248, 240)
        Note over User, DB: Step 2: 이메일 인증
        User->>Email: 인증 링크 클릭
        Email->>FE: /verify?token=xxx
        FE->>API: POST /auth/verify-email
        API->>Auth: 토큰 검증
        Auth->>DB: UPDATE status = VERIFIED
        Auth-->>API: Success
        API-->>FE: {verified: true}
        FE-->>User: "인증 완료! 로그인하세요"
    end

    rect rgb(240, 255, 240)
        Note over User, DB: Step 3: 첫 로그인 & 온보딩
        User->>FE: 로그인
        FE->>API: POST /auth/login
        API-->>FE: {token, user, is_first_login: true}
        FE->>FE: 온보딩 플로우 시작
        FE-->>User: 관심 장르/시리즈 선택
        User->>FE: 선호도 입력
        FE->>API: POST /users/preferences
        API-->>FE: 개인화 완료
        FE-->>User: 메인 페이지로 이동
    end
```

### 2.3 결제 플로우

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as Frontend
    participant API as API Server
    participant Sub as Subscription Service
    participant PG as Payment Gateway<br/>(Stripe/Toss)
    participant DB as Database

    User->>FE: 1. 구독 버튼 클릭
    FE->>FE: 플랜 선택 모달

    User->>FE: 2. 플랜 선택 (Premium)
    FE->>API: POST /subscriptions/checkout
    API->>Sub: 결제 세션 생성

    alt 신규 결제
        Sub->>PG: Create Checkout Session
        PG-->>Sub: {session_id, checkout_url}
    else 저장된 카드
        Sub->>PG: Charge saved payment method
        PG-->>Sub: {payment_intent}
    end

    Sub-->>API: {checkout_url or success}
    API-->>FE: Redirect to payment

    alt PG 리다이렉트
        FE->>PG: 결제 페이지
        User->>PG: 카드 정보 입력
        PG->>PG: 결제 처리
        PG-->>FE: Redirect /payment/success
    end

    FE->>API: POST /subscriptions/confirm
    API->>Sub: 구독 활성화
    Sub->>DB: INSERT subscription
    Sub->>DB: UPDATE user.tier = PREMIUM
    Sub-->>API: {subscription_id, expires_at}
    API-->>FE: Success
    FE-->>User: "구독이 활성화되었습니다!"

    Note over PG, DB: Webhook 처리
    PG->>API: Webhook: payment.succeeded
    API->>Sub: 결제 확인
    Sub->>DB: UPDATE payment_status = PAID
```

---

## 3. 구독 플랜 & 가격 정책

### 3.1 플랜 구조

```mermaid
flowchart TB
    subgraph Free["무료 플랜"]
        F1["제한된 콘텐츠<br/>(~50편)"]
        F2["광고 포함"]
        F3["720p 화질"]
        F4["1개 디바이스"]
    end

    subgraph Basic["Basic 플랜<br/>₩5,900/월"]
        B1["기본 라이브러리<br/>(~300편)"]
        B2["광고 없음"]
        B3["1080p HD"]
        B4["2개 디바이스"]
        B5["다운로드 X"]
    end

    subgraph Premium["Premium 플랜<br/>₩9,900/월"]
        P1["전체 라이브러리<br/>(500+편)"]
        P2["광고 없음"]
        P3["4K UHD + HDR"]
        P4["4개 디바이스"]
        P5["오프라인 다운로드"]
        P6["독점 콘텐츠"]
    end

    subgraph VIP["VIP 플랜<br/>₩19,900/월"]
        V1["Premium 전체"]
        V2["라이브 이벤트 무료"]
        V3["PPV 50% 할인"]
        V4["조기 접근"]
        V5["VIP 커뮤니티"]
        V6["월간 굿즈 박스"]
    end

    Free --> Basic
    Basic --> Premium
    Premium --> VIP
```

### 3.2 가격 비교표

| 기능 | 무료 | Basic | Premium | VIP |
|------|------|-------|---------|-----|
| **월 가격** | ₩0 | ₩5,900 | ₩9,900 | ₩19,900 |
| **연간 가격** | - | ₩59,000 (17% 할인) | ₩99,000 (17% 할인) | ₩199,000 (17% 할인) |
| **콘텐츠** | ~50편 | ~300편 | 전체 (500+) | 전체 + 독점 |
| **화질** | 720p | 1080p | 4K UHD | 4K UHD + HDR |
| **동시 시청** | 1 | 2 | 4 | 6 |
| **다운로드** | X | X | O (20편) | O (무제한) |
| **광고** | O | X | X | X |
| **라이브 이벤트** | X | 별도 구매 | 별도 구매 | 포함 |

### 3.3 수익 모델

```mermaid
pie title 예상 수익 구조 (3년차)
    "Premium 구독" : 45
    "VIP 구독" : 20
    "Basic 구독" : 15
    "PPV 이벤트" : 12
    "광고 (무료 유저)" : 5
    "파트너십/스폰서" : 3
```

---

## 4. 콘텐츠 전략

### 4.1 콘텐츠 티어링

```mermaid
flowchart LR
    subgraph FreeContent["무료 콘텐츠"]
        FC1["클래식 시리즈<br/>(2년+ 경과)"]
        FC2["하이라이트 클립<br/>(5-15분)"]
        FC3["교육 콘텐츠<br/>(초보자용)"]
        FC4["예고편/티저"]
    end

    subgraph BasicContent["Basic 콘텐츠"]
        BC1["일반 시리즈<br/>(1년+ 경과)"]
        BC2["풀 에피소드"]
        BC3["시즌 아카이브"]
    end

    subgraph PremiumContent["Premium 콘텐츠"]
        PC1["최신 시리즈<br/>(1년 미만)"]
        PC2["4K 리마스터"]
        PC3["비하인드 씬"]
        PC4["프로 해설판"]
    end

    subgraph ExclusiveContent["독점 콘텐츠"]
        EC1["WSOPTV 오리지널"]
        EC2["프로 인터뷰"]
        EC3["전략 마스터클래스"]
        EC4["라이브 이벤트"]
    end

    FreeContent --> BasicContent
    BasicContent --> PremiumContent
    PremiumContent --> ExclusiveContent
```

### 4.2 콘텐츠 라이브러리 구조

| 카테고리 | 무료 | Basic | Premium | 예시 |
|----------|------|-------|---------|------|
| **WSOP** | 2019 이전 | 2020-2022 | 2023-현재 | Main Event, Side Events |
| **HCL** | 시즌 1-5 | 시즌 6-10 | 시즌 11+ | High Stakes, Special |
| **GGMillions** | 하이라이트만 | 일부 이벤트 | 전체 | Super High Roller |
| **오리지널** | 예고편만 | X | 전체 | 다큐, 인터뷰 |
| **라이브** | X | X | VIP만 | 실시간 이벤트 |

### 4.3 콘텐츠 릴리스 전략

```mermaid
gantt
    title 콘텐츠 릴리스 윈도우
    dateFormat YYYY-MM-DD

    section 라이브
    실시간 방송      :live, 2024-01-01, 1d

    section VIP
    VIP 조기 접근    :vip, after live, 7d

    section Premium
    Premium 공개     :premium, after vip, 30d

    section Basic
    Basic 공개       :basic, after premium, 180d

    section Free
    무료 공개        :free, after basic, 365d
```

---

## 5. 시스템 아키텍처 (상용 버전)

### 5.1 전체 인프라 아키텍처

```mermaid
flowchart TB
    subgraph Users["사용자"]
        Web["Web<br/>(Next.js)"]
        Mobile["Mobile App<br/>(React Native)"]
        TV["Smart TV<br/>(Tizen/webOS)"]
    end

    subgraph Edge["Edge Layer"]
        CDN["CloudFront CDN<br/>(글로벌 배포)"]
        WAF["AWS WAF<br/>(보안)"]
    end

    subgraph LoadBalancer["Load Balancing"]
        ALB["Application<br/>Load Balancer"]
    end

    subgraph Backend["Backend Services (EKS)"]
        subgraph Core["Core Services"]
            API["API Gateway"]
            Auth["Auth Service"]
            User["User Service"]
            Content["Content Service"]
        end

        subgraph Business["Business Services"]
            Sub["Subscription<br/>Service"]
            Payment["Payment<br/>Service"]
            Billing["Billing<br/>Service"]
        end

        subgraph Streaming["Streaming Services"]
            Stream["Stream<br/>Service"]
            Transcode["Transcoding<br/>Service"]
            DRM["DRM Service<br/>(Widevine)"]
        end

        subgraph Analytics["Analytics"]
            Event["Event<br/>Collector"]
            Recommend["Recommendation<br/>Engine"]
            Report["Reporting<br/>Service"]
        end
    end

    subgraph Data["Data Layer"]
        PostgreSQL["PostgreSQL<br/>(RDS)"]
        Redis["Redis<br/>(ElastiCache)"]
        S3["S3<br/>(Media Storage)"]
        ES["Elasticsearch<br/>(Search)"]
    end

    subgraph External["External Services"]
        Stripe["Stripe<br/>(Global)"]
        Toss["Toss Payments<br/>(Korea)"]
        SendGrid["SendGrid<br/>(Email)"]
        Firebase["Firebase<br/>(Push)"]
    end

    Users --> CDN
    CDN --> WAF
    WAF --> ALB
    ALB --> Backend

    Core --> Data
    Business --> Data
    Streaming --> Data
    Analytics --> Data

    Payment --> Stripe
    Payment --> Toss
    Auth --> SendGrid
    User --> Firebase
```

### 5.2 스트리밍 파이프라인

```mermaid
flowchart LR
    subgraph Ingest["수집"]
        Source["원본 파일<br/>(MP4/MKV)"]
        Upload["업로드<br/>서비스"]
    end

    subgraph Process["처리"]
        Queue["SQS Queue"]
        Transcode["MediaConvert<br/>트랜스코딩"]
        Package["패키징<br/>(HLS/DASH)"]
    end

    subgraph Protect["보호"]
        DRM["DRM 암호화<br/>(Widevine/FairPlay)"]
        Watermark["워터마킹"]
    end

    subgraph Deliver["배포"]
        S3["S3 Origin"]
        CDN["CloudFront<br/>CDN"]
    end

    subgraph Play["재생"]
        Player["비디오 플레이어<br/>(Shaka/Video.js)"]
    end

    Source --> Upload
    Upload --> Queue
    Queue --> Transcode

    Transcode --> |"4K"| Package
    Transcode --> |"1080p"| Package
    Transcode --> |"720p"| Package
    Transcode --> |"480p"| Package

    Package --> DRM
    DRM --> Watermark
    Watermark --> S3
    S3 --> CDN
    CDN --> Player
```

### 5.3 결제 시스템 아키텍처

```mermaid
flowchart TB
    subgraph Client["클라이언트"]
        App["Web/Mobile App"]
    end

    subgraph Gateway["결제 게이트웨이"]
        Router["Payment Router"]

        subgraph Global["글로벌"]
            Stripe["Stripe"]
            PayPal["PayPal"]
        end

        subgraph Korea["한국"]
            Toss["토스페이먼츠"]
            Kakao["카카오페이"]
            Naver["네이버페이"]
        end
    end

    subgraph Backend["Backend"]
        PaymentSvc["Payment Service"]
        SubSvc["Subscription Service"]
        BillingSvc["Billing Service"]

        subgraph Events["이벤트 처리"]
            Webhook["Webhook Handler"]
            Retry["Retry Queue"]
        end
    end

    subgraph Data["데이터"]
        PaymentDB[("Payments DB")]
        SubDB[("Subscriptions DB")]
        AuditLog[("Audit Log")]
    end

    App --> Router
    Router --> Global
    Router --> Korea

    Global --> Webhook
    Korea --> Webhook

    Webhook --> PaymentSvc
    PaymentSvc --> SubSvc
    SubSvc --> BillingSvc

    PaymentSvc --> PaymentDB
    SubSvc --> SubDB
    BillingSvc --> AuditLog

    Webhook --> Retry
    Retry --> PaymentSvc
```

---

## 6. 데이터 모델 (상용 확장)

### 6.1 핵심 엔티티

```mermaid
erDiagram
    User ||--o{ Subscription : has
    User ||--o{ Payment : makes
    User ||--o{ WatchHistory : has
    User ||--o{ Device : owns
    User ||--o{ Preference : has

    Subscription ||--|| Plan : based_on
    Subscription ||--o{ Invoice : generates

    Payment ||--|| Invoice : pays

    Content ||--o{ WatchHistory : tracked_in
    Content ||--|| ContentTier : belongs_to
    Content ||--o{ ContentAccess : controlled_by

    Plan ||--o{ PlanFeature : includes
    Plan ||--o{ ContentAccess : grants

    User {
        uuid id PK
        string email UK
        string password_hash
        string phone
        enum status "UNVERIFIED|ACTIVE|SUSPENDED"
        enum tier "FREE|BASIC|PREMIUM|VIP"
        datetime email_verified_at
        datetime created_at
        datetime last_login_at
    }

    Subscription {
        uuid id PK
        uuid user_id FK
        uuid plan_id FK
        enum status "TRIAL|ACTIVE|CANCELLED|EXPIRED"
        datetime trial_ends_at
        datetime current_period_start
        datetime current_period_end
        boolean auto_renew
        string stripe_subscription_id
    }

    Plan {
        uuid id PK
        string name "FREE|BASIC|PREMIUM|VIP"
        decimal price_monthly
        decimal price_yearly
        int max_devices
        int max_downloads
        string max_quality "720p|1080p|4K"
        boolean ads_free
        boolean live_access
    }

    Payment {
        uuid id PK
        uuid user_id FK
        uuid invoice_id FK
        decimal amount
        string currency
        enum status "PENDING|COMPLETED|FAILED|REFUNDED"
        string provider "stripe|toss|kakao"
        string provider_payment_id
        datetime paid_at
    }

    Invoice {
        uuid id PK
        uuid subscription_id FK
        string invoice_number UK
        decimal subtotal
        decimal tax
        decimal total
        enum status "DRAFT|OPEN|PAID|VOID"
        datetime due_date
        datetime paid_at
    }

    Content {
        uuid id PK
        string title
        string description
        uuid tier_id FK
        int duration_seconds
        string thumbnail_url
        int release_year
        datetime available_from
        datetime premium_until
        boolean is_original
    }

    ContentTier {
        uuid id PK
        string name "FREE|BASIC|PREMIUM|EXCLUSIVE"
        int priority
    }

    Device {
        uuid id PK
        uuid user_id FK
        string device_id UK
        string device_type "WEB|IOS|ANDROID|TV"
        string device_name
        datetime last_active_at
        boolean is_active
    }

    WatchHistory {
        uuid id PK
        uuid user_id FK
        uuid content_id FK
        int position_seconds
        int duration_seconds
        float progress_percent
        datetime watched_at
        boolean completed
    }
```

### 6.2 구독 상태 전이

```mermaid
stateDiagram-v2
    [*] --> Unverified: 회원가입

    Unverified --> Active: 이메일 인증
    Unverified --> [*]: 미인증 만료 (7일)

    state Active {
        [*] --> Free: 기본
        Free --> Trial: 무료 체험 시작
        Trial --> Subscribed: 결제 완료
        Trial --> Free: 체험 만료
        Free --> Subscribed: 직접 구독
        Subscribed --> Free: 구독 취소/만료
    }

    Active --> Suspended: 정지
    Suspended --> Active: 정지 해제

    Active --> [*]: 계정 삭제

    note right of Trial
        7일 무료 체험
        카드 등록 필요
    end note

    note right of Subscribed
        Basic/Premium/VIP
        자동 갱신
    end note
```

---

## 7. API 설계 (상용 확장)

### 7.1 API 엔드포인트 구조

```mermaid
flowchart LR
    subgraph Auth["/api/v1/auth"]
        A1["POST /register"]
        A2["POST /login"]
        A3["POST /logout"]
        A4["POST /verify-email"]
        A5["POST /forgot-password"]
        A6["POST /reset-password"]
        A7["POST /oauth/{provider}"]
        A8["POST /refresh-token"]
    end

    subgraph User["/api/v1/users"]
        U1["GET /me"]
        U2["PATCH /me"]
        U3["GET /me/preferences"]
        U4["PUT /me/preferences"]
        U5["GET /me/devices"]
        U6["DELETE /me/devices/{id}"]
        U7["GET /me/watch-history"]
    end

    subgraph Sub["/api/v1/subscriptions"]
        S1["GET /plans"]
        S2["GET /current"]
        S3["POST /checkout"]
        S4["POST /change-plan"]
        S5["POST /cancel"]
        S6["POST /resume"]
        S7["GET /invoices"]
        S8["GET /payment-methods"]
        S9["POST /payment-methods"]
    end

    subgraph Content["/api/v1/content"]
        C1["GET /"]
        C2["GET /{id}"]
        C3["GET /featured"]
        C4["GET /categories"]
        C5["GET /search"]
        C6["GET /recommendations"]
        C7["POST /{id}/progress"]
        C8["GET /{id}/stream-url"]
    end

    subgraph Admin["/api/v1/admin"]
        AD1["GET /dashboard"]
        AD2["GET /users"]
        AD3["GET /subscriptions"]
        AD4["GET /revenue"]
        AD5["GET /content-stats"]
    end
```

### 7.2 주요 API 상세

| 카테고리 | Method | Endpoint | Request | Response | Auth |
|----------|--------|----------|---------|----------|------|
| **인증** | POST | `/auth/register` | `{email, password, name}` | `{user_id, verification_sent}` | - |
| | POST | `/auth/login` | `{email, password}` | `{access_token, refresh_token, user}` | - |
| | POST | `/auth/oauth/google` | `{id_token}` | `{access_token, user}` | - |
| | POST | `/auth/verify-email` | `{token}` | `{verified: true}` | - |
| **구독** | GET | `/subscriptions/plans` | - | `Plan[]` | - |
| | POST | `/subscriptions/checkout` | `{plan_id, payment_method}` | `{checkout_url}` | Bearer |
| | POST | `/subscriptions/cancel` | `{reason?}` | `{cancelled_at}` | Bearer |
| | GET | `/subscriptions/invoices` | `?page&limit` | `{invoices[], total}` | Bearer |
| **콘텐츠** | GET | `/content/` | `?tier&category&page` | `{items[], total}` | Bearer? |
| | GET | `/content/{id}/stream-url` | - | `{manifest_url, drm_license_url}` | Bearer |
| | POST | `/content/{id}/progress` | `{position, duration}` | `{saved: true}` | Bearer |
| **Webhook** | POST | `/webhooks/stripe` | Stripe Event | `200 OK` | Stripe Sig |
| | POST | `/webhooks/toss` | Toss Event | `200 OK` | Toss Sig |

---

## 8. UI/UX 디자인

### 8.1 주요 화면 구성

```mermaid
flowchart TB
    subgraph Landing["랜딩 페이지"]
        Hero["히어로 섹션<br/>CTA: 무료 시작하기"]
        Features["기능 소개"]
        Plans["플랜 비교"]
        FAQ["자주 묻는 질문"]
    end

    subgraph Auth["인증"]
        Login["로그인"]
        Register["회원가입"]
        Verify["이메일 인증"]
        Onboard["온보딩"]
    end

    subgraph Main["메인 (로그인 후)"]
        Home["홈<br/>- 이어보기<br/>- 추천<br/>- 신규"]
        Browse["탐색<br/>- 카테고리별<br/>- 시리즈별"]
        Search["검색<br/>- 자동완성<br/>- 필터"]
        Detail["콘텐츠 상세<br/>- 정보<br/>- 에피소드"]
        Player["플레이어<br/>- 재생 컨트롤<br/>- 화질 선택"]
    end

    subgraph Account["계정"]
        Profile["프로필"]
        Subscription["구독 관리"]
        Billing["결제 내역"]
        Devices["디바이스 관리"]
        Settings["설정"]
    end

    subgraph Premium["프리미엄 전용"]
        Download["다운로드"]
        Live["라이브 이벤트"]
        Exclusive["독점 콘텐츠"]
    end

    Landing --> Auth
    Auth --> Main
    Main --> Account
    Main --> Premium
```

### 8.2 홈 화면 레이아웃

```mermaid
flowchart TB
    subgraph Home["홈 화면"]
        subgraph Header["헤더"]
            Logo["WSOPTV"]
            Nav["홈 | 시리즈 | 라이브 | 내 리스트"]
            Search["검색"]
            Profile["프로필"]
        end

        subgraph Hero["히어로 배너"]
            Featured["추천 콘텐츠<br/>자동 재생 예고편"]
            CTA["▶ 재생  |  + 내 리스트"]
        end

        subgraph Continue["이어보기"]
            C1["📺 45%"]
            C2["📺 20%"]
            C3["📺 75%"]
        end

        subgraph ForYou["당신을 위한 추천"]
            R1["📺"]
            R2["📺"]
            R3["📺"]
            R4["📺"]
        end

        subgraph NewRelease["신규 콘텐츠"]
            N1["🆕"]
            N2["🆕"]
            N3["🆕"]
            N4["🆕"]
        end

        subgraph WSOP["WSOP 시리즈"]
            W1["📺"]
            W2["📺"]
            W3["📺"]
            W4["📺"]
        end
    end

    Header --> Hero
    Hero --> Continue
    Continue --> ForYou
    ForYou --> NewRelease
    NewRelease --> WSOP
```

### 8.3 결제 화면 플로우

```mermaid
flowchart LR
    subgraph Step1["Step 1: 플랜 선택"]
        Plans["플랜 카드 3개<br/>Basic | Premium | VIP"]
        Compare["기능 비교표"]
    end

    subgraph Step2["Step 2: 결제 정보"]
        Card["카드 정보 입력"]
        Saved["저장된 카드 선택"]
        Other["간편결제<br/>카카오|네이버|토스"]
    end

    subgraph Step3["Step 3: 확인"]
        Summary["주문 요약<br/>플랜: Premium<br/>₩9,900/월"]
        Terms["이용약관 동의"]
        Submit["결제하기"]
    end

    subgraph Step4["Step 4: 완료"]
        Success["결제 완료!<br/>프리미엄 이용 가능"]
        Receipt["영수증 이메일 발송"]
        Start["시청 시작하기"]
    end

    Step1 --> Step2
    Step2 --> Step3
    Step3 --> Step4
```

---

## 9. 마케팅 & 성장 전략

### 9.1 사용자 획득 퍼널

```mermaid
flowchart TB
    subgraph Awareness["인지 (Awareness)"]
        SEO["SEO/SEM"]
        Social["소셜 미디어"]
        Influencer["인플루언서"]
        Partnership["파트너십"]
    end

    subgraph Interest["관심 (Interest)"]
        Landing["랜딩 페이지"]
        FreeSample["무료 샘플"]
        Trailer["예고편"]
    end

    subgraph Consideration["고려 (Consideration)"]
        SignUp["회원가입"]
        FreeTrial["7일 무료 체험"]
        FreeContent["무료 콘텐츠"]
    end

    subgraph Conversion["전환 (Conversion)"]
        Subscribe["유료 구독"]
        Upgrade["플랜 업그레이드"]
    end

    subgraph Retention["유지 (Retention)"]
        Engagement["지속적 시청"]
        Loyalty["로열티 프로그램"]
        Referral["친구 추천"]
    end

    Awareness --> Interest
    Interest --> Consideration
    Consideration --> Conversion
    Conversion --> Retention
    Retention -->|"추천"| Awareness
```

### 9.2 핵심 성과 지표 (KPI)

| 카테고리 | 지표 | 목표 (1년차) | 측정 방법 |
|----------|------|-------------|-----------|
| **획득** | CAC (Customer Acquisition Cost) | < ₩15,000 | 마케팅 비용 / 신규 유료 유저 |
| | 회원가입 전환율 | > 5% | 가입자 / 방문자 |
| **전환** | 무료→유료 전환율 | > 8% | 유료 구독자 / 전체 가입자 |
| | 체험→유료 전환율 | > 30% | 체험 후 유료 / 체험 시작 |
| **유지** | 월간 이탈률 | < 5% | 취소자 / 전월 구독자 |
| | LTV (Lifetime Value) | > ₩120,000 | 평균 구독 기간 × ARPU |
| **참여** | DAU/MAU | > 40% | 일 활성 / 월 활성 |
| | 평균 시청 시간 | > 60분/일 | 총 시청 시간 / DAU |

### 9.3 수익 예측

```mermaid
xychart-beta
    title "월간 수익 예측 (단위: 백만원)"
    x-axis ["M1", "M3", "M6", "M9", "M12", "M18", "M24", "M36"]
    y-axis "매출" 0 --> 400
    bar [5, 15, 35, 55, 80, 150, 220, 350]
    line [5, 15, 35, 55, 80, 150, 220, 350]
```

---

## 10. 법적 & 규정 준수

### 10.1 필수 준수 사항

| 영역 | 규정 | 요구사항 |
|------|------|----------|
| **개인정보** | GDPR | EU 사용자 데이터 처리 동의, 삭제권 |
| | 개인정보보호법 | 국내 개인정보 처리방침, 동의 |
| **결제** | PCI-DSS | 카드 정보 직접 저장 금지 (PG 위임) |
| | 전자상거래법 | 청약철회, 환불 정책 고지 |
| **콘텐츠** | 저작권법 | 라이선스 계약, DRM 적용 |
| | 청소년보호법 | 연령 인증 (필요시) |
| **서비스** | 전자금융거래법 | 전자금융업 등록 (간편결제시) |
| | 통신비밀보호법 | 통신자료 제공 절차 |

### 10.2 이용약관 구조

```mermaid
flowchart TB
    subgraph Terms["이용약관"]
        T1["서비스 이용약관"]
        T2["개인정보처리방침"]
        T3["유료 서비스 이용약관"]
        T4["환불 정책"]
        T5["저작권 정책"]
    end

    subgraph Consent["동의 필요 시점"]
        C1["회원가입: T1, T2"]
        C2["유료 결제: T3, T4"]
        C3["콘텐츠 업로드: T5"]
    end

    Terms --> Consent
```

---

## 11. 개발 로드맵

### 11.1 Phase별 계획

```mermaid
gantt
    title WSOPTV 상용화 로드맵
    dateFormat YYYY-MM-DD

    section Phase 1: MVP
    인증 시스템 (이메일/소셜)      :p1-1, 2024-12-20, 14d
    결제 통합 (Stripe)            :p1-2, after p1-1, 14d
    구독 관리 시스템               :p1-3, after p1-2, 10d
    콘텐츠 티어링                  :p1-4, after p1-3, 7d
    MVP 출시                       :milestone, after p1-4, 0d

    section Phase 2: 성장
    국내 결제 (토스/카카오)        :p2-1, 2025-02-01, 14d
    추천 알고리즘                  :p2-2, after p2-1, 21d
    모바일 앱 (iOS)               :p2-3, after p2-2, 30d
    모바일 앱 (Android)           :p2-4, after p2-3, 30d

    section Phase 3: 확장
    라이브 스트리밍               :p3-1, 2025-06-01, 30d
    스마트 TV 앱                  :p3-2, after p3-1, 30d
    다국어 지원                   :p3-3, after p3-2, 21d
    글로벌 CDN                    :p3-4, after p3-3, 14d

    section Phase 4: 성숙
    오리지널 콘텐츠 제작          :p4-1, 2025-10-01, 90d
    커뮤니티 기능                 :p4-2, after p4-1, 30d
    AI 개인화                     :p4-3, after p4-2, 30d
```

### 11.2 Phase 상세

| Phase | 목표 | 주요 기능 | 기간 |
|-------|------|-----------|------|
| **Phase 1: MVP** | 유료 서비스 출시 | 회원가입, 결제, 구독, 스트리밍 | 2개월 |
| **Phase 2: 성장** | 사용자 확대 | 국내 결제, 추천, 모바일 앱 | 4개월 |
| **Phase 3: 확장** | 플랫폼 확장 | 라이브, TV 앱, 글로벌 | 4개월 |
| **Phase 4: 성숙** | 차별화 | 오리지널, 커뮤니티, AI | 지속 |

---

## 12. 운영 & 지원

### 12.1 고객 지원 구조

```mermaid
flowchart TB
    subgraph Support["고객 지원"]
        subgraph Tier1["Tier 1: 셀프 서비스"]
            FAQ["FAQ"]
            Help["도움말 센터"]
            Chatbot["AI 챗봇"]
        end

        subgraph Tier2["Tier 2: 기본 지원"]
            Email["이메일 문의"]
            Chat["실시간 채팅"]
            Ticket["티켓 시스템"]
        end

        subgraph Tier3["Tier 3: 전문 지원"]
            Phone["전화 상담<br/>(VIP 전용)"]
            Expert["기술 전문가"]
            Account["계정 담당자"]
        end
    end

    subgraph SLA["SLA"]
        S1["일반: 24시간 응답"]
        S2["Premium: 4시간 응답"]
        S3["VIP: 1시간 응답"]
    end

    Tier1 --> Tier2
    Tier2 --> Tier3
    Support --> SLA
```

### 12.2 모니터링 & 알림

| 영역 | 도구 | 알림 조건 |
|------|------|----------|
| **인프라** | CloudWatch, Datadog | CPU > 80%, 에러율 > 1% |
| **비즈니스** | Amplitude, Mixpanel | 전환율 급감, 이탈 급증 |
| **결제** | Stripe Dashboard | 결제 실패율 > 5% |
| **보안** | AWS GuardDuty | 이상 접근 탐지 |

---

## 13. 리스크 관리

### 13.1 리스크 매트릭스

```mermaid
quadrantChart
    title 리스크 평가 매트릭스
    x-axis 낮은 영향 --> 높은 영향
    y-axis 낮은 확률 --> 높은 확률
    quadrant-1 적극 관리
    quadrant-2 모니터링
    quadrant-3 수용
    quadrant-4 대응 계획

    "결제 장애": [0.9, 0.3]
    "저작권 분쟁": [0.8, 0.2]
    "서버 다운": [0.7, 0.4]
    "데이터 유출": [0.95, 0.1]
    "경쟁사 진입": [0.5, 0.6]
    "이탈률 증가": [0.6, 0.5]
    "CDN 장애": [0.4, 0.3]
```

### 13.2 리스크 대응 계획

| 리스크 | 영향 | 확률 | 대응 전략 |
|--------|------|------|-----------|
| 결제 장애 | High | Medium | 다중 PG, 자동 failover |
| 저작권 분쟁 | High | Low | 법무 검토, 라이선스 명확화 |
| 서버 다운 | High | Medium | Auto-scaling, 다중 AZ |
| 데이터 유출 | Critical | Low | 암호화, 보안 감사 |
| 경쟁사 진입 | Medium | High | 콘텐츠 차별화, 커뮤니티 |
| 이탈률 증가 | Medium | Medium | 추천 개선, 신규 콘텐츠 |

---

## 14. 부록

### A. 경쟁사 분석

| 서비스 | 가격 | 콘텐츠 | 강점 | 약점 |
|--------|------|--------|------|------|
| **PokerGO** | $14.99/월 | WSOP 독점 | 브랜드 파워 | 가격 높음 |
| **Poker Central** | 무료+광고 | 다양한 쇼 | 접근성 | 광고 피로 |
| **YouTube** | 무료 | 하이라이트 | 무료 | 정리 안됨 |
| **WSOPTV** | ₩9,900/월 | 다양한 시리즈 | 가격 경쟁력 | 브랜드 인지도 |

### B. 기술 스택

| 레이어 | 기술 | 버전 |
|--------|------|------|
| **Frontend** | Next.js | 14.x |
| | React Native | 0.73 |
| | TypeScript | 5.x |
| **Backend** | FastAPI | 0.115 |
| | Python | 3.12 |
| | Celery | 5.x |
| **Database** | PostgreSQL | 16 |
| | Redis | 7 |
| | Elasticsearch | 8.x |
| **Infrastructure** | AWS EKS | - |
| | CloudFront | - |
| | S3 | - |
| **Payment** | Stripe | API v2024 |
| | Toss Payments | - |
| **Streaming** | MediaConvert | - |
| | Shaka Player | 4.x |
| | Widevine DRM | - |

### C. 환경 변수

```env
# Application
APP_ENV=production
APP_URL=https://wsoptv.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/wsoptv
REDIS_URL=redis://host:6379/0

# Payment
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
TOSS_SECRET_KEY=xxx
TOSS_CLIENT_KEY=xxx

# AWS
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=ap-northeast-2
CLOUDFRONT_DISTRIBUTION_ID=xxx
S3_BUCKET_MEDIA=wsoptv-media

# DRM
WIDEVINE_LICENSE_URL=xxx
FAIRPLAY_LICENSE_URL=xxx

# Email
SENDGRID_API_KEY=xxx

# Analytics
AMPLITUDE_API_KEY=xxx
MIXPANEL_TOKEN=xxx
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2024-12-15 | Claude Code | 상용 OTT 비즈니스 모델 PRD 초안 |
