from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import os
import json


class QuestionGenerator:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY", "")

        # Sprawdź czy klucz API jest ustawiony
        if not api_key or api_key == "sk-your-openai-api-key-here":
            print("⚠️  WARNING: OPENAI_API_KEY not set! Using fake questions.")
            self.llm = None
        else:
            try:
                self.llm = ChatOpenAI(
                    model="gpt-4",
                    api_key=api_key,
                    temperature=0.7
                )
            except Exception as e:
                print(f"⚠️  WARNING: Failed to initialize OpenAI: {e}")
                self.llm = None

    def generate_question(self, topic, difficulty):
        # Jeśli brak API key, zwróć fake question
        if self.llm is None:
            return self._generate_fake_question(topic, difficulty)

        try:
            prompt = PromptTemplate(
                input_variables=["topic", "difficulty"],
                template="""
                Wygeneruj pytanie quizowe na temat: {topic}
                Poziom trudności: {difficulty} (skala 1-10)

                Zwróć odpowiedź TYLKO w formacie JSON (bez dodatkowego tekstu):
                {{
                    "question": "treść pytania",
                    "correct_answer": "poprawna odpowiedź",
                    "wrong_answers": ["błędna1", "błędna2", "błędna3"],
                    "explanation": "krótkie uzasadnienie"
                }}
                """
            )

            response = self.llm.invoke(prompt.format(topic=topic, difficulty=difficulty))
            content = response.content.strip()

            # Usuń markdown code blocks
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            content = content.strip()
            question_data = json.loads(content)
            return question_data

        except Exception as e:
            print(f"Error generating question with LLM: {e}")
            return self._generate_fake_question(topic, difficulty)

    def _generate_fake_question(self, topic, difficulty):
        """Fallback - fake questions gdy brak LLM"""
        import random

        questions = [
            {
                'question': f'What is the capital of France? (Topic: {topic}, Difficulty: {difficulty})',
                'correct_answer': 'Paris',
                'wrong_answers': ['London', 'Berlin', 'Madrid'],
                'explanation': 'Paris is the capital and largest city of France.'
            },
            {
                'question': f'What is 2 + 2? (Topic: {topic}, Difficulty: {difficulty})',
                'correct_answer': '4',
                'wrong_answers': ['3', '5', '22'],
                'explanation': 'Basic arithmetic: 2 + 2 equals 4.'
            },
            {
                'question': f'What color is the sky on a clear day? (Topic: {topic}, Difficulty: {difficulty})',
                'correct_answer': 'Blue',
                'wrong_answers': ['Green', 'Red', 'Yellow'],
                'explanation': 'The sky appears blue due to Rayleigh scattering.'
            },
            {
                'question': f'How many continents are there? (Topic: {topic}, Difficulty: {difficulty})',
                'correct_answer': '7',
                'wrong_answers': ['5', '6', '8'],
                'explanation': 'There are 7 continents: Africa, Antarctica, Asia, Europe, North America, Australia, South America.'
            },
        ]

        return random.choice(questions)