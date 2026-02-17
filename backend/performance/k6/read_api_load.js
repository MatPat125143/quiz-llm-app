import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

const baseUrl = (__ENV.BASE_URL || 'http://localhost:8000').replace(/\/+$/, '');
const perfEmail = __ENV.PERF_EMAIL;
const perfPassword = __ENV.PERF_PASSWORD;

if (!perfEmail || !perfPassword) {
  throw new Error('Missing PERF_EMAIL or PERF_PASSWORD.');
}

const readTrend = new Trend('read_api_duration', true);
const authFailures = new Counter('read_api_auth_failures');
const readFailures = new Counter('read_api_failures');

const jsonHeaders = { 'Content-Type': 'application/json' };

export const options = {
  scenarios: {
    read_api: {
      executor: 'constant-vus',
      vus: Number(__ENV.VUS || 8),
      duration: __ENV.DURATION || '2m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<2500'],
    read_api_duration: ['p(95)<2500'],
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

function authGet(token, path, endpointTag) {
  const response = http.get(`${baseUrl}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
    tags: { endpoint: endpointTag },
  });

  readTrend.add(response.timings.duration);

  const ok = check(response, {
    [`${endpointTag} status is 200`]: (r) => r.status === 200,
  });

  if (!ok) {
    readFailures.add(1);
  }

  return response;
}

export default function () {
  const token = login();
  if (!token) {
    return;
  }

  authGet(token, '/api/users/me/', 'users_me');
  authGet(token, '/api/quiz/history/?page=1&page_size=10', 'quiz_history');
  authGet(token, '/api/quiz/questions/?page=1&page_size=20', 'questions_library');
  authGet(token, '/api/quiz/leaderboard/global/?period=all&limit=20', 'leaderboard_global');
  authGet(token, '/api/quiz/leaderboard/me/', 'leaderboard_me');

  sleep(Number(__ENV.ITERATION_SLEEP || 0.5));
}
