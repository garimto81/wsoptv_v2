"""
HTTP Range Request Handler

HTTP Range 헤더 파싱 및 응답 생성 유틸리티
"""

import re
from collections.abc import AsyncGenerator
from pathlib import Path

from .models import RangeRequest


def parse_range_header(header: str, total_size: int = 0) -> RangeRequest | None:
    """
    HTTP Range 헤더 파싱

    Args:
        header: Range 헤더 값 (예: "bytes=0-1023")
        total_size: 전체 파일 크기 (선택적)

    Returns:
        RangeRequest or None: 파싱 결과

    Examples:
        >>> parse_range_header("bytes=0-1023")
        RangeRequest(start_byte=0, end_byte=1023)

        >>> parse_range_header("bytes=1024-")
        RangeRequest(start_byte=1024, end_byte=-1)
    """
    if not header:
        return None

    # "bytes=start-end" 형식 파싱
    match = re.match(r"bytes=(\d+)-(\d*)", header)
    if not match:
        return None

    start_byte = int(match.group(1))
    end_str = match.group(2)

    if end_str:
        end_byte = int(end_str)
    else:
        # "bytes=1024-" 형식 (끝까지)
        end_byte = total_size - 1 if total_size > 0 else -1

    try:
        return RangeRequest(start_byte=start_byte, end_byte=end_byte)
    except ValueError:
        return None


def build_range_response(
    total_size: int, start_byte: int, end_byte: int
) -> dict[str, str]:
    """
    HTTP 206 Partial Content 응답 헤더 생성

    Args:
        total_size: 전체 파일 크기
        start_byte: 시작 바이트
        end_byte: 종료 바이트

    Returns:
        dict: 응답 헤더

    Examples:
        >>> build_range_response(1000, 0, 499)
        {
            'Content-Range': 'bytes 0-499/1000',
            'Content-Length': '500',
            'Accept-Ranges': 'bytes'
        }
    """
    content_length = end_byte - start_byte + 1
    content_range = f"bytes {start_byte}-{end_byte}/{total_size}"

    return {
        "Content-Range": content_range,
        "Content-Length": str(content_length),
        "Accept-Ranges": "bytes",
    }


async def stream_file_range(
    file_path: Path, start_byte: int, end_byte: int, chunk_size: int = 1024 * 1024
) -> AsyncGenerator[bytes, None]:
    """
    파일의 특정 범위를 청크 단위로 스트리밍

    Args:
        file_path: 파일 경로
        start_byte: 시작 바이트
        end_byte: 종료 바이트
        chunk_size: 청크 크기 (기본 1MB)

    Yields:
        bytes: 파일 청크

    Examples:
        >>> async for chunk in stream_file_range(Path("video.mp4"), 0, 1048575):
        ...     print(f"Chunk size: {len(chunk)}")
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    total_bytes = end_byte - start_byte + 1
    remaining = total_bytes

    with open(file_path, "rb") as f:
        f.seek(start_byte)

        while remaining > 0:
            # 읽을 크기 결정 (남은 바이트와 청크 크기 중 작은 값)
            read_size = min(chunk_size, remaining)

            # 청크 읽기
            chunk = f.read(read_size)
            if not chunk:
                break

            yield chunk
            remaining -= len(chunk)


def calculate_optimal_chunk_size(
    total_size: int, bandwidth_mbps: float = 100.0
) -> int:
    """
    대역폭에 따른 최적 청크 크기 계산

    Args:
        total_size: 전체 파일 크기 (바이트)
        bandwidth_mbps: 대역폭 (Mbps)

    Returns:
        int: 최적 청크 크기 (바이트)

    Examples:
        >>> calculate_optimal_chunk_size(104857600, 100.0)
        1048576  # 1MB
    """
    # 기본 청크 크기: 1MB
    default_chunk = 1024 * 1024

    # 대역폭이 높으면 더 큰 청크 사용
    if bandwidth_mbps >= 1000:  # 1Gbps
        return default_chunk * 4  # 4MB
    elif bandwidth_mbps >= 100:  # 100Mbps
        return default_chunk * 2  # 2MB
    else:
        return default_chunk  # 1MB


def validate_range(
    start_byte: int, end_byte: int, total_size: int
) -> tuple[bool, str | None]:
    """
    Range Request 유효성 검증

    Args:
        start_byte: 시작 바이트
        end_byte: 종료 바이트
        total_size: 전체 파일 크기

    Returns:
        tuple: (유효 여부, 에러 메시지)

    Examples:
        >>> validate_range(0, 1023, 2048)
        (True, None)

        >>> validate_range(2048, 1023, 2048)
        (False, "Invalid range: start > end")
    """
    if start_byte < 0:
        return False, "Invalid range: start_byte < 0"

    if end_byte < start_byte:
        return False, "Invalid range: start > end"

    if start_byte >= total_size:
        return False, f"Invalid range: start_byte >= total_size ({total_size})"

    return True, None
