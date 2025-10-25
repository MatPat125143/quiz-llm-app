import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Register from './components/Register';
import ForgotPassword from './components/ForgotPassword';
import UserDashboard from './components/UserDashboard';
import AdminPanel from './components/AdminPanel';
import QuizSetup from './components/QuizSetup';
import QuestionDisplay from './components/QuestionDisplay';
import QuizDetails from './components/QuizDetails';
import QuizHistory from './components/QuizHistory';
import UserProfile from './components/UserProfile';
import QuestionsLibrary from './components/QuestionsLibrary';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Navigate to="/login" />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />

                {/* Protected Routes */}
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

                <Route path="/admin" element={
                    <ProtectedRoute>
                        <AdminPanel />
                    </ProtectedRoute>
                } />

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
            </Routes>
        </BrowserRouter>
    );
}

export default App;