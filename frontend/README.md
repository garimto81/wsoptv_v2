# WSOPTV Frontend

Private Poker VOD Streaming Platform - Frontend

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **UI Library**: shadcn/ui + Tailwind CSS
- **Video Player**: ReactPlayer (HLS/DASH)
- **State**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Forms**: React Hook Form + Zod

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/             # 인증 관련 페이지 그룹
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── (main)/             # 메인 레이아웃 그룹
│   │   │   ├── browse/
│   │   │   ├── search/
│   │   │   ├── watch/[id]/
│   │   │   └── history/
│   │   ├── admin/              # 관리자 페이지
│   │   │   ├── dashboard/
│   │   │   ├── users/
│   │   │   └── streams/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   │
│   ├── components/
│   │   ├── ui/                 # shadcn/ui 컴포넌트
│   │   ├── layout/             # 레이아웃 컴포넌트
│   │   │   ├── header.tsx
│   │   │   ├── sidebar.tsx
│   │   │   └── footer.tsx
│   │   ├── content/            # 콘텐츠 관련
│   │   │   ├── content-card.tsx
│   │   │   ├── content-grid.tsx
│   │   │   └── content-row.tsx
│   │   ├── player/             # 비디오 플레이어
│   │   │   ├── video-player.tsx
│   │   │   ├── player-controls.tsx
│   │   │   └── progress-bar.tsx
│   │   ├── search/             # 검색
│   │   │   ├── search-bar.tsx
│   │   │   └── search-results.tsx
│   │   └── admin/              # 관리자
│   │       ├── user-table.tsx
│   │       ├── stats-card.tsx
│   │       └── stream-monitor.tsx
│   │
│   ├── lib/
│   │   ├── api/                # API 클라이언트
│   │   │   ├── client.ts
│   │   │   ├── auth.ts
│   │   │   ├── content.ts
│   │   │   ├── search.ts
│   │   │   ├── stream.ts
│   │   │   └── admin.ts
│   │   ├── hooks/              # 커스텀 훅
│   │   │   ├── use-auth.ts
│   │   │   ├── use-content.ts
│   │   │   └── use-player.ts
│   │   ├── stores/             # Zustand 스토어
│   │   │   ├── auth-store.ts
│   │   │   └── player-store.ts
│   │   └── utils/
│   │       ├── cn.ts
│   │       └── format.ts
│   │
│   └── types/                  # TypeScript 타입
│       ├── api.ts
│       ├── content.ts
│       └── user.ts
│
├── public/
│   └── assets/
│
├── components.json             # shadcn/ui 설정
├── tailwind.config.ts
├── next.config.js
└── package.json
```

## Pages

### Public Pages
- `/` - 랜딩 페이지
- `/login` - 로그인
- `/register` - 회원가입
- `/register/pending` - 승인 대기 안내

### Protected Pages (User)
- `/browse` - 콘텐츠 카탈로그
- `/search` - 검색 결과
- `/watch/[id]` - 비디오 플레이어
- `/history` - 시청 기록

### Admin Pages
- `/admin/dashboard` - 대시보드
- `/admin/users` - 사용자 관리
- `/admin/streams` - 스트림 모니터링

## API Integration

Backend: `http://localhost:8002` (wsoptv-v2-app)

### Endpoints
- `POST /auth/login` - 로그인
- `POST /auth/register` - 회원가입
- `GET /content/` - 카탈로그
- `GET /search?keyword=` - 검색
- `GET /stream/{id}` - 스트리밍 URL
- `POST /stream/{id}/start` - 스트림 시작
- `GET /admin/dashboard` - 대시보드

## Getting Started

```bash
# 의존성 설치
npm install

# 개발 서버
npm run dev

# 빌드
npm run build
```

## Design System

### Colors (Dark Theme)
- Background: `hsl(222.2 84% 4.9%)`
- Foreground: `hsl(210 40% 98%)`
- Primary: `hsl(210 40% 98%)`
- Accent: `hsl(217.2 32.6% 17.5%)`

### Typography
- Font: Inter (Sans-serif)
- Headings: Bold, tracking-tight
- Body: Regular

### Components (shadcn/ui)
- Button, Input, Card
- Dialog, Sheet, Dropdown
- Table, Badge, Avatar
- Skeleton, Progress
