from rest_framework.exceptions import APIException
from rest_framework import status


class QuizException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Wystąpił błąd podczas operacji quizu'
    default_code = 'quiz_error'


class QuizNotFound(QuizException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Nie znaleziono sesji quizu'
    default_code = 'quiz_not_found'


class QuizAlreadyCompleted(QuizException):
    default_detail = 'Ten quiz został już ukończony'
    default_code = 'quiz_already_completed'


class QuizSessionInactive(QuizException):
    default_detail = 'Sesja quizu nie jest już aktywna'
    default_code = 'quiz_session_inactive'


class QuestionGenerationError(QuizException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Nie udało się wygenerować pytania'
    default_code = 'question_generation_error'


class InsufficientQuestionsError(QuizException):
    default_detail = 'Niewystarczająca liczba pytań dla podanych kryteriów'
    default_code = 'insufficient_questions'


class QuestionNotFound(QuizException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Nie znaleziono pytania'
    default_code = 'question_not_found'


class InvalidAnswerError(QuizException):
    default_detail = 'Nieprawidłowa odpowiedź'
    default_code = 'invalid_answer'


class AnswerAlreadySubmitted(QuizException):
    default_detail = 'Odpowiedź na to pytanie została już udzielona'
    default_code = 'answer_already_submitted'


class DifficultyAdaptationError(QuizException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Nie udało się dostosować poziomu trudności'
    default_code = 'difficulty_adaptation_error'


class UserException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Wystąpił błąd operacji użytkownika'
    default_code = 'user_error'


class UserNotFound(UserException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Nie znaleziono użytkownika'
    default_code = 'user_not_found'


class UserAlreadyExists(UserException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Użytkownik o podanym adresie email już istnieje'
    default_code = 'user_already_exists'


class InvalidCredentials(UserException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Nieprawidłowy email lub hasło'
    default_code = 'invalid_credentials'


class PermissionDenied(UserException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Brak uprawnień do wykonania tej operacji'
    default_code = 'permission_denied'


class ProfileNotFound(UserException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Nie znaleziono profilu użytkownika'
    default_code = 'profile_not_found'


class InvalidPasswordResetCode(UserException):
    default_detail = 'Nieprawidłowy lub wygasły kod resetowania hasła'
    default_code = 'invalid_reset_code'


class ValidationException(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Błąd walidacji danych'
    default_code = 'validation_error'

    def __init__(self, detail=None, field_errors=None):
        if field_errors:
            detail = {'field_errors': field_errors}
        super().__init__(detail)


class CacheException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Błąd operacji cache'
    default_code = 'cache_error'


class LLMIntegrationError(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Usługa LLM jest niedostępna'
    default_code = 'llm_service_error'