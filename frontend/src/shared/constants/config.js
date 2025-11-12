/**
 * Application configuration constants
 */

export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  TIMEOUT: 30000,
};

export const QUIZ_LIMITS = {
  MIN_QUESTIONS: 5,
  MAX_QUESTIONS: 20,
  MIN_TIME: 10,
  MAX_TIME: 60,
  DEFAULT_QUESTIONS: 10,
  DEFAULT_TIME: 30,
};

export const DIFFICULTY_LEVELS = {
  EASY: 'easy',
  MEDIUM: 'medium',
  HARD: 'hard',
};

export const DIFFICULTY_LABELS = {
  łatwy: 'Łatwy',
  średni: 'Średni',
  trudny: 'Trudny',
  easy: 'Łatwy',
  medium: 'Średni',
  hard: 'Trudny',
};

export const KNOWLEDGE_LEVELS = {
  ELEMENTARY: 'elementary',
  HIGH_SCHOOL: 'high_school',
  UNIVERSITY: 'university',
  EXPERT: 'expert',
};

export const KNOWLEDGE_LEVEL_LABELS = {
  elementary: 'Szkoła podstawowa',
  high_school: 'Liceum',
  university: 'Studia',
  expert: 'Ekspert',
};

export const USER_ROLES = {
  USER: 'user',
  ADMIN: 'admin',
};

export const TIMER_CONFIG = {
  WARNING_THRESHOLD: 10, // seconds
  CRITICAL_THRESHOLD: 5, // seconds
};

export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
};

export const CACHE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_DATA: 'user_data',
};
