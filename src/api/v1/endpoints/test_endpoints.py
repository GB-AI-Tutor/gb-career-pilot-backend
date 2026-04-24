import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.api.v1.deps import get_current_user
from src.database.database import get_supabase_admin_client
from src.schemas.test_schema import (
    AttemptHistoryResponse,
    DetailedResultsResponse,
    QuestionReportRequest,
    TestAttemptUpdate,
    TestDetailResponse,
    TestlistResponse,
    TestResultResponse,
    TestStartResponse,
    TestSubmitRequest,
    UserStatsResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# GET /tests - List available tests
# ═══════════════════════════════════════════════════════════════


@router.get("/tests", response_model=list[TestlistResponse])
async def list_tests(
    exam_type: str | None = None,
    type: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    """List all available tests (filterable by exam_type or type)"""
    db = await get_supabase_admin_client()
    query = db.table("tests").select("*").eq("is_published", True)

    if exam_type:
        query = query.eq("exam_type", exam_type)
    if type:
        query = query.eq("type", type)

    result = await query.order("created_at", desc=True).execute()
    return result.data


# ═══════════════════════════════════════════════════════════════
# GET /tests/{test_id} - Get test details
# ═══════════════════════════════════════════════════════════════
@router.get("/tests/{test_id}", response_model=TestDetailResponse)
async def get_test(test_id: UUID, current_user: dict = Depends(get_current_user)):
    """Get test metadata(without questions)"""
    db = await get_supabase_admin_client()
    result = await db.table("tests").select("*").eq("id", str(test_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Test not found")

    return result.data


# ═══════════════════════════════════════════════════════════════
# POST /tests/{test_id}/start - Start a new test attempt
# ═══════════════════════════════════════════════════════════════
@router.post("/tests/{test_id}/start", response_model=TestStartResponse)
async def start_test(test_id: UUID, current_user: dict = Depends(get_current_user)):
    """Start a new test attempt and return attempt_id + questions"""
    db = await get_supabase_admin_client()
    user_id = current_user["id"]

    # Get test details
    test = await db.table("tests").select("*").eq("id", str(test_id)).single().execute()

    if not test.data:
        raise HTTPException(status_code=404, detail="Test not found")

    # Calculate timer deadline (duration in minutes → milliseconds)
    duration_ms = test.data["duration_minutes"] * 60 * 1000
    timer_deadline_ms = int(datetime.now().timestamp() * 1000) + duration_ms

    # Create attempt
    attempt = (
        await db.table("test_attempts")
        .insert(
            {
                "user_id": user_id,
                "test_id": str(test_id),
                "timer_deadline_ms": timer_deadline_ms,
                "total_questions": test.data["total_questions"],
            }
        )
        .execute()
    )

    # Get questions
    questions = (
        await db.table("questions")
        .select("*")
        .eq("test_id", str(test_id))
        .order("order_number")
        .execute()
    )

    return {
        "attempt_id": attempt.data[0]["id"],
        "timer_deadline_ms": timer_deadline_ms,
        "test": test.data,
        "questions": questions.data,
    }


# ═══════════════════════════════════════════════════════════════
# PATCH /tests/attempts/{attempt_id} - Save progress (autosave)
# ═══════════════════════════════════════════════════════════════
@router.patch("/tests/attempts/{attempt_id}")
async def update_attempt(
    attempt_id: UUID, update: TestAttemptUpdate, current_user: dict = Depends(get_current_user)
):
    """Update answers (autosave during test)"""
    db = await get_supabase_admin_client()
    user_id = current_user["id"]

    # Verify ownership
    attempt = (
        await db.table("test_attempts")
        .select("user_id")
        .eq("id", str(attempt_id))
        .single()
        .execute()
    )

    if not attempt.data or attempt.data["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Update answers
    await (
        db.table("test_attempts")
        .update({"answers": update.answers})
        .eq("id", str(attempt_id))
        .execute()
    )

    return {"message": "Progress saved"}


# ═══════════════════════════════════════════════════════════════
# POST /tests/attempts/{attempt_id}/submit - Submit test
# ═══════════════════════════════════════════════════════════════
@router.post("/tests/attempts/{attempt_id}/submit", response_model=TestResultResponse)
async def submit_test(
    attempt_id: UUID, submit_data: TestSubmitRequest, current_user: dict = Depends(get_current_user)
):
    """Submit test and calculate score"""
    db = await get_supabase_admin_client()
    user_id = current_user["id"]

    # Get attempt
    attempt = (
        await db.table("test_attempts")
        .select("*, tests(*)")
        .eq("id", str(attempt_id))
        .single()
        .execute()
    )

    if not attempt.data:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.data["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if attempt.data["is_completed"]:
        raise HTTPException(status_code=400, detail="Test already submitted")

    # Get correct answers
    questions = (
        await db.table("questions")
        .select("id, correct_option")
        .eq("test_id", attempt.data["test_id"])
        .execute()
    )

    # Calculate score
    correct_count = 0
    wrong_count = 0
    answers = submit_data.answers

    for q in questions.data:
        qid = q["id"]
        if qid in answers:
            if answers[qid] == q["correct_option"]:
                correct_count += 1
            else:
                wrong_count += 1

    total = len(questions.data)
    accuracy = round((correct_count / total * 100), 2) if total > 0 else 0
    time_taken = submit_data.time_taken_seconds

    # Update attempt
    await (
        db.table("test_attempts")
        .update(
            {
                "answers": answers,
                "submitted_at": datetime.now().isoformat(),
                "is_completed": True,
                "score": correct_count,
                "time_taken_seconds": time_taken,
                "accuracy": accuracy,
            }
        )
        .eq("id", str(attempt_id))
        .execute()
    )

    # Update user stats
    await update_user_stats(
        db, user_id, correct_count, wrong_count, total, correct_count, str(attempt.data["test_id"])
    )

    return {
        "attempt_id": attempt_id,
        "score": correct_count,
        "total_questions": total,
        "accuracy": accuracy,
        "correct": correct_count,
        "wrong": wrong_count,
        "time_taken_seconds": time_taken,
    }


# ═══════════════════════════════════════════════════════════════
# GET /tests/attempts/{attempt_id}/results - View detailed results
# ═══════════════════════════════════════════════════════════════
@router.get("/tests/attempts/{attempt_id}/results", response_model=DetailedResultsResponse)
async def get_results(attempt_id: UUID, current_user: dict = Depends(get_current_user)):
    """Get detailed results with correct answers"""
    db = await get_supabase_admin_client()
    user_id = current_user["id"]

    # Get attempt with test info
    attempt = (
        await db.table("test_attempts")
        .select("*, tests(*)")
        .eq("id", str(attempt_id))
        .single()
        .execute()
    )

    if not attempt.data:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.data["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not attempt.data["is_completed"]:
        raise HTTPException(status_code=400, detail="Test not completed")

    # Get questions with user's answers
    questions = (
        await db.table("questions")
        .select("*")
        .eq("test_id", attempt.data["test_id"])
        .order("order_number")
        .execute()
    )

    user_answers = attempt.data["answers"]
    results = []

    for q in questions.data:
        qid = q["id"]
        user_answer = user_answers.get(qid)
        is_correct = user_answer == q["correct_option"]
        results.append(
            {
                "question": q,
                "user_answer": user_answer,
                "correct_answer": q["correct_option"],
                "is_correct": is_correct,
                "explanation": q.get("explanation"),
            }
        )

    return {"attempt": attempt.data, "results": results}


# ═══════════════════════════════════════════════════════════════
# GET /users/me/stats - Get user statistics
# ═══════════════════════════════════════════════════════════════
@router.get("/users/me/stats", response_model=UserStatsResponse)
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """Get user's test prep statistics"""
    db = await get_supabase_admin_client()
    user_id = current_user["id"]

    stats = await db.table("user_stats").select("*").eq("user_id", user_id).maybe_single().execute()

    if not stats:
        # Create initial stats
        await db.table("user_stats").insert({"user_id": user_id}).execute()
        return UserStatsResponse(user_id=user_id, best_test_id=None, last_attempt_at=None)

    return stats.data


# ═══════════════════════════════════════════════════════════════
# GET /users/me/attempts - Get attempt history
# ═══════════════════════════════════════════════════════════════
@router.get("/users/me/attempts", response_model=list[AttemptHistoryResponse])
async def get_user_attempts(limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Get user's test attempt history"""
    db = await get_supabase_admin_client()
    user_id = current_user["id"]

    attempts = (
        await db.table("test_attempts")
        .select(
            "id, test_id, tests(title, exam_type), submitted_at, score, total_questions, accuracy"
        )
        .eq("user_id", user_id)
        .eq("is_completed", True)
        .order("submitted_at", desc=True)
        .limit(limit)
        .execute()
    )

    # Flatten the response
    result = []
    for attempt in attempts.data:
        result.append(
            {
                "id": attempt["id"],
                "test_id": attempt["test_id"],
                "test_title": attempt["tests"]["title"] if attempt.get("tests") else "Unknown",
                "exam_type": attempt["tests"]["exam_type"] if attempt.get("tests") else None,
                "submitted_at": attempt["submitted_at"],
                "score": attempt["score"],
                "total_questions": attempt["total_questions"],
                "accuracy": attempt["accuracy"],
            }
        )

    return result


# ═══════════════════════════════════════════════════════════════
# POST /questions/{question_id}/report - Report question
# ═══════════════════════════════════════════════════════════════
@router.post("/questions/{question_id}/report")
async def report_question(
    question_id: UUID, report: QuestionReportRequest, current_user: dict = Depends(get_current_user)
):
    """Report a problem with a question"""
    db = await get_supabase_admin_client()
    user_id = current_user["id"]

    # Get current flag value
    question = (
        await db.table("questions").select("flag").eq("id", str(question_id)).single().execute()
    )

    if not question.data:
        raise HTTPException(status_code=404, detail="Question not found")

    # Increment flag count
    current_flags = question.data.get("flag", 0) or 0
    # convert current_flags to int if it's not already
    if isinstance(current_flags, str):
        try:
            current_flags = int(current_flags)
        except ValueError:
            current_flags = 0

    await (
        db.table("questions")
        .update({"flag": current_flags + 1})
        .eq("id", str(question_id))
        .execute()
    )

    # Log report
    await (
        db.table("question_reports")
        .insert(
            {
                "user_id": user_id,
                "question_id": str(question_id),
                "reason": report.reason,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
            }
        )
        .execute()
    )

    return {"message": "Question reported successfully"}


# ═══════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════


async def update_user_stats(
    db,
    user_id: str,
    correct_count: int,
    wrong_count: int,
    total_questions: int,
    score: int,
    test_id: str,
):
    """Update user statistics after test submission"""
    # Get or create user stats
    stats = await db.table("user_stats").select("*").eq("user_id", user_id).maybe_single().execute()

    if not stats:
        # Create new stats
        await (
            db.table("user_stats")
            .insert(
                {
                    "user_id": user_id,
                    "total_attempts": 1,
                    "total_questions_attempted": total_questions,
                    "total_correct": correct_count,
                    "total_wrong": wrong_count,
                    "overall_accuracy": round((correct_count / total_questions * 100), 2)
                    if total_questions > 0
                    else 0,
                    "best_score": score,
                    "best_test_id": test_id,
                    "last_attempt_at": datetime.now().isoformat(),
                }
            )
            .execute()
        )
    else:
        # Update existing stats
        current_stats = stats.data
        new_total_correct = (current_stats.get("total_correct", 0) or 0) + correct_count
        new_total_questions = (
            current_stats.get("total_questions_attempted", 0) or 0
        ) + total_questions
        new_total_wrong = (current_stats.get("total_wrong", 0) or 0) + wrong_count
        new_accuracy = (
            round((new_total_correct / new_total_questions * 100), 2)
            if new_total_questions > 0
            else 0
        )

        await (
            db.table("user_stats")
            .update(
                {
                    "total_attempts": (current_stats.get("total_attempts", 0) or 0) + 1,
                    "total_questions_attempted": new_total_questions,
                    "total_correct": new_total_correct,
                    "total_wrong": new_total_wrong,
                    "overall_accuracy": new_accuracy,
                    "best_score": max(current_stats.get("best_score", 0) or 0, score),
                    "last_attempt_at": datetime.now().isoformat(),
                }
            )
            .eq("user_id", user_id)
            .execute()
        )
