/**
 * Application route constants
 */

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',

  // Quiz routes
  QUIZ_SETUP: '/quiz',
  QUIZ_QUESTION: '/quiz/question/:sessionId',
  QUIZ_DETAILS: '/quiz/details/:sessionId',
  QUIZ_HISTORY: '/quiz/history',
  QUESTIONS_LIBRARY: '/quiz/questions',

  // User routes
  DASHBOARD: '/dashboard',
  PROFILE: '/profile',

  // Admin routes
  ADMIN_PANEL: '/admin',
};

/**
 * Helper functions for route generation
 */
export const generateRoute = {
  quizQuestion: (sessionId) => `/quiz/question/${sessionId}`,
  quizDetails: (sessionId) => `/quiz/details/${sessionId}`,
};
