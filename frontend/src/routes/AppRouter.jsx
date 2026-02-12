import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '../components/ProtectedRoute';


import Login from '../features/auth/Login';
import Register from '../features/auth/Register';
import ForgotPassword from '../features/auth/ForgotPassword';


import UserDashboard from '../features/user/UserDashboard';
import UserProfile from '../features/user/UserProfile';


import QuizSetup from '../features/quiz/QuizSetup';
import QuestionDisplay from '../features/quiz/play/QuestionDisplay';
import QuizDetails from '../features/quiz/QuizDetails';
import QuizHistory from '../features/quiz/QuizHistory';


import AdminPanel from '../features/admin/AdminPanel';


import QuestionsLibrary from '../features/library/QuestionsLibrary';
import Leaderboard from '../features/leaderboard/Leaderboard';


import NotFound from '../pages/errors/NotFound';
import Forbidden from '../pages/errors/Forbidden';
import ServerError from '../pages/errors/ServerError';

export default function AppRouter() {
    return (
        <Routes>
            <Route path="/" element={<Navigate to="/login" />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />

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

            <Route path="/quiz/setup" element={
                <ProtectedRoute>
                    <QuizSetup />
                </ProtectedRoute>
            } />

            <Route path="/quiz/play/:sessionId" element={
                <ProtectedRoute>
                    <QuestionDisplay />
                </ProtectedRoute>
            } />

            <Route path="/quiz/play" element={
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

            <Route path="/leaderboard" element={
                <ProtectedRoute>
                    <Leaderboard />
                </ProtectedRoute>
            } />

            <Route path="/admin" element={
                <ProtectedRoute>
                    <AdminPanel />
                </ProtectedRoute>
            } />

            <Route path="/403" element={<Forbidden />} />
            <Route path="/500" element={<ServerError />} />
            <Route path="/404" element={<NotFound />} />
            <Route path="*" element={<NotFound />} />
        </Routes>
    );
}
