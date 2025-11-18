import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { requestPasswordReset, verifyResetCode, resetPasswordWithCode } from '../../services/api';

export default function ForgotPassword() {
    const [step, setStep] = useState(1);
    const [email, setEmail] = useState('');
    const [code, setCode] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleRequestCode = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');
        setLoading(true);

        try {
            await requestPasswordReset(email);
            setMessage('Kod resetowania wysłany na email! Sprawdź skrzynkę.');
            setTimeout(() => {
                setMessage('');
                setStep(2);
            }, 2000);
        } catch (err) {
            console.error('Request reset error:', err);
            setError('Nie udało się wysłać kodu. Spróbuj ponownie.');
        } finally {
            setLoading(false);
        }
    };

    const handleVerifyCode = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');
        setLoading(true);

        try {
            await verifyResetCode(email, code);
            setMessage('Kod zweryfikowany! Wprowadź nowe hasło.');
            setTimeout(() => {
                setMessage('');
                setStep(3);
            }, 1500);
        } catch (err) {
            console.error('Verify code error:', err);
            setError('Nieprawidłowy lub wygasły kod. Spróbuj ponownie.');
        } finally {
            setLoading(false);
        }
    };

    const handleResetPassword = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');

        if (newPassword !== confirmPassword) {
            setError('Hasła nie są identyczne');
            return;
        }

        if (newPassword.length < 8) {
            setError('Hasło musi mieć minimum 8 znaków');
            return;
        }

        setLoading(true);

        try {
            await resetPasswordWithCode(email, code, newPassword);
            setMessage('Hasło zresetowane pomyślnie! Przekierowanie do logowania...');
            setTimeout(() => navigate('/login'), 2000);
        } catch (err) {
            console.error('Reset password error:', err);
            setError(err.response?.data?.error || 'Nie udało się zresetować hasła. Spróbuj ponownie.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-600 p-4">
            <div className="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="text-6xl mb-4">
                        {step === 1 && '📧'}
                        {step === 2 && '🔢'}
                        {step === 3 && '🔐'}
                    </div>
                    <h1 className="text-3xl font-bold text-gray-800 mb-2">
                        Resetowanie hasła
                    </h1>
                    <p className="text-gray-600">
                        {step === 1 && 'Podaj email, aby otrzymać kod resetowania'}
                        {step === 2 && 'Wpisz 6-cyfrowy kod wysłany na email'}
                        {step === 3 && 'Wprowadź nowe hasło'}
                    </p>
                </div>

                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                        {error}
                    </div>
                )}

                {message && (
                    <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                        {message}
                    </div>
                )}

                {step === 1 && (
                    <form onSubmit={handleRequestCode}>
                        <div className="mb-6">
                            <label className="block text-gray-700 font-semibold mb-2">
                                Adres email
                            </label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                                placeholder="twoj@email.com"
                                required
                                disabled={loading}
                                autoFocus
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700 transition font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Wysyłanie kodu...' : 'Wyślij kod'}
                        </button>
                    </form>
                )}

                {step === 2 && (
                    <form onSubmit={handleVerifyCode}>
                        <div className="mb-6">
                            <label className="block text-gray-700 font-semibold mb-2 text-center">
                                Kod weryfikacyjny
                            </label>
                            <input
                                type="text"
                                value={code}
                                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                className="w-full px-4 py-4 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 text-center text-3xl tracking-widest font-bold"
                                placeholder="000000"
                                maxLength={6}
                                required
                                disabled={loading}
                                autoFocus
                            />
                            <p className="text-sm text-gray-500 mt-2 text-center">
                                Kod wysłany do: <strong>{email}</strong>
                            </p>
                        </div>

                        <button
                            type="submit"
                            disabled={loading || code.length !== 6}
                            className="w-full bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700 transition font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed mb-3"
                        >
                            {loading ? 'Weryfikacja...' : 'Zweryfikuj kod'}
                        </button>

                        <button
                            type="button"
                            onClick={() => {
                                setStep(1);
                                setCode('');
                                setError('');
                                setMessage('');
                            }}
                            className="w-full text-purple-600 hover:text-purple-700 font-semibold py-2"
                        >
                            ← Zmień email
                        </button>
                    </form>
                )}

                {step === 3 && (
                    <form onSubmit={handleResetPassword}>
                        <div className="mb-4">
                            <label className="block text-gray-700 font-semibold mb-2">
                                Nowe hasło
                            </label>
                            <input
                                type="password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                                placeholder="••••••••"
                                required
                                minLength={8}
                                disabled={loading}
                                autoFocus
                            />
                            <p className="text-sm text-gray-500 mt-1">Minimum 8 znaków</p>
                        </div>

                        <div className="mb-6">
                            <label className="block text-gray-700 font-semibold mb-2">
                                Potwierdź nowe hasło
                            </label>
                            <input
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
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
                            {loading ? 'Resetowanie hasła...' : 'Zresetuj hasło'}
                        </button>
                    </form>
                )}

                <div className="mt-6 text-center">
                    <Link to="/login" className="text-purple-600 hover:text-purple-700 font-semibold">
                        ← Powrót do logowania
                    </Link>
                </div>
            </div>
        </div>
    );
}