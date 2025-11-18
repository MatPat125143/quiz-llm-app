import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { logout } from '../services/api';

export default function MainLayout({ children, user }) {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const isAdmin = user?.profile?.role === 'admin';

    const userMenuItems = [
        { icon: '🏠', label: 'Panel Główny', path: '/dashboard' },
        { icon: '🚀', label: 'Rozpocznij Quiz', path: '/quiz/setup' },
        { icon: '📚', label: 'Biblioteka Pytań', path: '/quiz/questions' },
        { icon: '📖', label: 'Historia Quizów', path: '/quiz/history' },
        { icon: '👤', label: 'Profil', path: '/profile' },
    ];

    const adminMenuItems = [
        ...userMenuItems,
        { icon: '👑', label: 'Panel Admina', path: '/admin', divider: true },
    ];

    const menuItems = isAdmin ? adminMenuItems : userMenuItems;

    return (
        <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
            {/* Navbar */}
            <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
                    <div className="flex justify-between items-center">
                        {/* Logo + Hamburger */}
                        <div className="flex items-center gap-4">
                            {/* Hamburger Button */}
                            <button
                                onClick={() => setSidebarOpen(!sidebarOpen)}
                                className="p-2 rounded-xl hover:bg-gray-100 transition-colors lg:hidden"
                                aria-label="Toggle menu"
                            >
                                <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                </svg>
                            </button>

                            {/* Logo */}
                            <div
                                className="flex items-center gap-3 cursor-pointer"
                                onClick={() => navigate('/dashboard')}
                            >
                                <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                                    <span className="text-xl">🎯</span>
                                </div>
                                <div className="hidden sm:block">
                                    <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                                        Quiz LLM
                                    </h1>
                                </div>
                            </div>
                        </div>

                        {/* Desktop Navigation */}
                        <nav className="hidden lg:flex items-center gap-2">
                            <button
                                onClick={() => navigate('/dashboard')}
                                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-xl transition-colors font-medium"
                            >
                                🏠 Dashboard
                            </button>
                            <button
                                onClick={() => navigate('/quiz/setup')}
                                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-xl transition-colors font-medium"
                            >
                                🚀 Nowy Quiz
                            </button>
                            <button
                                onClick={() => navigate('/quiz/questions')}
                                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-xl transition-colors font-medium"
                            >
                                📚 Biblioteka
                            </button>
                            <button
                                onClick={() => navigate('/quiz/history')}
                                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-xl transition-colors font-medium"
                            >
                                📖 Historia
                            </button>
                            {isAdmin && (
                                <button
                                    onClick={() => navigate('/admin')}
                                    className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all shadow-md font-medium"
                                >
                                    👑 Admin
                                </button>
                            )}
                        </nav>

                        {/* User Profile + Logout */}
                        <div className="flex items-center gap-3">
                            <div
                                className="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-gray-100 cursor-pointer transition-all"
                                onClick={() => navigate('/profile')}
                            >
                                {user?.profile?.avatar_url ? (
                                    <img
                                        src={user.profile.avatar_url}
                                        alt="Avatar"
                                        className="w-8 h-8 sm:w-10 sm:h-10 rounded-full object-cover border-2 border-indigo-300 shadow-sm"
                                    />
                                ) : (
                                    <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center shadow-sm">
                                        <span className="text-white font-bold text-sm">
                                            {user?.email?.[0]?.toUpperCase() || '?'}
                                        </span>
                                    </div>
                                )}
                                <span className="font-semibold text-gray-700 hidden md:block text-sm">
                                    {user?.username}
                                </span>
                            </div>

                            <button
                                onClick={handleLogout}
                                className="hidden sm:block px-4 py-2 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-all font-medium text-sm"
                            >
                                Wyloguj
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Mobile Sidebar */}
            <div
                className={`fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden transition-opacity ${
                    sidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
                }`}
                onClick={() => setSidebarOpen(false)}
            />

            <aside
                className={`fixed top-0 left-0 h-full w-80 bg-white shadow-2xl z-50 transform transition-transform lg:hidden ${
                    sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                }`}
            >
                <div className="p-6">
                    {/* Sidebar Header */}
                    <div className="flex items-center justify-between mb-8">
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                                <span className="text-2xl">🎯</span>
                            </div>
                            <div>
                                <h2 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                                    Menu
                                </h2>
                            </div>
                        </div>
                        <button
                            onClick={() => setSidebarOpen(false)}
                            className="p-2 rounded-xl hover:bg-gray-100 transition-colors"
                        >
                            <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    {/* User Info */}
                    <div className="mb-6 p-4 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl border border-indigo-100">
                        <div className="flex items-center gap-3">
                            {user?.profile?.avatar_url ? (
                                <img
                                    src={user.profile.avatar_url}
                                    alt="Avatar"
                                    className="w-12 h-12 rounded-full object-cover border-2 border-indigo-300 shadow-sm"
                                />
                            ) : (
                                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center shadow-sm">
                                    <span className="text-white font-bold text-lg">
                                        {user?.email?.[0]?.toUpperCase() || '?'}
                                    </span>
                                </div>
                            )}
                            <div>
                                <p className="font-bold text-gray-800">{user?.username}</p>
                                <p className="text-sm text-gray-600">{user?.email}</p>
                                {isAdmin && (
                                    <span className="inline-block mt-1 px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold">
                                        👑 Administrator
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Navigation Menu */}
                    <nav className="space-y-2">
                        {menuItems.map((item, index) => (
                            <div key={index}>
                                {item.divider && <div className="my-4 border-t-2 border-gray-200" />}
                                <button
                                    onClick={() => {
                                        navigate(item.path);
                                        setSidebarOpen(false);
                                    }}
                                    className="w-full flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-gradient-to-r hover:from-indigo-50 hover:to-purple-50 rounded-xl transition-all font-medium group"
                                >
                                    <span className="text-2xl group-hover:scale-110 transition-transform">
                                        {item.icon}
                                    </span>
                                    <span className="group-hover:text-indigo-600 transition-colors">
                                        {item.label}
                                    </span>
                                </button>
                            </div>
                        ))}

                        {/* Logout Button in Sidebar */}
                        <div className="pt-4 mt-4 border-t-2 border-gray-200">
                            <button
                                onClick={() => {
                                    handleLogout();
                                    setSidebarOpen(false);
                                }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-xl transition-all font-medium group"
                            >
                                <span className="text-2xl group-hover:scale-110 transition-transform">
                                    🚪
                                </span>
                                <span>Wyloguj się</span>
                            </button>
                        </div>
                    </nav>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1">
                {children}
            </main>

            {/* Footer */}
            <footer className="bg-white border-t border-gray-200 mt-auto">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {/* About Section */}
                        <div>
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                                    <span className="text-xl">🎯</span>
                                </div>
                                <h3 className="text-lg font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                                    Quiz LLM
                                </h3>
                            </div>
                            <p className="text-gray-600 text-sm">
                                Inteligentny system quizowy z adaptacyjnym poziomem trudności oparty na zaawansowanych modelach językowych.
                            </p>
                        </div>

                        {/* Quick Links */}
                        <div>
                            <h3 className="font-bold text-gray-800 mb-4">Szybkie linki</h3>
                            <ul className="space-y-2">
                                <li>
                                    <button
                                        onClick={() => navigate('/dashboard')}
                                        className="text-gray-600 hover:text-indigo-600 transition-colors text-sm"
                                    >
                                        Panel Główny
                                    </button>
                                </li>
                                <li>
                                    <button
                                        onClick={() => navigate('/quiz/setup')}
                                        className="text-gray-600 hover:text-indigo-600 transition-colors text-sm"
                                    >
                                        Rozpocznij Quiz
                                    </button>
                                </li>
                                <li>
                                    <button
                                        onClick={() => navigate('/quiz/questions')}
                                        className="text-gray-600 hover:text-indigo-600 transition-colors text-sm"
                                    >
                                        Biblioteka Pytań
                                    </button>
                                </li>
                                <li>
                                    <button
                                        onClick={() => navigate('/quiz/history')}
                                        className="text-gray-600 hover:text-indigo-600 transition-colors text-sm"
                                    >
                                        Historia Quizów
                                    </button>
                                </li>
                            </ul>
                        </div>

                        {/* Contact/Info */}
                        <div>
                            <h3 className="font-bold text-gray-800 mb-4">Informacje</h3>
                            <ul className="space-y-2 text-sm text-gray-600">
                                <li className="flex items-center gap-2">
                                    <span>🤖</span>
                                    <span>Powered by AI (LLM)</span>
                                </li>
                                <li className="flex items-center gap-2">
                                    <span>📊</span>
                                    <span>Adaptacyjny poziom trudności</span>
                                </li>
                                <li className="flex items-center gap-2">
                                    <span>🎓</span>
                                    <span>Edukacja i nauka</span>
                                </li>
                                <li className="flex items-center gap-2">
                                    <span>⚡</span>
                                    <span>Szybkie generowanie pytań</span>
                                </li>
                            </ul>
                        </div>
                    </div>

                    {/* Bottom Footer */}
                    <div className="mt-8 pt-8 border-t border-gray-200">
                        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                            <p className="text-gray-600 text-sm text-center md:text-left">
                                © 2025 Quiz LLM. Wszelkie prawa zastrzeżone.
                            </p>
                            <div className="flex items-center gap-4">
                                <span className="text-sm text-gray-600">
                                    Wykonano z ❤️ przy użyciu React & Django
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
}