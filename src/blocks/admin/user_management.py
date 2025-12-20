"""
Admin Block User Management

사용자 관리 기능:
- 사용자 목록 조회
- 사용자 승인
- 사용자 정지
"""



class UserManager:
    """
    사용자 관리자

    사용자 목록 조회, 승인, 정지 등의 기능 제공
    """

    def __init__(self, user_store: dict):
        """
        초기화

        Args:
            user_store: 사용자 저장소 (dict)
        """
        self._users = user_store

    def list_users(self, page: int = 1, size: int = 20) -> dict:
        """
        사용자 목록 조회

        Args:
            page: 페이지 번호 (1부터 시작)
            size: 페이지 크기

        Returns:
            사용자 목록 및 페이징 정보
        """
        users_list = list(self._users.values())
        total = len(users_list)

        # 페이징
        start = (page - 1) * size
        end = start + size
        paginated_users = users_list[start:end]

        return {
            "users": paginated_users,
            "total": total,
            "page": page,
            "size": size,
        }

    def approve_user(self, user_id: str) -> dict:
        """
        사용자 승인

        Args:
            user_id: 승인할 사용자 ID

        Returns:
            승인 결과

        Raises:
            ValueError: 사용자를 찾을 수 없음
        """
        user = self._users.get(user_id)
        if not user:
            raise ValueError("User not found")

        # 상태 업데이트
        user["status"] = "active"

        return {"status": "success", "user_id": user_id, "new_status": "active"}

    def suspend_user(self, user_id: str) -> dict:
        """
        사용자 정지

        Args:
            user_id: 정지할 사용자 ID

        Returns:
            정지 결과

        Raises:
            ValueError: 사용자를 찾을 수 없음
        """
        user = self._users.get(user_id)
        if not user:
            raise ValueError("User not found")

        # 상태 업데이트
        user["status"] = "suspended"

        return {"status": "success", "user_id": user_id, "new_status": "suspended"}

    def get_user(self, user_id: str) -> dict:
        """
        사용자 정보 조회

        Args:
            user_id: 사용자 ID

        Returns:
            사용자 정보

        Raises:
            ValueError: 사용자를 찾을 수 없음
        """
        user = self._users.get(user_id)
        if not user:
            raise ValueError("User not found")

        return user

    def filter_users_by_status(self, status: str) -> list[dict]:
        """
        상태별 사용자 필터링

        Args:
            status: 필터링할 상태 (pending, active, suspended)

        Returns:
            필터링된 사용자 목록
        """
        return [user for user in self._users.values() if user["status"] == status]
