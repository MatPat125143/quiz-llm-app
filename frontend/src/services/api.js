import api from './apiClient';

export const register = async (email, username, password, defaultKnowledgeLevel = 'high_school') => {
    const response = await api.post('/auth/users/', {
        email,
        username: username || email.split('@')[0],
        password,
        re_password: password,
        default_knowledge_level: defaultKnowledgeLevel
    });
    return response.data;
};

export const login = async (email, password) => {
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



export const getCurrentUser = async () => {
    const response = await api.get('/users/me/');
    return response.data;
};

export const updateProfile = async (data) => {
    const response = await api.put('/users/update/', data);
    return response.data;
};

export const changePassword = async (passwordData) => {
    const response = await api.post('/users/change-password/', passwordData);
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

export const updateProfileSettings = async (data) => {
    const response = await api.put('/users/settings/', data);
    return response.data;
};

export const deleteMyAccount = async () => {
    const response = await api.delete('/users/delete/');
    return response.data;
};



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

export const getQuizHistory = async (params = {}) => {
    const response = await api.get('/quiz/history/', { params });
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



export const getGlobalLeaderboard = async (period = 'all', limit = 50) => {
    const response = await api.get('/quiz/leaderboard/global/', {
        params: { period, limit }
    });
    return response.data;
};

export const getUserRanking = async () => {
    const response = await api.get('/quiz/leaderboard/me/');
    return response.data;
};

export const getLeaderboardStats = async () => {
    const response = await api.get('/quiz/leaderboard/stats/');
    return response.data;
};



export const getAdminDashboard = async () => {
    const response = await api.get('/users/admin/dashboard/');
    return response.data;
};

export const getAllUsers = async () => {
    const response = await api.get('/users/admin/users/');
    return response.data;
};

export const deleteUser = async (userId) => {
    const response = await api.delete(`/users/admin/users/${userId}/delete/`);
    return response.data;
};

export const changeUserRole = async (userId, role) => {
    const response = await api.patch(`/users/admin/users/${userId}/role/`, { role });
    return response.data;
};

export const toggleUserStatus = async (userId) => {
    const response = await api.patch(`/users/admin/users/${userId}/toggle/`);
    return response.data;
};

export const adminSearchUsers = async (params = {}) => {
    const response = await api.get('/users/admin/users/search/', { params });
    return response.data;
};

export const adminGetUserQuizzes = async (userId) => {
    const response = await api.get(`/users/admin/users/${userId}/quizzes/`);
    return response.data;
};

export const adminDeleteQuizSession = async (sessionId) => {
    const response = await api.delete(`/users/admin/sessions/${sessionId}/delete/`);
    return response.data;
};




export const adminGetQuestions = async (params = {}) => {
    const response = await api.get('/quiz/admin/questions/', { params });
    return response.data;
};

export const adminGetQuestionDetail = async (questionId) => {
    const response = await api.get(`/quiz/admin/questions/${questionId}/`);
    return response.data;
};

export const adminUpdateQuestion = async (questionId, data) => {
    const response = await api.put(`/quiz/admin/questions/${questionId}/update/`, data);
    return response.data;
};

export const adminDeleteQuestion = async (questionId) => {
    const response = await api.delete(`/quiz/admin/questions/${questionId}/delete/`);
    return response.data;
};

export const adminGetQuestionStats = async () => {
    const response = await api.get('/quiz/admin/questions/stats/');
    return response.data;
};

export default api;
