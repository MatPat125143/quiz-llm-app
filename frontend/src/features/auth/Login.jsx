import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { login } from '../../services/api';
import useThemeToggle from '../../hooks/useThemeToggle';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { theme, toggleTheme } = useThemeToggle();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await login(email, password);
            navigate('/dashboard', { replace: true });
        } catch (err) {
            console.error('Login error:', err);
            setError('Nieprawidłowy e-mail lub hasło');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="relative min-h-[125dvh] flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600 p-4 overflow-y-auto">
            <button
                type="button"
                onClick={toggleTheme}
                className="absolute top-4 right-4 h-10 w-10 rounded-xl bg-white/90 dark:bg-slate-900/90 border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors flex items-center justify-center"
                aria-label="Przełącz motyw"
                title="Przełącz motyw"
            >
                {theme === 'dark' ? '🌙' : '☀️'}
            </button>
            <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl shadow-2xl border border-gray-100 dark:border-slate-800 w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="text-6xl mb-4">🎮</div>
                    <h1 className="text-3xl font-bold text-gray-800 dark:text-slate-100 mb-2">
                        Witaj ponownie!
                    </h1>
                    <p className="text-gray-600 dark:text-slate-300">Zaloguj się, aby kontynuować</p>
                </div>

                {error && (
                    <div className="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded mb-4">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label className="block text-gray-700 dark:text-slate-200 font-semibold mb-2">
                            Adres e-mail
                        </label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="ui-input placeholder:text-gray-400 dark:placeholder:text-slate-400"
                            placeholder="twoj@email.com"
                            required
                            disabled={loading}
                        />
                    </div>

                    <div className="mb-6">
                        <label className="block text-gray-700 dark:text-slate-200 font-semibold mb-2">
                            Hasło
                        </label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="ui-input placeholder:text-gray-400 dark:placeholder:text-slate-400"
                            placeholder="••••••••"
                            required
                            disabled={loading}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-indigo-600 dark:bg-indigo-700 text-white py-3 rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Logowanie...' : 'Zaloguj się'}
                    </button>
                </form>

                <div className="mt-4 text-center">
                    <Link to="/forgot-password" className="text-indigo-600 dark:text-indigo-300 hover:text-indigo-700 dark:hover:text-indigo-200 font-semibold">
                        Zapomniałeś hasła?
                    </Link>
                </div>

                <div className="mt-6 text-center">
                    <p className="text-gray-600 dark:text-slate-300">
                        Nie masz konta?{' '}
                        <Link to="/register" className="text-indigo-600 dark:text-indigo-300 hover:text-indigo-700 dark:hover:text-indigo-200 font-semibold">
                            Zarejestruj się
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}

