import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    }
});

// Request interceptor - dodaj token do każdego requesta
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor - refresh token gdy wygaśnie
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const refreshToken = localStorage.getItem('refresh_token');
                const response = await axios.post(`${API_URL}/auth/jwt/refresh/`, {
                    refresh: refreshToken
                });

                localStorage.setItem('access_token', response.data.access);
                originalRequest.headers.Authorization = `Bearer ${response.data.access}`;

                return api(originalRequest);
            } catch (refreshError) {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

// ==================== AUTH ====================

export const register = async (email, username, password) => {
    const response = await api.post('/auth/users/', {
        email,
        username: username || email.split('@')[0], // Username opcjonalny
        password,
        re_password: password
    });
    return response.data;
};

export const login = async (email, password) => {
    // Logowanie przez email
    const response = await api.post('/auth/jwt/create/', {
        email,
        password
    });

    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);

    return response.data;
};

export const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
};

// ==================== USER PROFILE ====================

export const getCurrentUser = async () => {
    const response = await api.get('/users/me/');
    return response.data;
};

export const updateProfile = async (data) => {
    const response = await api.put('/users/update/', data);
    return response.data;
};

export const changePassword = async (oldPassword, newPassword) => {
    const response = await api.post('/users/change-password/', {
        old_password: oldPassword,
        new_password: newPassword
    });
    return response.data;
};

export const uploadAvatar = async (file) => {
    const formData = new FormData();
    formData.append('avatar', file);

    const response = await api.post('/users/avatar/upload/', formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    });
    return response.data;
};

export const deleteAvatar = async () => {
    const response = await api.delete('/users/avatar/delete/');
    return response.data;
};

// ==================== QUIZ ====================

export const startQuiz = async (topic, difficulty, questionsCount, timePerQuestion, useAdaptiveDifficulty, subtopic = '', knowledgeLevel = 'high_school') => {
    const response = await api.post('/quiz/start/', {
        topic,
        subtopic,
        knowledge_level: knowledgeLevel,
        difficulty,
        questions_count: questionsCount,
        time_per_question: timePerQuestion,
        use_adaptive_difficulty: useAdaptiveDifficulty
    });
    return response.data;
};

export const getQuestion = async (sessionId) => {
    const response = await api.get(`/quiz/question/${sessionId}/`);
    return response.data;
};

export const submitAnswer = async (questionId, selectedAnswer, responseTime) => {
    const response = await api.post('/quiz/answer/', {
        question_id: questionId,
        selected_answer: selectedAnswer,
        response_time: responseTime
    });
    return response.data;
};

export const endQuiz = async (sessionId) => {
    const response = await api.post(`/quiz/end/${sessionId}/`);
    return response.data;
};

export const getQuizHistory = async () => {
    const response = await api.get('/quiz/history/');
    return response.data;
};

export const getQuizDetails = async (sessionId) => {
    const response = await api.get(`/quiz/details/${sessionId}/`);
    return response.data;
};

export const getQuestionsLibrary = async (params = {}) => {
    const response = await api.get('/quiz/questions/', { params });
    return response.data;
};

// ==================== ADMIN ====================

export const getAdminDashboard = async () => {
    const response = await api.get('/admin/dashboard/');
    return response.data;
};

export const getAllUsers = async () => {
    const response = await api.get('/admin/users/');
    return response.data;
};

export const deleteUser = async (userId) => {
    const response = await api.delete(`/admin/users/${userId}/delete/`);
    return response.data;
};

export const changeUserRole = async (userId, role) => {
    const response = await api.patch(`/admin/users/${userId}/role/`, { role });
    return response.data;
};

export const toggleUserStatus = async (userId) => {
    const response = await api.patch(`/admin/users/${userId}/toggle/`);
    return response.data;
};

export const requestPasswordReset = async (email) => {
    const response = await api.post('/users/password-reset/request/', { email });
    return response.data;
};

export const verifyResetCode = async (email, code) => {
    const response = await api.post('/users/password-reset/verify/', { email, code });
    return response.data;
};

export const resetPasswordWithCode = async (email, code, newPassword) => {
    const response = await api.post('/users/password-reset/confirm/', {
        email,
        code,
        new_password: newPassword
    });
    return response.data;
};

export async function adminSearchUsers(params = {}) {
  const query = new URLSearchParams(params).toString();
  return api.get(`/admin/users/search/?${query}`).then(res => res.data);
}

export async function adminGetUserQuizzes(userId) {
  return api.get(`/admin/users/${userId}/quizzes/`).then(res => res.data);
}

export async function adminDeleteQuizSession(sessionId) {
  return api.delete(`/admin/sessions/${sessionId}/delete/`).then(res => res.data);
}


export default api;