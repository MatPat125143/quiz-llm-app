import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { register, login } from '../../services/api';

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
            setTimeout(() => {
                navigate('/dashboard');
                window.location.reload();
            }, 2000);
        } catch (err) {
            console.error('Registration error:', err.response?.data);
            const errorData = err.response?.data;

            // Tłumaczenie błędów z backendu
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
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-500 to-blue-600">
                <div className="bg-white p-8 rounded-2xl shadow-2xl text-center">
                    <div className="text-6xl mb-4">✅</div>
                    <h2 className="text-3xl font-bold text-gray-800 mb-2">Witamy!</h2>
                    <p className="text-gray-600">Konto utworzone pomyślnie!</p>
                    <p className="text-gray-500 text-sm mt-2">Przekierowanie do panelu...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-600 p-4">
            <div className="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-md">
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold text-gray-800 mb-2">🎯 Utwórz konto</h1>
                    <p className="text-gray-600">Dołącz do nas i rozpocznij swoją przygodę!</p>
                </div>

                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label className="block text-gray-700 font-semibold mb-2">
                            Adres email *
                        </label>
                        <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                            placeholder="twoj@email.com"
                            required
                            disabled={loading}
                        />
                    </div>

                    <div className="mb-4">
                        <label className="block text-gray-700 font-semibold mb-2">
                            Nazwa użytkownika (opcjonalne)
                        </label>
                        <input
                            type="text"
                            name="username"
                            value={formData.username}
                            onChange={handleChange}
                            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                            placeholder="cooluser123"
                            disabled={loading}
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            Zostaw puste, aby użyć początku emaila jako nazwy użytkownika
                        </p>
                    </div>

                    <div className="mb-4">
                        <label className="block text-gray-700 font-semibold mb-2">
                            Twój poziom wiedzy *
                        </label>
                        <select
                            name="knowledgeLevel"
                            value={formData.knowledgeLevel}
                            onChange={handleChange}
                            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 bg-white"
                            disabled={loading}
                            required
                        >
                            <option value="elementary">🎒 Szkoła podstawowa</option>
                            <option value="high_school">🎓 Liceum</option>
                            <option value="university">🏛️ Studia</option>
                            <option value="expert">🔬 Ekspert</option>
                        </select>
                        <p className="text-xs text-gray-500 mt-1">
                            Pytania będą dostosowane do Twojego poziomu edukacji
                        </p>
                    </div>

                    <div className="mb-4">
                        <label className="block text-gray-700 font-semibold mb-2">
                            Hasło *
                        </label>
                        <input
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                            placeholder="••••••••"
                            required
                            minLength={8}
                            disabled={loading}
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            Minimum 8 znaków
                        </p>
                    </div>

                    <div className="mb-6">
                        <label className="block text-gray-700 font-semibold mb-2">
                            Potwierdź hasło *
                        </label>
                        <input
                            type="password"
                            name="confirmPassword"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                            placeholder="••••••••"
                            required
                            minLength={8}
                            disabled={loading}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700 transition font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Tworzenie konta...' : 'Zarejestruj się'}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <p className="text-gray-600">
                        Masz już konto?{' '}
                        <Link to="/login" className="text-purple-600 hover:text-purple-700 font-semibold">
                            Zaloguj się tutaj
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}