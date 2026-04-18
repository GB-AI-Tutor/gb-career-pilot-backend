# from database. import create_client

from src.database.database import get_supabase_admin_client

db = get_supabase_admin_client()


# Example: Import questions from OpenPrep
# You'll need to adapt this based on OpenPrep's actual data format
def import_nust_mock_test():
    """Import NUST mock test from OpenPrep"""  # First, create the test
    test_data = {
        "title": "NUST NET Mock Test 1 (from OpenPrep)",
        "description": "Full-length NUST practice test with 100 questions",
        "type": "mock_test",
        "duration_minutes": 120,
        "total_questions": 100,
        "exam_type": "NUST NET",
        "is_published": True,
    }
    test_result = db.table("tests").insert(test_data).execute()
    test_id = test_result.data[0]["id"]
    print(f"✅ Created test: {test_id}")
    # Now import questions
    # This is a template - adapt based on your OpenPrep data format
    sample_questions = [
        {
            "test_id": test_id,
            "question_text": "What is the value of x in: 2x + 5 = 15?",
            "option_a": "5",
            "option_b": "10",
            "option_c": "7.5",
            "option_d": "15",
            "correct_option": "a",
            "explanation": "Solving: 2x = 15 - 5 = 10, therefore x = 5",
            "subject": "Math",
            "difficulty": "easy",
            "order_number": 1,
        },
        # Add more questions here...
    ]
    for question in sample_questions:
        db.table("questions").insert(question).execute()
        print(f"✅ Imported question {question['order_number']}")

    print(f"\n✅ Successfully imported {len(sample_questions)} questions!")


if __name__ == "__main__":
    import_nust_mock_test()
