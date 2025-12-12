-- WSOPTV 초기 데이터베이스 스키마
-- PostgreSQL 16

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin', 'moderator')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'suspended')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 콘텐츠 테이블
CREATE TABLE IF NOT EXISTS contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    file_path VARCHAR(1000) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    duration_seconds INTEGER,
    codec VARCHAR(50),
    resolution VARCHAR(20),
    thumbnail_path VARCHAR(1000),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 시청 진행률 테이블
CREATE TABLE IF NOT EXISTS watch_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content_id UUID NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    position_seconds INTEGER NOT NULL DEFAULT 0,
    total_seconds INTEGER NOT NULL,
    percentage DECIMAL(5, 2) GENERATED ALWAYS AS (
        CASE WHEN total_seconds > 0
        THEN ROUND((position_seconds::DECIMAL / total_seconds) * 100, 2)
        ELSE 0 END
    ) STORED,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, content_id)
);

-- 스트리밍 세션 테이블
CREATE TABLE IF NOT EXISTS streaming_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content_id UUID NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    bytes_transferred BIGINT DEFAULT 0
);

-- 캐시 메타데이터 테이블
CREATE TABLE IF NOT EXISTS cache_metadata (
    content_id UUID PRIMARY KEY REFERENCES contents(id) ON DELETE CASCADE,
    cache_tier VARCHAR(10) NOT NULL CHECK (cache_tier IN ('L1', 'L2', 'L3', 'L4')),
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_contents_title ON contents USING gin(to_tsvector('simple', title));
CREATE INDEX IF NOT EXISTS idx_watch_progress_user ON watch_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_streaming_sessions_user ON streaming_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_streaming_sessions_active ON streaming_sessions(user_id) WHERE ended_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_cache_metadata_tier ON cache_metadata(cache_tier);
CREATE INDEX IF NOT EXISTS idx_cache_metadata_access ON cache_metadata(access_count DESC);

-- 기본 관리자 계정 (비밀번호: admin)
INSERT INTO users (email, password_hash, role, status)
VALUES ('admin@wsoptv.local', '$2b$12$ZbCPRu9T4.i71bvNCbL06.MTq0pcKqkYC9D1NdSSGmmxRTNiK82gS', 'admin', 'active')
ON CONFLICT (email) DO NOTHING;

-- 테스트 사용자 (비밀번호: password)
INSERT INTO users (email, password_hash, role, status)
VALUES ('test@wsoptv.local', '$2b$12$9iRRxQ153xLeun/lDWVyjeVumzQn/HspAkTA9SSYf5KZ7XLYL.kuu', 'user', 'active')
ON CONFLICT (email) DO NOTHING;
