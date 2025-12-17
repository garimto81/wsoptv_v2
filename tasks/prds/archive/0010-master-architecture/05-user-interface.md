# 05. User Interface

*← [04-data-models.md](./04-data-models.md) | [06-security.md](./06-security.md) →*

---

## 1. Page Structure

### 1.1 Route Map

```mermaid
flowchart TB
    subgraph Public["Public Routes"]
        Root["/"] --> Redirect["Redirect Logic"]
        Login["/login"]
        Register["/register"]
        Pending["/register/pending"]
    end

    subgraph Protected["Protected Routes (User)"]
        Browse["/browse"]
        Search["/search"]
        Watch["/watch/[id]"]
        History["/history"]
    end

    subgraph Admin["Admin Routes"]
        Dashboard["/admin/dashboard"]
        Users["/admin/users"]
        Streams["/admin/streams"]
    end

    Redirect -->|"Not logged in"| Login
    Redirect -->|"Logged in"| Browse

    Login -->|"Success"| Browse
    Register -->|"Success"| Pending

    Browse --> Watch
    Browse --> Search
    Search --> Watch
```

### 1.2 Page Authentication Matrix

| Route | Auth Required | Role | Redirect |
|-------|--------------|------|----------|
| `/` | - | - | → `/login` or `/browse` |
| `/login` | No | - | → `/browse` if logged in |
| `/register` | No | - | → `/browse` if logged in |
| `/register/pending` | No | - | - |
| `/browse` | Yes | User+ | → `/login` |
| `/search` | Yes | User+ | → `/login` |
| `/watch/[id]` | Yes | User+ | → `/login` |
| `/history` | Yes | User+ | → `/login` |
| `/admin/*` | Yes | Admin | → `/browse` if not admin |

---

## 2. Layout Architecture

### 2.1 Main Layout

```mermaid
flowchart TB
    subgraph MainLayout["Main Layout"]
        direction TB
        Header["Header (64px)<br/>━━━━━━━━━━━━━━━━━━━━━━━━━━<br/>Logo | Search | User Menu"]
        Main["Main Content (flex-1)<br/>━━━━━━━━━━━━━━━━━━━━━━━━━━<br/>Page Content"]
        Footer["Footer (optional, 48px)<br/>━━━━━━━━━━━━━━━━━━━━━━━━━━<br/>Links | Copyright"]
    end

    Header --> Main --> Footer
```

### 2.2 Admin Layout

```mermaid
flowchart TB
    subgraph AdminLayout["Admin Layout"]
        direction TB
        Header["Header (64px)<br/>━━━━━━━━━━━━━━━━━━━━━━━━━━<br/>WSOPTV Admin | User Menu"]

        subgraph Body["Body"]
            direction LR
            Sidebar["Sidebar (240px)<br/>━━━━━━━━━━━━━━━━━━━━<br/>Dashboard<br/>Users<br/>Streams<br/>Settings"]
            Content["Main Content (flex-1)<br/>━━━━━━━━━━━━━━━━━━━━<br/>Page Content"]
        end
    end

    Header --> Body
```

---

## 3. Component Architecture

### 3.1 Component Hierarchy

```mermaid
flowchart TB
    subgraph Layout["Layout Components"]
        Header["Header"]
        Sidebar["Sidebar"]
        Footer["Footer"]
    end

    subgraph Content["Content Components"]
        ContentCard["ContentCard"]
        ContentGrid["ContentGrid"]
        ContentRow["ContentRow"]
        HeroBanner["HeroBanner"]
    end

    subgraph Player["Player Components"]
        VideoPlayer["VideoPlayer"]
        PlayerControls["PlayerControls"]
        ProgressSaver["ProgressSaver"]
    end

    subgraph UI["UI Components (shadcn)"]
        Button["Button"]
        Input["Input"]
        Dialog["Dialog"]
        Table["Table"]
        Toast["Toast"]
    end

    ContentGrid --> ContentCard
    ContentRow --> ContentCard
    VideoPlayer --> PlayerControls
    VideoPlayer --> ProgressSaver
```

### 3.2 Directory Structure

```
frontend/src/
├── app/                          # Next.js App Router
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── register/pending/page.tsx
│   ├── (main)/
│   │   ├── browse/page.tsx
│   │   ├── search/page.tsx
│   │   ├── watch/[id]/page.tsx
│   │   └── history/page.tsx
│   ├── admin/
│   │   ├── dashboard/page.tsx
│   │   ├── users/page.tsx
│   │   └── streams/page.tsx
│   ├── layout.tsx
│   └── globals.css
├── components/
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   ├── Footer.tsx
│   │   ├── MainLayout.tsx
│   │   └── AdminLayout.tsx
│   ├── content/
│   │   ├── ContentCard.tsx
│   │   ├── ContentGrid.tsx
│   │   ├── ContentRow.tsx
│   │   ├── HeroBanner.tsx
│   │   └── ContentDetail.tsx
│   ├── player/
│   │   ├── VideoPlayer.tsx
│   │   ├── PlayerControls.tsx
│   │   └── ProgressSaver.tsx
│   └── ui/                       # shadcn/ui
│       ├── button.tsx
│       ├── input.tsx
│       ├── dialog.tsx
│       └── table.tsx
├── lib/
│   ├── api/
│   │   ├── auth.ts
│   │   ├── catalog.ts
│   │   ├── stream.ts
│   │   └── admin.ts
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useCatalog.ts
│   │   ├── usePlayer.ts
│   │   └── useProgress.ts
│   └── stores/
│       ├── authStore.ts
│       └── playerStore.ts
└── types/
    ├── api.ts
    ├── catalog.ts
    └── user.ts
```

---

## 4. Page Designs

### 4.1 Browse Page

```mermaid
flowchart TB
    subgraph BrowsePage["Browse Page (/browse)"]
        direction TB

        subgraph Header["Header"]
            direction LR
            Logo["WSOPTV"]
            SearchBar["Search..."]
            UserMenu["👤 User ▼"]
        end

        subgraph Hero["Hero Section (400px)"]
            Featured["━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br/><br/>🎬 WSOP 2024 Main Event - Final Table<br/><br/>Epic heads-up battle between...<br/><br/>[▶ Play]  [+ My List]  [ℹ️ More Info]<br/><br/>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        end

        subgraph Continue["Continue Watching"]
            direction LR
            C1["Card<br/>▓▓▓░ 75%"]
            C2["Card<br/>▓▓░░ 45%"]
            C3["Card<br/>▓░░░ 20%"]
        end

        subgraph WSOP["WSOP Series (156)"]
            direction LR
            W1["Event #1"]
            W2["Event #2"]
            W3["Main Event"]
            WMore["→"]
        end

        subgraph HCL["Hustler Casino Live (89)"]
            direction LR
            H1["S12E10"]
            H2["S12E09"]
            H3["S12E08"]
            HMore["→"]
        end
    end

    Header --> Hero --> Continue --> WSOP --> HCL
```

### 4.2 Content Card Component

```
┌─────────────────────────────┐
│ [MP4]                [2.1GB]│  ← File info badges
│                             │
│         [Thumbnail]         │  ← 16:9 ratio
│            ▶                │  ← Play overlay on hover
│                             │
│ ▓▓▓▓▓▓▓▓▓▓░░░░░░ 65%       │  ← Progress bar (if watching)
├─────────────────────────────┤
│ WSOP 2024 Event #5          │  ← display_title (truncated)
│ Day 1                       │
│                             │
│ [NLHE] [Main Event]         │  ← category_tags
│ ⭐ 95%  •  2h 45m           │  ← confidence, duration
└─────────────────────────────┘
```

### 4.3 Watch Page

```mermaid
flowchart TB
    subgraph WatchPage["Watch Page (/watch/[id])"]
        direction TB

        subgraph VideoArea["Video Area"]
            BackBtn["← Back"]
            Player["━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br/><br/><br/><br/>         VIDEO PLAYER<br/><br/><br/><br/>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
            Controls["⏮  ▶  ⏭   ━━━━━━━━━━●━━━━   🔊  ⛶"]
        end

        subgraph Info["Content Info"]
            Title["WSOP 2024 Event #5 - Day 1"]
            Tags["[WSOP] [2024] [NLHE] [Main Event]"]
            Meta["2h 45m  •  2.1 GB  •  1080p"]
        end

        subgraph Related["Related Content"]
            direction LR
            R1["Next Episode"]
            R2["Same Series"]
            R3["Recommended"]
        end
    end

    VideoArea --> Info --> Related
```

### 4.4 Admin Dashboard

```mermaid
flowchart TB
    subgraph Dashboard["Admin Dashboard"]
        direction TB

        subgraph Stats["Statistics Cards"]
            direction LR
            S1["👥 Users<br/>━━━━━━━━<br/>125 total<br/>15 pending"]
            S2["📺 Streams<br/>━━━━━━━━<br/>8/20 active"]
            S3["🎬 Content<br/>━━━━━━━━<br/>325 items"]
            S4["👁️ Today<br/>━━━━━━━━<br/>47 views"]
        end

        subgraph Pending["Pending Users"]
            PTable["Email              | Date    | Actions<br/>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br/>user1@ex.com    | Dec 17 | [✓] [✗]<br/>user2@ex.com    | Dec 16 | [✓] [✗]"]
        end

        subgraph Active["Active Streams"]
            ATable["User      | Content     | Time  | Action<br/>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br/>user1    | WSOP 2024  | 15m  | [Stop]<br/>user2    | HCL S12E5  | 5m   | [Stop]"]
        end
    end

    Stats --> Pending --> Active
```

---

## 5. State Management

### 5.1 Store Architecture

```mermaid
flowchart LR
    subgraph Zustand["Zustand (Client State)"]
        AuthStore["authStore<br/>━━━━━━━━━━━━━━<br/>user<br/>token<br/>isAuthenticated"]
        PlayerStore["playerStore<br/>━━━━━━━━━━━━━━<br/>currentItem<br/>isPlaying<br/>volume"]
    end

    subgraph TanStack["TanStack Query (Server State)"]
        CatalogQuery["useCatalog<br/>━━━━━━━━━━━━━━<br/>카탈로그 목록<br/>캐싱, 리페치"]
        SearchQuery["useSearch<br/>━━━━━━━━━━━━━━<br/>검색 결과<br/>디바운싱"]
        ProgressQuery["useProgress<br/>━━━━━━━━━━━━━━<br/>시청 진행률<br/>낙관적 업데이트"]
    end
```

### 5.2 Auth Store

```typescript
interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;

  // Actions
  login: (token: string, user: User) => void;
  logout: () => void;
  setUser: (user: User) => void;
}
```

### 5.3 Player Store

```typescript
interface PlayerStore {
  currentItem: CatalogItem | null;
  isPlaying: boolean;
  volume: number;
  currentTime: number;
  duration: number;

  // Actions
  setItem: (item: CatalogItem) => void;
  play: () => void;
  pause: () => void;
  setVolume: (v: number) => void;
  setCurrentTime: (t: number) => void;
}
```

---

## 6. Video Player States

```mermaid
stateDiagram-v2
    [*] --> Loading: 페이지 진입

    Loading --> Ready: 메타데이터 로드
    Loading --> Error: 로드 실패

    Ready --> Playing: play()
    Playing --> Paused: pause()
    Paused --> Playing: play()

    Playing --> Buffering: 버퍼 부족
    Buffering --> Playing: 버퍼 충분

    Playing --> Ended: 재생 완료
    Ended --> Playing: replay()

    Error --> [*]

    note right of Playing
        매 10초마다
        POST /api/v1/progress
    end note

    note right of Buffering
        스피너 표시
        자동 재개
    end note
```

---

## 7. Responsive Design

### 7.1 Breakpoints

| Name | Width | Grid Columns | Usage |
|------|-------|--------------|-------|
| `sm` | < 640px | 1-2 | Mobile |
| `md` | 640px - 1024px | 3-4 | Tablet |
| `lg` | 1024px - 1920px | 5-6 | Desktop |
| `xl` | > 1920px | 6-8 | Large Desktop |

### 7.2 Content Card Grid

```css
/* Responsive grid */
.content-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(2, 1fr);   /* Mobile */
}

@media (min-width: 640px) {
  .content-grid {
    grid-template-columns: repeat(3, 1fr); /* Tablet */
  }
}

@media (min-width: 1024px) {
  .content-grid {
    grid-template-columns: repeat(5, 1fr); /* Desktop */
  }
}

@media (min-width: 1920px) {
  .content-grid {
    grid-template-columns: repeat(6, 1fr); /* Large */
  }
}
```

---

## 8. TypeScript Interfaces

### 8.1 CatalogItem

```typescript
interface CatalogItem {
  id: string;
  nas_file_id: string | null;
  display_title: string;
  short_title: string;
  thumbnail_url: string | null;
  project_code: string;
  year: number | null;
  category_tags: string[];
  file_path: string;
  file_name: string;
  file_size_bytes: number;
  file_size_formatted: string;
  file_extension: string;
  duration_seconds: number | null;
  quality: string | null;
  is_visible: boolean;
  confidence: number;
  created_at: string;
  updated_at: string;
}
```

### 8.2 User

```typescript
interface User {
  id: string;
  email: string;
  status: 'pending' | 'active' | 'suspended';
  is_admin: boolean;
  created_at: string;
  last_login: string | null;
}
```

### 8.3 WatchProgress

```typescript
interface WatchProgress {
  content_id: string;
  position_seconds: number;
  total_seconds: number;
  percentage: number;
  last_watched: string;
}
```

---

*← [04-data-models.md](./04-data-models.md) | [06-security.md](./06-security.md) →*
