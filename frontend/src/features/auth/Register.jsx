import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { register, login } from '../../services/api';
import { KNOWLEDGE_LEVELS } from '../../services/constants';
import { useRef } from 'react';
import useThemeToggle from '../../hooks/useThemeToggle';

export default function Register() {
    const [formData, setFormData] = useState({
        email: '',
        username: '',
        password: '',
        confirmPassword: '',
        knowledgeLevel: 'high_school'
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const navigate = useNavigate();
    const { theme, toggleTheme } = useThemeToggle();
    const [isTinyMobile, setIsTinyMobile] = useState(
        typeof window !== 'undefined' ? window.innerWidth <= 767 : false
    );
    const redirectTimeoutRef = useRef(null);

    useEffect(() => {
        const onResize = () => setIsTinyMobile(window.innerWidth <= 767);
        window.addEventListener('resize', onResize);
        return () => window.removeEventListener('resize', onResize);
    }, []);

    useEffect(() => () => {
        if (redirectTimeoutRef.current) {
            clearTimeout(redirectTimeoutRef.current);
        }
    }, []);

    const getKnowledgeOptionLabel = (opt) => {
        if (!isTinyMobile) return `${opt.emoji} ${opt.label}`;
        const compactLabels = {
            elementary: '🏫 Podstawowa',
            high_school: '🎓 Liceum',
            university: '🏛️ Studia',
            expert: '⭐ Ekspert',
        };
        return compactLabels[opt.key] || `${opt.emoji} ${opt.label}`;
    };

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        if (formData.password !== formData.confirmPassword) {
            setError('Hasła nie są identyczne');
            setLoading(false);
            return;
        }

        if (formData.password.length < 8) {
            setError('Hasło musi mieć minimum 8 znaków');
            setLoading(false);
            return;
        }

        if (!formData.email.includes('@')) {
            setError('Proszę podać prawidłowy adres email');
            setLoading(false);
            return;
        }

        try {
            await register(formData.email, formData.username, formData.password, formData.knowledgeLevel);
            await login(formData.email, formData.password);
            setSuccess(true);
            redirectTimeoutRef.current = setTimeout(() => {
                navigate('/dashboard', { replace: true });
            }, 2000);
        } catch (err) {
            console.error('Registration error:', err.response?.data);
            const errorData = err.response?.data;

            
            if (errorData?.email) {
                const emailError = errorData.email[0];
                if (emailError.includes('already exists')) {
                    setError('Email: Użytkownik z tym adresem email już istnieje');
                } else if (emailError.includes('valid email')) {
                    setError('Email: Wprowadź prawidłowy adres email');
                } else {
                    setError(`Email: ${emailError}`);
                }
            } else if (errorData?.username) {
                const usernameError = errorData.username[0];
                if (usernameError.includes('already exists')) {
                    setError('Nazwa użytkownika: Użytkownik z tą nazwą już istnieje');
                } else if (usernameError.includes('valid username')) {
                    setError('Nazwa użytkownika: Wprowadź prawidłową nazwę użytkownika');
                } else {
                    setError(`Nazwa użytkownika: ${usernameError}`);
                }
            } else if (errorData?.password) {
                const passwordError = errorData.password[0];
                if (passwordError.includes('too short')) {
                    setError('Hasło: Hasło jest za krótkie (minimum 8 znaków)');
                } else if (passwordError.includes('too common')) {
                    setError('Hasło: Hasło jest zbyt popularne, wybierz inne');
                } else if (passwordError.includes('numeric')) {
                    setError('Hasło: Hasło nie może składać się tylko z cyfr');
                } else {
                    setError(`Hasło: ${passwordError}`);
                }
            } else if (errorData?.detail) {
                setError(errorData.detail);
            } else if (errorData?.non_field_errors) {
                setError(errorData.non_field_errors[0]);
            } else {
                setError('Rejestracja nie powiodła się. Spróbuj ponownie.');
            }
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="relative min-h-screen flex items-center justify-center bg-gradient-to-br from-green-500 to-blue-600 p-4 pt-16 sm:pt-4">
                <button
                type="button"
                onClick={toggleTheme}
                className="absolute top-4 right-4 h-10 w-10 rounded-xl bg-white/90 dark:bg-slate-900/90 border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors flex items-center justify-center"
                aria-label="Przełącz motyw"
                title="Przełącz motyw"
            >
                {theme === 'dark' ? '🌙' : '☀️'}
            </button>
            <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl shadow-2xl border border-gray-100 dark:border-slate-800 text-center">
                    <div className="text-6xl mb-4">✅</div>
                    <h2 className="text-3xl font-bold text-gray-800 dark:text-slate-100 mb-2">Witamy!</h2>
                    <p className="text-gray-600 dark:text-slate-300">Konto utworzone pomyślnie!</p>
                    <p className="text-gray-500 dark:text-slate-400 text-sm mt-2">Przekierowanie do panelu...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="relative min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-600 p-4 pt-16 sm:pt-4">
            <button
                type="button"
                onClick={toggleTheme}
                className="absolute top-4 right-4 h-10 w-10 rounded-xl bg-white/90 dark:bg-slate-900/90 border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors flex items-center justify-center"
                aria-label="Przełącz motyw"
                title="Przełącz motyw"
            >
                {theme === 'dark' ? '🌙' : '☀️'}
            </button>
            <div className="bg-white dark:bg-slate-900 p-5 sm:p-8 rounded-2xl shadow-2xl border border-gray-100 dark:border-slate-800 w-full max-w-md">
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold text-gray-800 dark:text-slate-100 mb-2">🎯 Utwórz konto</h1>
                    <p className="text-gray-600 dark:text-slate-300">Dołącz do nas i rozpocznij swoją przygodę!</p>
                </div>

                {error && (
                    <div className="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded mb-4">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label className="block text-gray-700 dark:text-slate-200 font-semibold mb-2">
                            Adres email *
                        </label>
                        <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            className="ui-input placeholder:text-gray-400 dark:placeholder:text-slate-400"
                            placeholder="twoj@email.com"
                            required
                            disabled={loading}
                        />
                    </div>

                    <div className="mb-4">
                        <label className="block text-gray-700 dark:text-slate-200 font-semibold mb-2">
                            Nazwa użytkownika (opcjonalne)
                        </label>
                        <input
                            type="text"
                            name="username"
                            value={formData.username}
                            onChange={handleChange}
                            className="ui-input placeholder:text-gray-400 dark:placeholder:text-slate-400"
                            placeholder="cooluser123"
                            disabled={loading}
                        />
                        <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">
                            Zostaw puste, aby użyć początku emaila jako nazwy użytkownika
                        </p>
                    </div>

                    <div className="mb-4">
                        <label className="block text-gray-700 dark:text-slate-200 font-semibold mb-2">
                            Twój poziom wiedzy *
                        </label>
                        <select
                            name="knowledgeLevel"
                            value={formData.knowledgeLevel}
                            onChange={handleChange}
                            className="ui-select w-full max-w-full !py-3 text-sm sm:text-base"
                            disabled={loading}
                            required
                        >
                            {KNOWLEDGE_LEVELS.map((opt) => (
                                <option key={opt.key} value={opt.key}>
                                    {getKnowledgeOptionLabel(opt)}
                                </option>
                            ))}
                        </select>
                        <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">
                            Pytania będą dostosowane do Twojego poziomu edukacji
                        </p>
                    </div>

                    <div className="mb-4">
                        <label className="block text-gray-700 dark:text-slate-200 font-semibold mb-2">
                            Hasło *
                        </label>
                        <input
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            className="ui-input placeholder:text-gray-400 dark:placeholder:text-slate-400"
                            placeholder="••••••••"
                            required
                            minLength={8}
                            disabled={loading}
                        />
                        <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">
                            Minimum 8 znaków
                        </p>
                    </div>

                    <div className="mb-6">
                        <label className="block text-gray-700 dark:text-slate-200 font-semibold mb-2">
                            Potwierdź hasło *
                        </label>
                        <input
                            type="password"
                            name="confirmPassword"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            className="ui-input placeholder:text-gray-400 dark:placeholder:text-slate-400"
                            placeholder="••••••••"
                            required
                            minLength={8}
                            disabled={loading}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-indigo-600 dark:bg-indigo-700 text-white py-3 rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Tworzenie konta...' : 'Zarejestruj się'}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <p className="text-gray-600 dark:text-slate-300">
                        Masz już konto?{' '}
                        <Link to="/login" className="text-indigo-600 dark:text-indigo-300 hover:text-indigo-700 dark:hover:text-indigo-200 font-semibold">
                            Zaloguj się tutaj
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}

