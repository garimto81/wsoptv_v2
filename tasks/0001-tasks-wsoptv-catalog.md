# Task List: WSOPTV Netflix-style Catalog (PRD v1.5.0)

**Created**: 2025-12-11
**PRD**: docs/prd.md v1.5.0
**Status**: In Progress (74% Complete)

---

## Phase 0: Setup & Foundation

### Task 0.0: Project Setup
- [x] 0.0.1: Create Next.js 15 frontend project
- [x] 0.0.2: Create FastAPI backend project
- [x] 0.0.3: Configure Tailwind CSS
- [x] 0.0.4: Setup CORS middleware

### Task 0.1: Authentication System
- [x] 0.1.1: Login page UI
- [x] 0.1.2: Register page UI
- [x] 0.1.3: Pending approval page
- [x] 0.1.4: Admin dashboard - user management
- [x] 0.1.5: User status management (pending/active/rejected/suspended)
- [x] 0.1.6: Backend API integration (/api/auth/*)
  **Completed**: 2025-12-11 - auth.py created
- [x] 0.1.7: JWT token management
  **Completed**: 2025-12-11 - token-based auth in auth.py
- [ ] 0.1.8: Session persistence (Frontend integration pending)

---

## Phase 1: Netflix-style UI Implementation

### Task 1.0: Layout Components
- [x] 1.0.1: Header component (투명 그라디언트)
  - Logo (WSOPTV)
  - Category navigation (All, WSOP, HCL, GGMillions, GOG, MPP, PAD)
  - Search icon
  - Admin link
  - User avatar dropdown
  Priority: High
  Estimate: 4h
  **Completed**: 2025-12-11

- [x] 1.0.2: Main layout with dark theme (#141414 background)
  Priority: High
  Estimate: 2h
  **Completed**: 2025-12-11

### Task 1.1: Hero Billboard Component
- [x] 1.1.1: Full-width hero banner (40% viewport height)
  Priority: High
  Estimate: 4h
  **Completed**: 2025-12-11

- [x] 1.1.2: Left gradient overlay (black → transparent)
  Priority: Medium
  Estimate: 1h
  **Completed**: 2025-12-11

- [x] 1.1.3: Content info overlay (title, description)
  Priority: High
  Estimate: 2h
  **Completed**: 2025-12-11

- [x] 1.1.4: Action buttons (Play, More Info)
  Priority: High
  Estimate: 1h
  **Completed**: 2025-12-11

- [ ] 1.1.5: Auto-rotation with fade transition (optional)
  Priority: Low
  Estimate: 2h

### Task 1.2: Content Row Component
- [x] 1.2.1: Row container with title and navigation arrows
  Priority: High
  Estimate: 2h
  **Completed**: 2025-12-11

- [x] 1.2.2: Horizontal scroll with snap
  Priority: High
  Estimate: 2h
  **Completed**: 2025-12-11

- [x] 1.2.3: Row types:
  - "이어서 시청하기" (Continue Watching) with progress bar
  - "오늘 TOP 10" with large ranking numbers
  - Category rows (WSOP, HCL, etc.)
  Priority: High
  Estimate: 4h
  **Completed**: 2025-12-11

### Task 1.3: Content Card Component
- [x] 1.3.1: Basic card with thumbnail
- [x] 1.3.2: Hover expand effect (150% scale)
  Priority: High
  Estimate: 3h
  **Completed**: 2025-12-11

- [x] 1.3.3: Hover preview info (title, metadata, buttons)
  Priority: Medium
  Estimate: 2h
  **Completed**: 2025-12-11

- [x] 1.3.4: Progress indicator for watched content
  Priority: Medium
  Estimate: 1h
  **Completed**: 2025-12-11

### Task 1.4: Search Component
- [x] 1.4.1: Expandable search input
  Priority: Medium
  Estimate: 2h
  **Completed**: 2025-12-11

- [x] 1.4.2: Search results page
  Priority: Medium
  Estimate: 3h
  **Completed**: 2025-12-11

- [x] 1.4.3: Category filter
  Priority: Low
  Estimate: 2h
  **Completed**: 2025-12-11

---

## Phase 2: Backend API Integration

### Task 2.0: Catalog API (Netflix-style)
- [x] 2.0.1: GET /api/v1/contents/browse (browse page)
  **Completed**: 2025-12-11 - contents.py
- [x] 2.0.2: GET /api/v1/contents/:id (single content)
  **Completed**: 2025-12-11
- [x] 2.0.3: GET /api/v1/contents/featured (hero billboard)
  **Completed**: 2025-12-11
- [x] 2.0.4: GET /api/v1/contents/top10 (trending)
  **Completed**: 2025-12-11
- [x] 2.0.5: GET /api/v1/contents/continue (continue watching)
  **Completed**: 2025-12-11 - Integrated with Progress API
- [x] 2.0.6: GET /api/v1/contents/category/:category (by category)
  **Completed**: 2025-12-11
  Priority: High
  Estimate: 8h

### Task 2.1: User API
- [x] 2.1.1: POST /api/v1/auth/register
  **Completed**: 2025-12-11 - auth.py
- [x] 2.1.2: POST /api/v1/auth/login
  **Completed**: 2025-12-11
- [x] 2.1.3: GET /api/v1/auth/me
  **Completed**: 2025-12-11
- [x] 2.1.4: GET /api/v1/auth/users (admin only)
  **Completed**: 2025-12-11
- [x] 2.1.5: PATCH /api/v1/auth/users/:id/status (admin only)
  **Completed**: 2025-12-11
  Priority: High
  Estimate: 6h

### Task 2.2: Watch Progress API
- [x] 2.2.1: POST /api/v1/progress (save progress)
  **Completed**: 2025-12-11 - progress.py created
- [x] 2.2.2: GET /api/v1/progress/:contentId (get progress)
  **Completed**: 2025-12-11
- [x] 2.2.3: GET /api/v1/progress (get all user progress)
  **Completed**: 2025-12-11
- [x] 2.2.4: DELETE /api/v1/progress/:contentId (delete progress)
  **Completed**: 2025-12-11
- [x] 2.2.5: POST /api/v1/progress/:contentId/complete (mark as completed)
  **Completed**: 2025-12-11
  Priority: Medium
  Estimate: 3h

---

## Phase 3: Video Streaming

### Task 3.0: Video Player
- [x] 3.0.1: Basic video player component
  **Completed**: 2025-12-11
- [x] 3.0.2: Custom controls (Netflix-style)
  **Completed**: 2025-12-11 - 10초 앞/뒤로, 재생속도, 볼륨 슬라이더
- [x] 3.0.3: Progress tracking
  **Completed**: 2025-12-11 - Progress API 연동
- [x] 3.0.4: Resume from last position
  **Completed**: 2025-12-11 - initialProgress prop
- [ ] 3.0.5: Quality selector (if multiple sources)
  Priority: Medium
  Estimate: 8h

### Task 3.1: Streaming Backend
- [ ] 3.1.1: Range request support
- [ ] 3.1.2: NAS file access
- [ ] 3.1.3: Rate limiting
  Priority: High
  Estimate: 6h

---

## Phase 4: Cache System

### Task 4.0: 4-Tier Cache Implementation
- [ ] 4.0.1: L1 Redis metadata cache
- [ ] 4.0.2: L2 SSD hot content cache
- [ ] 4.0.3: L3 Rate limiter
- [ ] 4.0.4: L4 NAS direct access
  Priority: Medium
  Estimate: 16h

---

## Phase 5: Testing & Polish

### Task 5.0: Testing
- [ ] 5.0.1: Unit tests for components
- [ ] 5.0.2: API integration tests
- [ ] 5.0.3: E2E tests (Playwright)
  Priority: Medium
  Estimate: 12h

### Task 5.1: Performance
- [ ] 5.1.1: Image optimization
- [ ] 5.1.2: Lazy loading
- [ ] 5.1.3: Bundle optimization
  Priority: Low
  Estimate: 4h

---

## Summary

| Phase | Total Tasks | Completed | Progress |
|-------|-------------|-----------|----------|
| Phase 0 | 12 | 11 | **92%** |
| Phase 1 | 15 | 14 | **93%** |
| Phase 2 | 16 | 16 | **100%** |
| Phase 3 | 8 | 4 | **50%** |
| Phase 4 | 4 | 0 | 0% |
| Phase 5 | 6 | 0 | 0% |
| **Total** | **61** | **45** | **74%** |

**Last Updated**: 2025-12-11

---

## Priority Order (Recommended)

1. **High Priority** - Netflix UI Core
   - 1.0.1: Header component
   - 1.0.2: Main layout
   - 1.1.1-1.1.4: Hero Billboard
   - 1.2.1-1.2.3: Content Rows
   - 1.3.2-1.3.3: Card hover effects

2. **Medium Priority** - Backend Integration
   - 2.0.1-2.0.6: Catalog API
   - 2.1.1-2.1.5: User API
   - 0.1.6-0.1.8: Auth integration

3. **Lower Priority** - Enhancement
   - Search, Video player, Cache system, Testing
