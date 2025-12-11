import { Link, useNavigate } from 'react-router-dom';

export default function Forbidden() {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
            <div className="max-w-md w-full text-center">
                <div className="mb-8">
                    <h1 className="text-9xl font-bold text-red-600">403</h1>
                    <div className="text-6xl mb-4">🚫</div>
                    <h2 className="text-3xl font-semibold text-gray-900 mb-4">
                        Access Denied
                    </h2>
                    <p className="text-gray-600 mb-8">
                        You don't have permission to access this page.
                    </p>
                </div>

                <div className="space-y-4">
                    <button
                        onClick={() => navigate(-1)}
                        className="block w-full bg-indigo-600 text-white py-3 px-4 rounded-lg hover:bg-indigo-700 transition-colors"
                    >
                        Go Back
                    </button>
                    <Link
                        to="/dashboard"
                        className="block w-full bg-gray-200 text-gray-700 py-3 px-4 rounded-lg hover:bg-gray-300 transition-colors"
                    >
                        Go to Dashboard
                    </Link>
                </div>
            </div>
        </div>
    );
}
