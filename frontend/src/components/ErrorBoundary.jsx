import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleGoToHome = () => {
    this.setState({ hasError: false, error: null }, () => {
      window.location.assign('/dashboard');
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-950 px-4">
          <div className="max-w-md w-full text-center">
            <div className="mb-8">
              <div className="text-6xl mb-4">💥</div>
              <h2 className="text-3xl font-semibold text-gray-900 dark:text-slate-100 mb-4">
                Coś poszło nie tak
              </h2>
              <p className="text-gray-600 dark:text-slate-300 mb-4">
                Wystąpił nieoczekiwany błąd. Odśwież stronę lub wróć do strony głównej.
              </p>
            </div>

            <div className="space-y-4">
              <button
                onClick={() => window.location.reload()}
                className="block w-full bg-indigo-600 dark:bg-indigo-700 text-white py-3 px-4 rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors"
              >
                Odśwież stronę
              </button>
              <button
                onClick={this.handleGoToHome}
                className="block w-full bg-gray-200 dark:bg-slate-800 text-gray-700 dark:text-slate-200 py-3 px-4 rounded-lg hover:bg-gray-300 dark:hover:bg-slate-700 border border-gray-300 dark:border-slate-700 transition-colors"
              >
                Wróć do strony głównej
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
