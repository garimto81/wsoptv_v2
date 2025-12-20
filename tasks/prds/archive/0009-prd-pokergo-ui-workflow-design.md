# PokerGO 홈페이지 - 클릭하면 뭐가 되나요?

**문서 번호**: PRD-0009 | **버전**: 8.0.0 | **작성일**: 2025-12-15

> 이 문서는 PokerGO 홈페이지의 **모든 버튼과 링크**를 눌렀을 때 어떤 일이 일어나는지 설명합니다.

---

## 전체 홈페이지 구조

```mermaid
flowchart TB
    subgraph PAGE["🏠 PokerGO 홈페이지"]
        direction TB

        subgraph HEADER["1️⃣ 상단 메뉴 (항상 보임)"]
            LOGO["🎰 로고"]
            NAV["Home | Schedule | On-Demand | Poker U | News"]
            ICONS["🔍 👤"]
        end

        subgraph HERO["2️⃣ 메인 배너 (가장 큰 영역)"]
            TITLE["POT True Classic 2025\nFinal Table"]
            WATCH["▶ Watch Now"]
            POSTER["🖼️ 선수 사진"]
        end

        subgraph INTEREST["3️⃣ 관심 콘텐츠"]
            CARD1["📺 영상 카드 1"]
            CARD2["📺 영상 카드 2"]
        end

        subgraph SERIES["4️⃣ 이번 주의 시리즈"]
            SERIES_POSTER["📁 시리즈 포스터"]
            EP_LIST["Episode 1\nEpisode 2\nEpisode 3\nEpisode 4"]
        end

        subgraph RECENT["5️⃣ 최근 추가"]
            NEW1["📺 새 영상 1"]
            NEW2["📺 새 영상 2"]
        end

        subgraph TRENDING["6️⃣ 인기 영상"]
            HOT1["🔥 인기 1"]
            HOT2["🔥 인기 2"]
            ARROWS1["◀ ▶"]
        end

        subgraph CONTINUE["7️⃣ 이어보기 ⭐"]
            RESUME1["▓▓▓░░ 45%"]
            RESUME2["▓▓░░░ 25%"]
            ARROWS2["◀ ▶"]
        end

        subgraph FOOTER["8️⃣ 하단 메뉴"]
            SNS["📘 ✖ 📷 ▶"]
            LINKS["About | FAQ | Contact | Terms"]
        end
    end
```

---

## 1️⃣ 상단 메뉴 - 클릭하면?

```mermaid
flowchart LR
    subgraph HEADER["상단 메뉴 (항상 화면 위에 고정)"]
        LOGO["🎰 pokerGO\n로고"]
        HOME["Home\n(빨간색)"]
        SCHEDULE["Schedule"]
        ONDEMAND["On-Demand"]
        POKERU["Poker U"]
        NEWS["News"]
        SEARCH["🔍"]
        PROFILE["👤"]
    end

    LOGO -.->|"💬 클릭하면"| R1["🏠 홈으로 이동!"]
    HOME -.->|"💬 지금 여기!"| R2["현재 페이지"]
    SCHEDULE -.->|"💬 클릭하면"| R3["📅 생방송 일정표"]
    ONDEMAND -.->|"💬 클릭하면"| R4["📚 다시보기 목록"]
    POKERU -.->|"💬 클릭하면"| R5["🎓 포커 강의 영상"]
    NEWS -.->|"💬 클릭하면"| R6["📰 포커 뉴스"]
    SEARCH -.->|"💬 클릭하면"| R7["🔍 검색창 열림!"]
    PROFILE -.->|"💬 클릭하면"| R8["👤 내 계정 메뉴"]

    style HOME fill:#e53935,color:#fff
    style R1 fill:#e8f5e9
    style R3 fill:#e8f5e9
    style R4 fill:#e8f5e9
    style R5 fill:#e8f5e9
    style R6 fill:#e8f5e9
    style R7 fill:#fff3e0
    style R8 fill:#fff3e0
```

---

## 2️⃣ 메인 배너 - 클릭하면?

```mermaid
flowchart TB
    subgraph HERO["메인 배너 (가장 큰 영역)"]
        direction LR

        subgraph LEFT["왼쪽 - 텍스트"]
            TITLE["🏆 POT True Classic\nRags To Riches 2025\nFinal Table"]
            DESC["The POT True Classic is down to\nthe final table of seven players..."]
            WATCH["▶ Watch Now\n(보라색 버튼)"]
        end

        subgraph RIGHT["오른쪽 - 이미지"]
            POSTER["🖼️\n\n선수들 사진\n\n🃏"]
        end
    end

    WATCH ==>|"💬 클릭하면"| PLAY["▶ 바로 재생!\n이 영상을 지금 바로\n볼 수 있어요"]
    POSTER -.->|"💬 클릭하면"| DETAIL["📋 상세 페이지\n줄거리, 출연진 등\n자세한 정보 보기"]

    style WATCH fill:#9f26b5,color:#fff
    style PLAY fill:#e8f5e9,stroke:#4caf50,stroke-width:3px
    style DETAIL fill:#e3f2fd
```

---

## 3️⃣ 관심 콘텐츠 - 클릭하면?

```mermaid
flowchart TB
    subgraph INTEREST["Of Interest (관심 가질만한 영상)"]
        direction LR

        subgraph CARD1["카드 1"]
            IMG1["🖼️ 썸네일"]
            T1["POT True Classic Day 2\nDec 05, 08:00 AM"]
        end

        subgraph CARD2["카드 2"]
            IMG2["🖼️ 썸네일"]
            T2["Triton PO Final Table\nDec 05, 05:00 AM"]
        end
    end

    CARD1 ==>|"💬 카드 클릭!"| PLAY1["▶ 바로 재생!"]
    CARD2 ==>|"💬 카드 클릭!"| PLAY2["▶ 바로 재생!"]

    style PLAY1 fill:#e8f5e9,stroke:#4caf50,stroke-width:3px
    style PLAY2 fill:#e8f5e9,stroke:#4caf50,stroke-width:3px
```

---

## 4️⃣ 이번 주의 시리즈 - 클릭하면?

```mermaid
flowchart TB
    subgraph SERIES["Series of the Week (이번 주 추천 시리즈)"]
        direction LR

        subgraph POSTER_AREA["왼쪽 - 포스터"]
            POSTER["📁\nNO GAMBLE,\nNO FUTURE\n\nSEASON 8\nby PokerStars"]
        end

        subgraph EPISODE_LIST["오른쪽 - 에피소드 목록"]
            EP1["▶ Episode 1"]
            EP2["▶ Episode 2"]
            EP3["▶ Episode 3"]
            EP4["▶ Episode 4"]
        end
    end

    POSTER -.->|"💬 포스터 클릭"| SERIES_PAGE["📚 시리즈 전체 보기\n모든 회차 목록"]

    EP1 ==>|"💬 클릭"| P1["▶ 1화 재생!"]
    EP2 ==>|"💬 클릭"| P2["▶ 2화 재생!"]
    EP3 ==>|"💬 클릭"| P3["▶ 3화 재생!"]
    EP4 ==>|"💬 클릭"| P4["▶ 4화 재생!"]

    style SERIES_PAGE fill:#e3f2fd
    style P1 fill:#e8f5e9,stroke:#4caf50,stroke-width:3px
    style P2 fill:#e8f5e9,stroke:#4caf50,stroke-width:3px
    style P3 fill:#e8f5e9,stroke:#4caf50,stroke-width:3px
    style P4 fill:#e8f5e9,stroke:#4caf50,stroke-width:3px
```

---

## 5️⃣ 최근 추가된 영상 - 클릭하면?

```mermaid
flowchart TB
    subgraph RECENT["Recently Added (새로 올라온 영상)"]
        direction LR

        subgraph NEW1["새 영상 1"]
            I1["🖼️ 썸네일"]
            N1["Joseph clipping\n12-13-25"]
        end

        subgraph NEW2["새 영상 2"]
            I2["🖼️ 썸네일"]
            N2["PokerAtlas Tour\nChampionship"]
        end
    end

    NEW1 ==>|"💬 클릭!"| PLAY1["▶ 바로 재생!"]
    NEW2 ==>|"💬 클릭!"| PLAY2["▶ 바로 재생!"]

    style PLAY1 fill:#e8f5e9,stroke:#4caf50,stroke-width:3px
    style PLAY2 fill:#e8f5e9,stroke:#4caf50,stroke-width:3px
```

---

## 6️⃣ 인기 영상 - 클릭하면?

```mermaid
flowchart TB
    subgraph TRENDING["Trending (요즘 많이 보는 영상)"]
        direction LR

        ARROWS["◀ ▶\n화살표"]

        subgraph HOT1["인기 1"]
            H1["🔥 썸네일"]
            HT1["POT True Classic\nDec 09"]
        end

        subgraph HOT2["인기 2"]
            H2["🔥 썸네일"]
            HT2["POT True Classic\nDec 02"]
        end
    end

    HOT1 ==>|"💬 클릭!"| PLAY1["▶ 바로 재생!"]
    HOT2 ==>|"💬 클릭!"| PLAY2["▶ 바로 재생!"]
    ARROWS -.->|"💬 클릭"| MORE["👉 더 많은 인기 영상\n(좌우로 넘기기)"]

    style PLAY1 fill:#e8f5e9,stroke:#4caf50,stroke-width:3px
    style PLAY2 fill:#e8f5e9,stroke:#4caf50,stroke-width:3px
    style MORE fill:#fff3e0
```

---

## 7️⃣ 이어보기 - 클릭하면? ⭐중요⭐

```mermaid
flowchart TB
    subgraph CONTINUE["Continue Watching (보다가 멈춘 영상)"]
        direction LR

        subgraph RESUME1["이어보기 1"]
            R1_IMG["🖼️ WSOP"]
            R1_BAR["▓▓▓▓▓▓▓▓▓░░░░░░░ 45%"]
            R1_TITLE["WSOP 2019 Bracelet"]
        end

        subgraph RESUME2["이어보기 2"]
            R2_IMG["🖼️ WSOP"]
            R2_BAR["▓▓▓▓▓░░░░░░░░░░░ 25%"]
            R2_TITLE["WSOP 2019 Bracelet"]
        end
    end

    RESUME1 ==>|"💬 클릭하면"| PLAY1["⏩ 45% 지점부터\n이어서 재생!\n\n(처음부터 안 봐도 됨!)"]
    RESUME2 ==>|"💬 클릭하면"| PLAY2["⏩ 25% 지점부터\n이어서 재생!\n\n(처음부터 안 봐도 됨!)"]

    style R1_BAR fill:#9f26b5,color:#fff
    style R2_BAR fill:#9f26b5,color:#fff
    style PLAY1 fill:#e8f5e9,stroke:#4caf50,stroke-width:3px
    style PLAY2 fill:#e8f5e9,stroke:#4caf50,stroke-width:3px
```

**핵심 포인트:**
- **보라색 진행 바** = 여기까지 봤다는 표시
- **클릭하면** → 멈춘 지점부터 이어서 재생!

---

## 8️⃣ 하단 메뉴 - 클릭하면?

```mermaid
flowchart TB
    subgraph FOOTER["하단 메뉴 (Footer)"]
        direction LR

        subgraph SNS_AREA["SNS"]
            FB["📘"]
            X["✖"]
            IG["📷"]
            YT["▶"]
        end

        subgraph ABOUT["ABOUT"]
            A1["About PokerGO"]
            A2["Press Releases"]
        end

        subgraph SUPPORT["SUPPORT"]
            S1["FAQ"]
            S2["Contact"]
        end

        subgraph LEGAL["LEGAL"]
            L1["Privacy Policy"]
            L2["Terms of Use"]
        end
    end

    FB -.->|"💬"| FB_LINK["Facebook 페이지"]
    X -.->|"💬"| X_LINK["X (Twitter)"]
    IG -.->|"💬"| IG_LINK["Instagram"]
    YT -.->|"💬"| YT_LINK["YouTube"]

    A1 -.->|"💬"| ABOUT_PAGE["회사 소개"]
    S1 -.->|"💬"| FAQ_PAGE["자주 묻는 질문"]
    S2 -.->|"💬"| CONTACT_PAGE["문의하기"]
    L1 -.->|"💬"| PRIVACY["개인정보 처리방침"]
    L2 -.->|"💬"| TERMS["이용약관"]
```

---

## 한눈에 보기 - 클릭 정리

```mermaid
flowchart LR
    subgraph SUMMARY["🎯 클릭하면 뭐가 되나요?"]
        direction TB

        A["📺 영상 카드\n(썸네일)"] ==> A1["▶ 바로 재생!"]
        B["▶ Watch Now\n(보라색 버튼)"] ==> B1["▶ 바로 재생!"]
        C["📁 시리즈 포스터"] -.-> C1["📚 전체 회차 목록"]
        D["🔢 에피소드 목록"] ==> D1["▶ 해당 회차 재생"]
        E["▓▓░░ 이어보기 카드"] ==> E1["⏩ 멈춘 지점부터!"]
        F["🔍 검색 아이콘"] -.-> F1["🔍 검색창 열림"]
        G["👤 프로필 아이콘"] -.-> G1["👤 내 계정 메뉴"]
        H["◀ ▶ 화살표"] -.-> H1["👉 더 많은 영상"]
    end

    style A1 fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style B1 fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style D1 fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style E1 fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
```

---

## WSOPTV에서 똑같이 만들 것들

```mermaid
flowchart TB
    subgraph WSOPTV["🎰 WSOPTV 적용 기능"]
        direction LR

        F1["⏩ 이어보기"] --- D1["보다가 멈추면\n다음에 이어서"]
        F2["▓▓░░ 진행률 바"] --- D2["얼마나 봤는지\n한눈에"]
        F3["📁 시리즈 묶음"] --- D3["같은 시리즈는\n한 묶음으로"]
        F4["🔍 검색"] --- D4["원하는 영상\n찾기"]
        F5["🔥 인기 영상"] --- D5["많이 보는 영상\n추천"]
    end

    style F1 fill:#9f26b5,color:#fff
    style F2 fill:#9f26b5,color:#fff
    style F3 fill:#9f26b5,color:#fff
    style F4 fill:#9f26b5,color:#fff
    style F5 fill:#9f26b5,color:#fff
```

---

*문서 끝*
