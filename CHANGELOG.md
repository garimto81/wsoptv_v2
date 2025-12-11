# Changelog

All notable changes to the WSOPTV project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2025-12-11

### Added

#### Backend API (wsoptv_v2_db)
- **Watch Progress API** (`progress.py`)
  - `POST /api/v1/progress` - Save watch progress
  - `GET /api/v1/progress/{content_id}` - Get progress for specific content
  - `GET /api/v1/progress` - Get all user progress
  - `DELETE /api/v1/progress/{content_id}` - Delete progress
  - `POST /api/v1/progress/{content_id}/complete` - Mark as completed

- **Continue Watching API** (`contents.py`)
  - `GET /api/v1/contents/continue` - Get continue watching list

#### Frontend (wsoptv_v2/frontend)
- **Netflix-style Video Player** enhancements
  - Custom controls with 10-second skip forward/backward
  - Playback speed selector (0.5x - 2x)
  - Volume slider with hover expand
  - Buffering indicator
  - Skip indicator animation
  - Keyboard shortcuts (Space, J, K, L, F, M)
  - Resume from last position
  - Auto-save progress (2s debounce)

### Changed
- Updated `watch/[id]/page.tsx` to use new VideoPlayer component
- Integrated Progress API for automatic watch tracking
- Improved video player UI to match Netflix design

### Technical Details
- Progress API uses in-memory storage (to be replaced with database)
- Progress auto-saves every 5 seconds of playback change
- Content marked as completed at 95% progress

---

## [1.4.0] - 2025-12-11

### Added

#### Backend API
- **Auth API** (`auth.py`)
  - User registration with pending approval
  - Token-based authentication
  - Admin user management
  - User status management (pending/active/rejected/suspended)

- **Contents API** (`contents.py`)
  - `GET /api/v1/contents/browse` - Netflix-style browse page
  - `GET /api/v1/contents/featured` - Hero billboard content
  - `GET /api/v1/contents/top10` - Trending content
  - `GET /api/v1/contents/category/{category}` - Content by category
  - `GET /api/v1/contents/{id}` - Single content

#### Frontend
- Netflix-style UI components
  - Header with transparent gradient
  - Hero Billboard (40% viewport)
  - Content Row with horizontal scroll
  - Content Card with hover effects (130% scale)
  - Search page with category filters
  - Browse page

---

## [1.3.0] - 2025-12-10

### Added
- Initial Netflix-style UI implementation
- Basic video player component
- Authentication pages (login, register, pending approval)
- Admin dashboard for user management

---

## [1.0.0] - 2025-12-09

### Added
- Initial project setup
- Next.js 15 frontend with TypeScript
- FastAPI backend structure
- Tailwind CSS configuration
- CORS middleware setup
