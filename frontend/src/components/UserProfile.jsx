import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    getCurrentUser,
    updateProfile,
    changePassword,
    uploadAvatar,
    deleteAvatar,
    logout
} from '../services/api';

export default function UserProfile() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('profile');
    const [message, setMessage] = useState({ type: '', text: '' });
    const navigate = useNavigate();
    const fileInputRef = useRef(null);

    // Profile form
    const [profileData, setProfileData] = useState({
        email: '',
        username: ''
    });

    // Password form
    const [passwordData, setPasswordData] = useState({
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
    });

    useEffect(() => {
        loadUser();
    }, []);

    const loadUser = async () => {
        try {
            const data = await getCurrentUser();
            setUser(data);
            setProfileData({
                email: data.email,
                username: data.username
            });
        } catch (err) {
            console.error('Error loading user:', err);
            setMessage({ type: 'error', text: 'Nie udało się załadować danych użytkownika' });
        } finally {
            setLoading(false);
        }
    };

    const handleProfileUpdate = async (e) => {
        e.preventDefault();
        setMessage({ type: '', text: '' });

        try {
            const response = await updateProfile(profileData);
            setUser(response.user);
            setMessage({ type: 'success', text: 'Profil zaktualizowany pomyślnie!' });
        } catch (err) {
            console.error('Update error:', err);
            setMessage({
                type: 'error',
                text: err.response?.data?.email?.[0] || err.response?.data?.username?.[0] || 'Nie udało się zaktualizować profilu'
            });
        }
    };

    const handlePasswordChange = async (e) => {
        e.preventDefault();
        setMessage({ type: '', text: '' });

        if (passwordData.newPassword !== passwordData.confirmPassword) {
            setMessage({ type: 'error', text: 'Hasła nie są identyczne' });
            return;
        }

        if (passwordData.newPassword.length < 8) {
            setMessage({ type: 'error', text: 'Hasło musi mieć minimum 8 znaków' });
            return;
        }

        try {
            await changePassword(passwordData.oldPassword, passwordData.newPassword);
            setMessage({ type: 'success', text: 'Hasło zmienione pomyślnie!' });
            setPasswordData({ oldPassword: '', newPassword: '', confirmPassword: '' });
        } catch (err) {
            console.error('Password change error:', err);
            setMessage({
                type: 'error',
                text: err.response?.data?.old_password?.[0] || 'Nie udało się zmienić hasła'
            });
        }
    };

    const handleAvatarUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Validate file
        if (!file.type.startsWith('image/')) {
            setMessage({ type: 'error', text: 'Proszę wybrać plik obrazu' });
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            setMessage({ type: 'error', text: 'Obraz musi być mniejszy niż 5MB' });
            return;
        }

        try {
            await uploadAvatar(file);
            await loadUser();
            setMessage({ type: 'success', text: 'Avatar przesłany pomyślnie!' });
        } catch (err) {
            console.error('Avatar upload error:', err);
            setMessage({ type: 'error', text: 'Nie udało się przesłać avatara' });
        }
    };

    const handleAvatarDelete = async () => {
        if (!confirm('Czy na pewno chcesz usunąć swój avatar?')) return;

        try {
            await deleteAvatar();
            await loadUser();
            setMessage({ type: 'success', text: 'Avatar usunięty pomyślnie!' });
        } catch (err) {
            console.error('Avatar delete error:', err);
            setMessage({ type: 'error', text: 'Nie udało się usunąć avatara' });
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100">
                <div className="text-2xl font-semibold text-gray-600">Ładowanie...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-100">
            {/* Header */}
            <header className="bg-white shadow-md">
                <div className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
                    <h1 className="text-3xl font-bold text-blue-600">👤 Profil użytkownika</h1>
                    <div className="flex items-center gap-4">
                        {/* Avatar i nazwa użytkownika */}
                        <div className="flex items-center gap-3">
                            {user?.profile?.avatar_url ? (
                                <img
                                    src={user.profile.avatar_url}
                                    alt="Avatar"
                                    className="w-10 h-10 rounded-full object-cover border-2 border-blue-500"
                                />
                            ) : (
                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center border-2 border-blue-500">
                                    <span className="text-white font-bold text-lg">
                                        {user?.email?.[0]?.toUpperCase() || '?'}
                                    </span>
                                </div>
                            )}
                            <span className="font-semibold text-gray-800">{user?.username}</span>
                        </div>

                        {/* Dashboard button */}
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition font-semibold"
                        >
                            ← Panel główny
                        </button>

                        {/* Admin button */}
                        {user?.profile?.role === 'admin' && (
                            <button
                                onClick={() => navigate('/admin')}
                                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition font-semibold"
                            >
                                👑 Panel admina
                            </button>
                        )}

                        {/* Logout button */}
                        <button
                            onClick={handleLogout}
                            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition font-semibold"
                        >
                            Wyloguj
                        </button>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-4 py-8">
                {/* Message */}
                {message.text && (
                    <div className={`mb-6 px-4 py-3 rounded-lg ${
                        message.type === 'success' 
                            ? 'bg-green-100 border border-green-400 text-green-700'
                            : 'bg-red-100 border border-red-400 text-red-700'
                    }`}>
                        {message.text}
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {/* Sidebar */}
                    <div className="md:col-span-1">
                        <div className="bg-white rounded-xl shadow-lg p-6">
                            {/* Avatar */}
                            <div className="text-center mb-6">
                                <div className="relative inline-block">
                                    {user?.profile?.avatar_url ? (
                                        <img
                                            src={user.profile.avatar_url}
                                            alt="Avatar"
                                            className="w-32 h-32 rounded-full object-cover border-4 border-blue-500"
                                        />
                                    ) : (
                                        <div className="w-32 h-32 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center border-4 border-blue-500">
                                            <span className="text-5xl text-white font-bold">
                                                {user?.email?.[0]?.toUpperCase() || '?'}
                                            </span>
                                        </div>
                                    )}
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        className="absolute bottom-0 right-0 bg-blue-600 text-white p-2 rounded-full hover:bg-blue-700 transition"
                                        title="Zmień avatar"
                                    >
                                        📷
                                    </button>
                                    <input
                                        ref={fileInputRef}
                                        type="file"
                                        accept="image/*"
                                        onChange={handleAvatarUpload}
                                        className="hidden"
                                    />
                                </div>
                                {user?.profile?.avatar_url && (
                                    <button
                                        onClick={handleAvatarDelete}
                                        className="mt-2 text-sm text-red-600 hover:text-red-700"
                                    >
                                        Usuń avatar
                                    </button>
                                )}
                            </div>

                            {/* User Info */}
                            <div className="text-center mb-6">
                                <h2 className="text-2xl font-bold text-gray-800">{user?.username}</h2>
                                <p className="text-gray-600">{user?.email}</p>
                                {user?.profile?.role === 'admin' && (
                                    <span className="inline-block mt-2 px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-semibold">
                                        👑 ADMIN
                                    </span>
                                )}
                            </div>

                            {/* Stats */}
                            <div className="space-y-3">
                                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                                    <span className="text-gray-600">Rozegrane quizy</span>
                                    <span className="font-bold text-blue-600">{user?.profile?.total_quizzes_played || 0}</span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                                    <span className="text-gray-600">Odpowiedzi</span>
                                    <span className="font-bold text-green-600">{user?.profile?.total_questions_answered || 0}</span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                                    <span className="text-gray-600">Dokładność</span>
                                    <span className="font-bold text-purple-600">{user?.profile?.accuracy || 0}%</span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                                    <span className="text-gray-600">Najwyższa passa</span>
                                    <span className="font-bold text-orange-600">{user?.profile?.highest_streak || 0} 🔥</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Main Content */}
                    <div className="md:col-span-2">
                        {/* Tabs */}
                        <div className="bg-white rounded-xl shadow-lg p-6">
                            <div className="flex border-b mb-6">
                                <button
                                    onClick={() => setActiveTab('profile')}
                                    className={`px-6 py-3 font-semibold transition ${
                                        activeTab === 'profile'
                                            ? 'border-b-2 border-blue-600 text-blue-600'
                                            : 'text-gray-600 hover:text-blue-600'
                                    }`}
                                >
                                    📝 Edytuj profil
                                </button>
                                <button
                                    onClick={() => setActiveTab('password')}
                                    className={`px-6 py-3 font-semibold transition ${
                                        activeTab === 'password'
                                            ? 'border-b-2 border-blue-600 text-blue-600'
                                            : 'text-gray-600 hover:text-blue-600'
                                    }`}
                                >
                                    🔒 Zmień hasło
                                </button>
                            </div>

                            {/* Profile Tab */}
                            {activeTab === 'profile' && (
                                <form onSubmit={handleProfileUpdate}>
                                    <div className="mb-6">
                                        <label className="block text-gray-700 font-semibold mb-2">
                                            Adres email
                                        </label>
                                        <input
                                            type="email"
                                            value={profileData.email}
                                            onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                                            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                                            required
                                        />
                                    </div>

                                    <div className="mb-6">
                                        <label className="block text-gray-700 font-semibold mb-2">
                                            Nazwa użytkownika
                                        </label>
                                        <input
                                            type="text"
                                            value={profileData.username}
                                            onChange={(e) => setProfileData({ ...profileData, username: e.target.value })}
                                            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                                            required
                                        />
                                    </div>

                                    <button
                                        type="submit"
                                        className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition font-semibold text-lg"
                                    >
                                        Zapisz zmiany
                                    </button>
                                </form>
                            )}

                            {/* Password Tab */}
                            {activeTab === 'password' && (
                                <form onSubmit={handlePasswordChange}>
                                    <div className="mb-4">
                                        <label className="block text-gray-700 font-semibold mb-2">
                                            Obecne hasło
                                        </label>
                                        <input
                                            type="password"
                                            value={passwordData.oldPassword}
                                            onChange={(e) => setPasswordData({ ...passwordData, oldPassword: e.target.value })}
                                            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                                            required
                                        />
                                    </div>

                                    {/* FORGOT PASSWORD LINK */}
                                    <div className="mb-6 text-right">
                                        <button
                                            type="button"
                                            onClick={() => navigate('/forgot-password')}
                                            className="text-blue-600 hover:text-blue-700 text-sm font-semibold"
                                        >
                                            Zapomniałeś obecnego hasła?
                                        </button>
                                    </div>

                                    <div className="mb-6">
                                        <label className="block text-gray-700 font-semibold mb-2">
                                            Nowe hasło
                                        </label>
                                        <input
                                            type="password"
                                            value={passwordData.newPassword}
                                            onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                                            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                                            required
                                            minLength={8}
                                        />
                                        <p className="text-sm text-gray-500 mt-1">Minimum 8 znaków</p>
                                    </div>

                                    <div className="mb-6">
                                        <label className="block text-gray-700 font-semibold mb-2">
                                            Potwierdź nowe hasło
                                        </label>
                                        <input
                                            type="password"
                                            value={passwordData.confirmPassword}
                                            onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                                            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                                            required
                                            minLength={8}
                                        />
                                    </div>

                                    <button
                                        type="submit"
                                        className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition font-semibold text-lg"
                                    >
                                        Zmień hasło
                                    </button>
                                </form>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}