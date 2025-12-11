"""
Worker Block Models

Task, TaskType, TaskStatus, TaskResult 정의
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict


class TaskType(str, Enum):
    """작업 타입"""
    THUMBNAIL = "THUMBNAIL"
    CACHE_WARM = "CACHE_WARM"
    NAS_SCAN = "NAS_SCAN"


class TaskStatus(str, Enum):
    """작업 상태"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class Task:
    """작업 모델"""
    id: str
    type: TaskType
    payload: Dict[str, Any]
    priority: int = 0
    status: TaskStatus = TaskStatus.PENDING
    retries: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaskResult:
    """작업 결과"""
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
