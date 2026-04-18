from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TestlistResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    type: str
    exam_type: str | None
    duration_minutes: int
    total_questions: int
    year: int | None
    created_at: datetime


class TestDetailResponse(TestlistResponse):
    pass


class QuestionResponse(BaseModel):
    id: UUID
    test_id: UUID
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    subject: str | None
    difficulty: str | None
    order_number: int


class TestStartResponse(BaseModel):
    attempt_id: UUID
    timer_deadline_ms: int
    test: TestDetailResponse
    questions: list[QuestionResponse]


class TestAttemptUpdate(BaseModel):
    answers: dict[str, str]  # { "question_id": "a/b/c/d" }


class TestSubmitRequest(BaseModel):
    answers: dict[str, str]
    time_taken_seconds: int


class TestResultResponse(BaseModel):
    attempt_id: UUID
    score: int
    total_questions: int
    accuracy: float
    correct: int
    wrong: int
    time_taken_seconds: int


class QuestionResultDetail(BaseModel):
    question: QuestionResponse
    user_answer: str | None
    correct_answer: str
    is_correct: bool
    explanation: str | None


class DetailedResultsResponse(BaseModel):
    attempt: dict
    results: list[QuestionResultDetail]


class UserStatsResponse(BaseModel):
    user_id: UUID
    total_attempts: int = 0
    total_questions_attempted: int = 0
    total_correct: int = 0
    total_wrong: int = 0
    overall_accuracy: float = 0.0
    best_score: int = 0
    best_test_id: UUID | None
    last_attempt_at: datetime | None


class QuestionReportRequest(BaseModel):
    reason: str  # 'Problem with question', 'Problem with options or answer', 'Wrong or incorrect explanation'


class AttemptHistoryResponse(BaseModel):
    id: UUID
    test_id: UUID
    test_title: str
    exam_type: str | None
    submitted_at: datetime | None
    score: int
    total_questions: int
    accuracy: float
