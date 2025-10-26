import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    getAdminDashboard,
    getAllUsers,
    deleteUser,
    changeUserRole,
    toggleUserStatus,
    logout
} from '../services/api';

export default function AdminPanel() {
    const [stats, setStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        loadAdminData();
    }, []);

    const loadAdminData = async () => {
        try {
            const [statsData, usersData] = await Promise.all([
                getAdminDashboard(),
                getAllUsers()
            ]);
            setStats(statsData);
            setUsers(usersData);
        } catch (err) {
            console.error('Error loading admin data:', err);
            if (err.response?.status === 403) {
                alert('Brak uprawnień administratora');
                navigate('/dashboard');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteUser = async (userId, email) => {
        if (!confirm(`Czy na pewno chcesz usunąć użytkownika ${email}?`)) return;

        try {
            await deleteUser(userId);
            await loadAdminData();
            alert('Użytkownik usunięty pomyślnie');
        } catch (err) {
            console.error('Delete error:', err);
            alert('Nie udało się usunąć użytkownika');
        }
    };

    const handleChangeRole = async (userId, currentRole) => {
        const newRole = currentRole === 'admin' ? 'user' : 'admin';
        if (!confirm(`Zmienić rolę użytkownika na ${newRole === 'admin' ? 'ADMIN' : 'USER'}?`)) return;

        try {
            await changeUserRole(userId, newRole);
            await loadAdminData();
            alert('Rola zmieniona pomyślnie');
        } catch (err) {
            console.error('Role change error:', err);
            alert('Nie udało się zmienić roli');
        }
    };

    const handleToggleStatus = async (userId, isActive) => {
        const action = isActive ? 'dezaktywować' : 'aktywować';
        if (!confirm(`Czy na pewno chcesz ${action} tego użytkownika?`)) return;

        try {
            await toggleUserStatus(userId);
            await loadAdminData();
            alert(`Użytkownik ${isActive ? 'dezaktywowany' : 'aktywowany'} pomyślnie`);
        } catch (err) {
            console.error('Toggle status error:', err);
            alert('Nie udało się zmienić statusu');
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
            <header className="bg-gradient-to-r from-purple-600 to-pink-600 shadow-lg">
                <div className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
                    <div>
                        <h1 className="text-4xl font-bold text-white">👑 Panel administratora</h1>
                        <p className="text-purple-100 mt-1">Zarządzanie systemem quizowym</p>
                    </div>
                    <div className="flex gap-4">
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="bg-white text-purple-600 px-6 py-2 rounded-lg hover:bg-purple-50 transition font-semibold"
                        >
                            ← Panel główny
                        </button>
                        <button
                            onClick={handleLogout}
                            className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition font-semibold"
                        >
                            Wyloguj
                        </button>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-4 py-8">
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-600 text-sm font-semibold">Wszyscy użytkownicy</p>
                                <p className="text-4xl font-bold text-blue-600 mt-2">
                                    {stats?.total_users || 0}
                                </p>
                            </div>
                            <div className="text-5xl">👥</div>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-600 text-sm font-semibold">Aktywni użytkownicy</p>
                                <p className="text-4xl font-bold text-green-600 mt-2">
                                    {stats?.active_users || 0}
                                </p>
                            </div>
                            <div className="text-5xl">✅</div>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-600 text-sm font-semibold">Wszystkie quizy</p>
                                <p className="text-4xl font-bold text-purple-600 mt-2">
                                    {stats?.total_quizzes || 0}
                                </p>
                            </div>
                            <div className="text-5xl">📝</div>
                        </div>
                    </div>
                </div>

                {/* Users Table */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                    <h2 className="text-2xl font-bold text-gray-800 mb-6">Zarządzanie użytkownikami</h2>

                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b-2 border-gray-200">
                                    <th className="text-left py-3 px-4 font-semibold text-gray-700">ID</th>
                                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Email</th>
                                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Nazwa użytkownika</th>
                                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Rola</th>
                                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Quizy</th>
                                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Akcje</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users.map((user) => (
                                    <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50">
                                        <td className="py-4 px-4">{user.id}</td>
                                        <td className="py-4 px-4">{user.email}</td>
                                        <td className="py-4 px-4 font-semibold">{user.username}</td>
                                        <td className="py-4 px-4">
                                            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                                                user.profile?.role === 'admin'
                                                    ? 'bg-purple-100 text-purple-800'
                                                    : 'bg-blue-100 text-blue-800'
                                            }`}>
                                                {user.profile?.role === 'admin' ? '👑 ADMIN' : '👤 USER'}
                                            </span>
                                        </td>
                                        <td className="py-4 px-4">
                                            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                                                user.is_active
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-red-100 text-red-800'
                                            }`}>
                                                {user.is_active ? '✅ Aktywny' : '❌ Nieaktywny'}
                                            </span>
                                        </td>
                                        <td className="py-4 px-4 text-center">
                                            {user.profile?.total_quizzes_played || 0}
                                        </td>
                                        <td className="py-4 px-4">
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={() => handleChangeRole(user.id, user.profile?.role)}
                                                    className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600 transition text-sm font-semibold"
                                                    title="Zmień rolę"
                                                >
                                                    🔄
                                                </button>
                                                <button
                                                    onClick={() => handleToggleStatus(user.id, user.is_active)}
                                                    className="bg-yellow-500 text-white px-3 py-1 rounded hover:bg-yellow-600 transition text-sm font-semibold"
                                                    title={user.is_active ? 'Dezaktywuj' : 'Aktywuj'}
                                                >
                                                    {user.is_active ? '🔒' : '🔓'}
                                                </button>
                                                <button
                                                    onClick={() => handleDeleteUser(user.id, user.email)}
                                                    className="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600 transition text-sm font-semibold"
                                                    title="Usuń użytkownika"
                                                >
                                                    🗑️
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {users.length === 0 && (
                        <div className="text-center py-12">
                            <p className="text-xl text-gray-600">Brak użytkowników</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}