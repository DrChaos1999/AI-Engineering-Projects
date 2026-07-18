from database.database import (
    QuestionLimitReached,
    consume_question,
    create_database,
    get_or_create_session,
    get_session_status,
)


def test_session_question_limit(tmp_path):
    create_database(tmp_path / "test.db")
    session = get_or_create_session(
        existing_session_id=None,
        access_key_hash="customer-hash",
        limit_minutes=5,
        max_questions=1,
    )
    assert session.active
    consumed = consume_question(session.session_id)
    assert consumed.question_count == 1
    assert not consumed.active

    try:
        consume_question(session.session_id)
    except QuestionLimitReached:
        pass
    else:
        raise AssertionError("QuestionLimitReached was not raised")


def test_access_code_reuses_same_allocation(tmp_path):
    create_database(tmp_path / "test.db")
    first = get_or_create_session(
        existing_session_id=None,
        access_key_hash="same-customer",
        limit_minutes=10,
        max_questions=5,
    )
    second = get_or_create_session(
        existing_session_id=None,
        access_key_hash="same-customer",
        limit_minutes=10,
        max_questions=5,
    )
    assert first.session_id == second.session_id
    assert get_session_status(first.session_id) is not None
