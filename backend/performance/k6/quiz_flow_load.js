import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

const baseUrl = (__ENV.BASE_URL || 'http://localhost:8000').replace(/\/+$/, '');
const perfEmail = __ENV.PERF_EMAIL;
const perfPassword = __ENV.PERF_PASSWORD;

if (!perfEmail || !perfPassword) {
  throw new Error('Missing PERF_EMAIL or PERF_PASSWORD.');
}

const topic = __ENV.QUIZ_TOPIC || 'Matematyka';
const subtopic = __ENV.QUIZ_SUBTOPIC || '';
const knowledgeLevel = __ENV.QUIZ_KNOWLEDGE_LEVEL || 'high_school';
const difficulty = __ENV.QUIZ_DIFFICULTY || 'medium';
const questionsCount = Number(__ENV.QUIZ_QUESTIONS || 2);
const timePerQuestion = Number(__ENV.QUIZ_TIME_PER_QUESTION || 20);
const useAdaptiveDifficulty = String(
  __ENV.QUIZ_ADAPTIVE === undefined ? 'true' : __ENV.QUIZ_ADAPTIVE
).toLowerCase() === 'true';

const startTrend = new Trend('quiz_start_duration', true);
const getQuestionTrend = new Trend('quiz_get_question_duration', true);
const submitAnswerTrend = new Trend('quiz_submit_answer_duration', true);
const endTrend = new Trend('quiz_end_duration', true);

const authFailures = new Counter('quiz_auth_failures');
const flowFailures = new Counter('quiz_flow_failures');

const jsonHeaders = { 'Content-Type': 'application/json' };

export const options = {
  scenarios: {
    quiz_flow: {
      executor: 'constant-vus',
      vus: Number(__ENV.VUS || 2),
      duration: __ENV.DURATION || '1m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.10'],
    http_req_duration: ['p(95)<5000'],
    quiz_start_duration: ['p(95)<8000'],
    quiz_get_question_duration: ['p(95)<5000'],
    quiz_submit_answer_duration: ['p(95)<5000'],
    quiz_end_duration: ['p(95)<4000'],
  },
};

function asJson(response) {
  try {
    return response.json();
  } catch {
    return null;
  }
}

function login() {
  const response = http.post(
    `${baseUrl}/api/auth/jwt/create/`,
    JSON.stringify({
      email: perfEmail,
      password: perfPassword,
    }),
    { headers: jsonHeaders, tags: { endpoint: 'auth_jwt_create' } }
  );

  const ok = check(response, {
    'login status is 200': (r) => r.status === 200,
    'login has access token': (r) => !!asJson(r)?.access,
  });

  if (!ok) {
    authFailures.add(1);
    return null;
  }

  return asJson(response).access;
}

function startQuiz(accessToken) {
  const response = http.post(
    `${baseUrl}/api/quiz/start/`,
    JSON.stringify({
      topic,
      subtopic,
      knowledge_level: knowledgeLevel,
      difficulty,
      questions_count: questionsCount,
      time_per_question: timePerQuestion,
      use_adaptive_difficulty: useAdaptiveDifficulty,
    }),
    {
      headers: {
        ...jsonHeaders,
        Authorization: `Bearer ${accessToken}`,
      },
      tags: { endpoint: 'quiz_start' },
    }
  );

  startTrend.add(response.timings.duration);

  const body = asJson(response);
  const ok = check(response, {
    'start quiz status is 201': (r) => r.status === 201,
    'start quiz has session id': () => Number.isInteger(body?.session_id),
  });

  if (!ok) {
    flowFailures.add(1);
    return null;
  }

  return body.session_id;
}

function getQuestion(accessToken, sessionId) {
  const response = http.get(`${baseUrl}/api/quiz/question/${sessionId}/`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    tags: { endpoint: 'quiz_get_question' },
  });

  getQuestionTrend.add(response.timings.duration);

  const ok = check(response, {
    'get question status is 200 or 404': (r) => r.status === 200 || r.status === 404,
  });

  if (!ok) {
    flowFailures.add(1);
  }

  if (response.status === 404) {
    return null;
  }

  return response;
}

function submitAnswer(accessToken, questionId, selectedAnswer) {
  const response = http.post(
    `${baseUrl}/api/quiz/answer/`,
    JSON.stringify({
      question_id: questionId,
      selected_answer: selectedAnswer,
      response_time: Number(__ENV.RESPONSE_TIME || 3),
    }),
    {
      headers: {
        ...jsonHeaders,
        Authorization: `Bearer ${accessToken}`,
      },
      tags: { endpoint: 'quiz_submit_answer' },
    }
  );

  submitAnswerTrend.add(response.timings.duration);

  const ok = check(response, {
    'submit answer status is 200': (r) => r.status === 200,
  });

  if (!ok) {
    flowFailures.add(1);
  }
}

function endQuiz(accessToken, sessionId) {
  const response = http.post(
    `${baseUrl}/api/quiz/end/${sessionId}/`,
    '{}',
    {
      headers: {
        ...jsonHeaders,
        Authorization: `Bearer ${accessToken}`,
      },
      tags: { endpoint: 'quiz_end' },
    }
  );

  endTrend.add(response.timings.duration);

  const ok = check(response, {
    'end quiz status is 200 or 400': (r) => r.status === 200 || r.status === 400,
  });

  if (!ok) {
    flowFailures.add(1);
  }
}

export default function () {
  const token = login();
  if (!token) {
    return;
  }

  const sessionId = startQuiz(token);
  if (!sessionId) {
    return;
  }

  for (let i = 0; i < questionsCount; i += 1) {
    const questionResponse = getQuestion(token, sessionId);
    if (!questionResponse) {
      break;
    }

    const questionPayload = asJson(questionResponse);
    const questionId = questionPayload?.question_id;
    const answers = Array.isArray(questionPayload?.answers) ? questionPayload.answers : [];

    if (!questionId || answers.length === 0) {
      flowFailures.add(1);
      break;
    }

    submitAnswer(token, questionId, answers[0]);

    if (Number(questionPayload?.questions_remaining || 0) <= 1) {
      break;
    }

    sleep(Number(__ENV.BETWEEN_QUESTIONS_SLEEP || 0.2));
  }

  endQuiz(token, sessionId);
  sleep(Number(__ENV.ITERATION_SLEEP || 0.5));
}
