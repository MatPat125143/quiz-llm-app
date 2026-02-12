import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { requestPasswordReset, verifyResetCode, resetPasswordWithCode } from '../../services/api';
import { useEffect, useRef } from 'react';

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
    const timeoutsRef = useRef([]);

    useEffect(() => () => {
        timeoutsRef.current.forEach((timeoutId) => clearTimeout(timeoutId));
        timeoutsRef.current = [];
    }, []);

    const scheduleTimeout = (callback, delayMs) => {
        const timeoutId = setTimeout(callback, delayMs);
        timeoutsRef.current.push(timeoutId);
    };

    const handleRequestCode = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');
        setLoading(true);

        try {
            await requestPasswordReset(email);
            setMessage('Kod resetowania wysłany na email! Sprawdź skrzynkę.');
            scheduleTimeout(() => {
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
            scheduleTimeout(() => {
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
            scheduleTimeout(() => navigate('/login', { replace: true }), 2000);
        } catch (err) {
            console.error('Reset password error:', err);
            setError(err.response?.data?.error || 'Nie udało się zresetować hasła. Spróbuj ponownie.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-600 p-4">
            <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl shadow-2xl border border-gray-100 dark:border-slate-800 w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="text-6xl mb-4">
                        {step === 1 && '📧'}
                        {step === 2 && '🔢'}
                        {step === 3 && '🔐'}
                    </div>
                    <h1 className="text-3xl font-bold text-gray-800 dark:text-slate-100 mb-2">
                        Resetowanie hasła
                    </h1>
                    <p className="text-gray-600 dark:text-slate-300">
                        {step === 1 && 'Podaj email, aby otrzymać kod resetowania'}
                        {step === 2 && 'Wpisz 6-cyfrowy kod wysłany na email'}
                        {step === 3 && 'Wprowadź nowe hasło'}
                    </p>
                </div>

                {error && (
                    <div className="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded mb-4">
                        {error}
                    </div>
                )}

                {message && (
                    <div className="bg-green-100 dark:bg-green-900/30 border border-green-400 dark:border-green-700 text-green-700 dark:text-green-200 px-4 py-3 rounded mb-4">
                        {message}
                    </div>
                )}

                {step === 1 && (
                    <form onSubmit={handleRequestCode}>
                        <div className="mb-6">
                            <label className="block text-gray-700 dark:text-slate-200 font-semibold mb-2">
                                Adres email
                            </label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="ui-input placeholder:text-gray-400 dark:placeholder:text-slate-400"
                                placeholder="twoj@email.com"
                                required
                                disabled={loading}
                                autoFocus
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-indigo-600 dark:bg-indigo-700 text-white py-3 rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Wysyłanie kodu...' : 'Wyślij kod'}
                        </button>
                    </form>
                )}

                {step === 2 && (
                    <form onSubmit={handleVerifyCode}>
                        <div className="mb-6">
                            <label className="block text-gray-700 dark:text-slate-200 font-semibold mb-2 text-center">
                                Kod weryfikacyjny
                            </label>
                            <input
                                type="text"
                                value={code}
                                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                className="ui-input py-4 text-center text-3xl tracking-widest font-bold placeholder:text-gray-400 dark:placeholder:text-slate-400"
                                placeholder="000000"
                                maxLength={6}
                                required
                                disabled={loading}
                                autoFocus
                            />
                            <p className="text-sm text-gray-500 dark:text-slate-400 mt-2 text-center">
                                Kod wysłany do: <strong className="text-gray-700 dark:text-slate-200">{email}</strong>
                            </p>
                        </div>

                        <button
                            type="submit"
                            disabled={loading || code.length !== 6}
                            className="w-full bg-indigo-600 dark:bg-indigo-700 text-white py-3 rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed mb-3"
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
                            className="w-full text-indigo-600 dark:text-indigo-300 hover:text-indigo-700 dark:hover:text-indigo-200 font-semibold py-2"
                        >
                            ← Zmień email
                        </button>
                    </form>
                )}

                {step === 3 && (
                    <form onSubmit={handleResetPassword}>
                        <div className="mb-4">
                            <label className="block text-gray-700 dark:text-slate-200 font-semibold mb-2">
                                Nowe hasło
                            </label>
                            <input
                                type="password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                className="ui-input placeholder:text-gray-400 dark:placeholder:text-slate-400"
                                placeholder="••••••••"
                                required
                                minLength={8}
                                disabled={loading}
                                autoFocus
                            />
                            <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">Minimum 8 znaków</p>
                        </div>

                        <div className="mb-6">
                            <label className="block text-gray-700 dark:text-slate-200 font-semibold mb-2">
                                Potwierdź nowe hasło
                            </label>
                            <input
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
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
                            {loading ? 'Resetowanie hasła...' : 'Zresetuj hasło'}
                        </button>
                    </form>
                )}

                <div className="mt-6 text-center">
                    <Link to="/login" className="text-indigo-600 dark:text-indigo-300 hover:text-indigo-700 dark:hover:text-indigo-200 font-semibold">
                        ← Powrót do logowania
                    </Link>
                </div>
            </div>
        </div>
    );
}

