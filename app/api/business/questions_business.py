from app.api.services import (
    audit_service,
    audit_types,
    briefs,
    brief_clarification_question_service,
    brief_question_service
)
from app.api.business.errors import (
    NotFoundError,
    ValidationError
)
from app.models import (
    BriefClarificationQuestion
)


def get_counts(brief_id, questions=None, answers=None):
    if questions:
        questionsCount = len(questions)
    else:
        questionsCount = len(brief_question_service.get_questions(brief_id))

    if answers:
        answersCount = len(answers)
    else:
        answersCount = len(brief_clarification_question_service.get_answers(brief_id))

    return {
        "questions": questionsCount,
        "answers": answersCount
    }


def get_questions(brief_id):
    brief = briefs.find(id=brief_id).one_or_none()
    if not brief:
        raise NotFoundError("Invalid brief id '{}'".format(brief_id))

    questions = brief_question_service.get_questions(brief_id)

    return {
        "questions": questions,
        "brief": {
            "title": brief.data.get('title'),
            "id": brief.id,
            "internalReference": brief.data.get('internalReference')
        },
        "questionCount": get_counts(brief_id, questions=questions)
    }


def get_answers(brief_id):
    brief = briefs.find(id=brief_id).one_or_none()
    if not brief:
        raise NotFoundError("Invalid brief id '{}'".format(brief_id))

    answers = brief_clarification_question_service.get_answers(brief_id)

    return {
        "answers": answers,
        "brief": {
            "title": brief.data.get('title'),
            "id": brief.id,
            "internalReference": brief.data.get('internalReference')
        },
        "questionCount": get_counts(brief_id, answers=answers)
    }


def publish_answer(user_info, brief_id, data):
    brief = briefs.get(brief_id)
    if not brief:
        raise NotFoundError("Invalid brief id '{}'".format(brief_id))

    question = data.get('question')
    if not question:
        raise ValidationError('Question is required')

    answer = data.get('answer')
    if not answer:
        raise ValidationError('Answer is required')

    brief_clarification_question = brief_clarification_question_service.save(BriefClarificationQuestion(
        _brief_id=brief_id,
        question=question,
        answer=answer,
        user_id=user_info.get('user_id')
    ))

    audit_service.log_audit_event(
        audit_type=audit_types.create_brief_clarification_question,
        user=user_info.get('email_address'),
        data={
            'briefId': brief.id
        },
        db_object=brief_clarification_question)


def mark_question_as_answered(user_info, question_id, data):
    question = brief_question_service.get(question_id)

    if not question:
        raise NotFoundError('Question not found')

    answered = data.get('answered')
    if answered is None:
        raise ValidationError('Answered is required')

    question.answered = answered
    brief_question_service.save(question)
