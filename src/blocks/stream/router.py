"""
Stream Block FastAPI Router

HTTP Range Streaming 엔드포인트:
- GET /stream/{content_id}: 스트리밍 URL 획득
- GET /stream/{content_id}/video: 실제 비디오 스트리밍 (Range 지원)
- POST /stream/{content_id}/start: 스트리밍 시작
- POST /stream/{content_id}/end: 스트리밍 종료
"""


from fastapi import APIRouter, Header, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from .models import StreamInfo, StreamResult
from .range_handler import (
    build_range_response,
    parse_range_header,
    stream_file_range,
    validate_range,
)
from .service import StreamService

router = APIRouter(prefix="/stream", tags=["stream"])


@router.get("/{content_id}", response_model=dict)
async def get_stream_url(
    content_id: str, request: Request, authorization: str = Header(None)
) -> dict:
    """
    스트리밍 URL 획득

    Args:
        content_id: 컨텐츠 ID
        authorization: Bearer 토큰

    Returns:
        dict: 스트리밍 정보 {"url": ..., "content_type": ..., "content_length": ...}

    Raises:
        HTTPException 401: 인증 실패
    """
    # Authorization 헤더에서 토큰 추출
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    # StreamService 가져오기 (DI)
    service: StreamService = request.app.state.stream_service

    try:
        stream_info: StreamInfo = await service.get_stream_url(content_id, token)
        return {
            "url": stream_info.url,
            "content_type": stream_info.content_type,
            "content_length": stream_info.content_length,
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/{content_id}/video")
async def stream_video(
    content_id: str, request: Request, range: str = Header(None)
) -> Response:
    """
    비디오 스트리밍 (HTTP Range 지원)

    Args:
        content_id: 컨텐츠 ID
        range: Range 헤더 (예: "bytes=0-1048575")

    Returns:
        StreamingResponse: 206 Partial Content 또는 200 OK

    Raises:
        HTTPException 416: Range 요청 오류
        HTTPException 404: 파일 없음
    """
    service: StreamService = request.app.state.stream_service

    # 스트리밍 소스 조회
    try:
        source = await service.get_stream_source(content_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Content not found")

    file_path = source.path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    total_size = file_path.stat().st_size

    # Range 요청 처리
    if range:
        # Range 헤더 파싱
        range_req = parse_range_header(range, total_size)
        if not range_req:
            raise HTTPException(status_code=416, detail="Invalid Range header")

        start_byte = range_req.start_byte
        end_byte = (
            range_req.end_byte if range_req.end_byte >= 0 else total_size - 1
        )

        # Range 유효성 검증
        valid, error = validate_range(start_byte, end_byte, total_size)
        if not valid:
            raise HTTPException(status_code=416, detail=error)

        # 206 Partial Content 응답
        headers = build_range_response(total_size, start_byte, end_byte)
        headers["Content-Type"] = "video/mp4"

        return StreamingResponse(
            stream_file_range(file_path, start_byte, end_byte),
            status_code=206,
            headers=headers,
            media_type="video/mp4",
        )
    else:
        # 200 OK 응답 (전체 파일)
        return StreamingResponse(
            stream_file_range(file_path, 0, total_size - 1),
            status_code=200,
            headers={
                "Content-Length": str(total_size),
                "Content-Type": "video/mp4",
                "Accept-Ranges": "bytes",
            },
            media_type="video/mp4",
        )


@router.post("/{content_id}/start", response_model=dict)
async def start_stream(content_id: str, request: Request) -> dict:
    """
    스트리밍 시작

    Args:
        content_id: 컨텐츠 ID

    Returns:
        dict: {"allowed": true} 또는 {"allowed": false, "error": "..."}

    Raises:
        HTTPException 429: 동시 스트리밍 제한 초과
    """
    service: StreamService = request.app.state.stream_service

    # TODO: 실제 사용자 ID는 인증 토큰에서 추출
    user_id = "user123"

    result: StreamResult = await service.start_stream(user_id, content_id)

    if not result.allowed:
        raise HTTPException(status_code=429, detail=result.error)

    return {"allowed": result.allowed}


@router.post("/{content_id}/end")
async def end_stream(content_id: str, request: Request) -> dict:
    """
    스트리밍 종료

    Args:
        content_id: 컨텐츠 ID

    Returns:
        dict: {"status": "ended"}
    """
    service: StreamService = request.app.state.stream_service

    # TODO: 실제 사용자 ID는 인증 토큰에서 추출
    user_id = "user123"

    await service.end_stream(user_id, content_id)

    return {"status": "ended"}


@router.get("/{content_id}/bandwidth", response_model=dict)
async def get_bandwidth(content_id: str, request: Request) -> dict:
    """
    사용자 대역폭 조회

    Args:
        content_id: 컨텐츠 ID (미사용, 호환성을 위해 유지)

    Returns:
        dict: {"limit_mbps": ..., "current_mbps": ...}
    """
    service: StreamService = request.app.state.stream_service

    # TODO: 실제 사용자 ID는 인증 토큰에서 추출
    user_id = "user123"

    bandwidth = await service.get_user_bandwidth(user_id)

    return {"limit_mbps": bandwidth.limit_mbps, "current_mbps": bandwidth.current_mbps}
