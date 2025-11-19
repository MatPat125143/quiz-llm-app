from llm_integration.question_generator import QuestionGenerator
from llm_integration.difficulty_adapter import DifficultyAdapter
from .question_service import QuestionService
from ..models import QuizSession, Answer, QuizSessionQuestion, Question

generator = QuestionGenerator()
difficulty_adapter = DifficultyAdapter()
question_service = QuestionService()


class AnswerService:
    """Logika biznesowa dla sprawdzania odpowiedzi i generowania kolejnych pytań"""

    def generate_new_batch_after_difficulty_change(self, session_id, to_generate):
        """Generuje nową partię pytań po zmianie poziomu trudności"""
        try:
            session_refresh = QuizSession.objects.get(id=session_id)

            unused_questions = QuizSessionQuestion.objects.filter(
                session=session_refresh
            ).exclude(
                question_id__in=Answer.objects.filter(session=session_refresh)
                .values_list('question_id', flat=True)
            )

            unused_question_ids = list(unused_questions.values_list('question_id', flat=True))
            deleted_count = len(unused_question_ids)

            unused_questions.delete()
            print(f"🗑️ Deleted {deleted_count} QuizSessionQuestion")

            orphans_deleted = 0
            for question_id in unused_question_ids:
                try:
                    other_sessions = QuizSessionQuestion.objects.filter(
                        question_id=question_id).exists()
                    has_answers = Answer.objects.filter(question_id=question_id).exists()

                    if not other_sessions and not has_answers:
                        Question.objects.filter(id=question_id).delete()
                        orphans_deleted += 1
                except Exception as e:
                    print(f"⚠️ Could not delete Question ID={question_id}: {e}")

            if orphans_deleted > 0:
                print(f"✅ Deleted {orphans_deleted} orphan Questions")

            all_questions_data = generator.generate_multiple_questions(
                session_refresh.topic,
                session_refresh.current_difficulty,
                to_generate,
                subtopic=session_refresh.subtopic,
                knowledge_level=session_refresh.knowledge_level
            )

            all_questions_data = all_questions_data[:to_generate]

            difficulty_text = difficulty_adapter.get_difficulty_level(
                session_refresh.current_difficulty)

            seen_texts = set(
                Answer.objects.filter(session=session_refresh)
                .values_list('question__question_text', flat=True)
            )

            for i, question_data in enumerate(all_questions_data):
                q, created = question_service.find_or_create_global_question(
                    session_refresh.topic,
                    question_data,
                    difficulty_text,
                    user=session_refresh.user,
                    subtopic=session_refresh.subtopic,
                    knowledge_level=session_refresh.knowledge_level
                )

                if q.question_text not in seen_texts:
                    order = QuizSessionQuestion.objects.filter(session=session_refresh).count()
                    question_service.add_question_to_session(session_refresh, q, order=order)
                    seen_texts.add(q.question_text)

            session_refresh.questions_generated_count = Answer.objects.filter(session=session_refresh).count() + to_generate
            session_refresh.save(update_fields=['questions_generated_count'])
            print(f"✅ Generated {to_generate} questions")

        except Exception as e:
            print(f"❌ Error generating batch: {e}")
            import traceback
            traceback.print_exc()

    def generate_backup_questions(self, session_id, needed):
        """Generuje zapasowe pytania w trybie adaptacyjnym"""
        try:
            session_refresh = QuizSession.objects.get(id=session_id)
            difficulty_text = difficulty_adapter.get_difficulty_level(
                session_refresh.current_difficulty)

            seen_texts = set(
                Answer.objects.filter(session=session_refresh)
                .values_list('question__question_text', flat=True)
            )
            seen_texts |= set(
                QuizSessionQuestion.objects.filter(session=session_refresh)
                .select_related('question')
                .values_list('question__question_text', flat=True)
            )

            questions_added = 0
            max_attempts_per_question = 3

            for i in range(needed):
                question_added = False

                for attempt in range(max_attempts_per_question):
                    question_data = generator.generate_question(
                        session_refresh.topic,
                        session_refresh.current_difficulty,
                        subtopic=session_refresh.subtopic,
                        knowledge_level=session_refresh.knowledge_level
                    )

                    q, created = question_service.find_or_create_global_question(
                        session_refresh.topic,
                        question_data,
                        difficulty_text,
                        user=session_refresh.user,
                        subtopic=session_refresh.subtopic,
                        knowledge_level=session_refresh.knowledge_level
                    )

                    if q.question_text in seen_texts:
                        continue

                    order = QuizSessionQuestion.objects.filter(session=session_refresh).count()
                    session_question = question_service.add_question_to_session(session_refresh, q, order=order)

                    if session_question is not None:
                        questions_added += 1
                        seen_texts.add(q.question_text)
                        question_added = True
                        break
                    else:
                        seen_texts.add(q.question_text)

                        try:
                            if not QuizSessionQuestion.objects.filter(
                                    question_id=q.id).exists() and not Answer.objects.filter(
                                question_id=q.id).exists():
                                q.delete()
                        except:
                            pass

                if not question_added:
                    print(f"❌ Failed to generate backup {i + 1}/{needed}")

            if questions_added > 0:
                print(f"✅ Generated {questions_added}/{needed} backups")
            else:
                fallback = Question.objects.filter(
                    topic=session_refresh.topic,
                    difficulty_level=difficulty_text,
                    subtopic=session_refresh.subtopic if session_refresh.subtopic else None,
                    knowledge_level=session_refresh.knowledge_level
                ).exclude(
                    question_text__in=seen_texts
                ).order_by('-times_used').first()

                if not fallback and session_refresh.subtopic:
                    fallback = Question.objects.filter(
                        topic=session_refresh.topic,
                        difficulty_level=difficulty_text,
                        knowledge_level=session_refresh.knowledge_level
                    ).exclude(
                        question_text__in=seen_texts
                    ).order_by('-times_used').first()

                if fallback:
                    order = QuizSessionQuestion.objects.filter(session=session_refresh).count()
                    session_question = question_service.add_question_to_session(session_refresh, fallback,
                                                                                order=order)
                    if session_question:
                        print(f"✅ Used fallback question")

        except Exception as e:
            print(f"❌ Error generating backup: {e}")

    def generate_next_batch_fixed_mode(self, session_id, to_generate):
        """Generuje kolejną partię pytań w trybie stałej trudności"""
        try:
            session_refresh = QuizSession.objects.get(id=session_id)
            all_questions_data = generator.generate_multiple_questions(
                session_refresh.topic,
                session_refresh.current_difficulty,
                to_generate,
                subtopic=session_refresh.subtopic,
                knowledge_level=session_refresh.knowledge_level
            )

            all_questions_data = all_questions_data[:to_generate]

            difficulty_text = difficulty_adapter.get_difficulty_level(
                session_refresh.current_difficulty)

            for i, question_data in enumerate(all_questions_data):
                q, created = question_service.find_or_create_global_question(
                    session_refresh.topic,
                    question_data,
                    difficulty_text,
                    user=session_refresh.user,
                    subtopic=session_refresh.subtopic,
                    knowledge_level=session_refresh.knowledge_level
                )
                order = session_refresh.questions_generated_count + i
                question_service.add_question_to_session(session_refresh, q, order=order)

            session_refresh.questions_generated_count += to_generate
            session_refresh.save(update_fields=['questions_generated_count'])
            print(f"✅ Generated batch of {to_generate}")

        except Exception as e:
            print(f"❌ Error generating batch: {e}")