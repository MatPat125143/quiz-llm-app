import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '../components/ProtectedRoute';

// Auth
import Login from '../features/auth/Login';
import Register from '../features/auth/Register';
import ForgotPassword from '../features/auth/ForgotPassword';

// User
import UserDashboard from '../features/user/UserDashboard';
import UserProfile from '../features/user/UserProfile';

// Quiz
import QuizSetup from '../features/quiz/QuizSetup';
import QuestionDisplay from '../features/quiz/QuestionDisplay';
import QuizDetails from '../features/quiz/QuizDetails';
import QuizHistory from '../features/quiz/QuizHistory';

// Admin
import AdminPanel from '../features/admin/AdminPanel';

// Library
import QuestionsLibrary from '../features/library/QuestionsLibrary';

export default function AppRouter() {
    return (
        <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Navigate to="/login" />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />

            {/* Protected Routes - User */}
            <Route path="/dashboard" element={
                <ProtectedRoute>
                    <UserDashboard />
                </ProtectedRoute>
            } />

            <Route path="/profile" element={
                <ProtectedRoute>
                    <UserProfile />
                </ProtectedRoute>
            } />

            {/* Protected Routes - Quiz */}
            <Route path="/quiz/setup" element={
                <ProtectedRoute>
                    <QuizSetup />
                </ProtectedRoute>
            } />

            <Route path="/quiz/new" element={
                <ProtectedRoute>
                    <QuizSetup />
                </ProtectedRoute>
            } />

            <Route path="/quiz/play/:sessionId" element={
                <ProtectedRoute>
                    <QuestionDisplay />
                </ProtectedRoute>
            } />

            <Route path="/quiz/details/:sessionId" element={
                <ProtectedRoute>
                    <QuizDetails />
                </ProtectedRoute>
            } />

            <Route path="/quiz/history" element={
                <ProtectedRoute>
                    <QuizHistory />
                </ProtectedRoute>
            } />

            <Route path="/quiz/questions" element={
                <ProtectedRoute>
                    <QuestionsLibrary />
                </ProtectedRoute>
            } />

            {/* Protected Routes - Admin */}
            <Route path="/admin" element={
                <ProtectedRoute>
                    <AdminPanel />
                </ProtectedRoute>
            } />
        </Routes>
    );
}