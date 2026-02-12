import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { logout } from '../services/api';
import useThemeToggle from '../hooks/useThemeToggle';

export default function MainLayout({ children, user, hideChrome = false }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { theme, toggleTheme } = useThemeToggle();
  const [showScrollTop, setShowScrollTop] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  useEffect(() => {
    const onScroll = () => setShowScrollTop(window.scrollY > 360);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const isAdmin = user?.profile?.role === 'admin';

  const userMenuItems = [
    { icon: '🚀', label: 'Rozpocznij Quiz', path: '/quiz/setup' },
    { icon: '📚', label: 'Biblioteka Pytań', path: '/quiz/questions' },
    { icon: '📖', label: 'Historia Quizów', path: '/quiz/history' },
    { icon: '🏆', label: 'Ranking', path: '/leaderboard' }
  ];

  const adminMenuItems = [
    ...userMenuItems,
    { icon: '🛠️', label: 'Panel Admina', path: '/admin', divider: true }
  ];

  const menuItems = isAdmin ? adminMenuItems : userMenuItems;

  const isRouteActive = (path) => {
    const pathname = location.pathname;
    if (path === '/quiz/history' && pathname.startsWith('/quiz/details')) return true;
    if (path === '/quiz/setup' && pathname.startsWith('/quiz/play')) return true;
    return pathname === path;
  };

  const navButtonClass = (path) =>
    `px-4 py-2 rounded-xl transition-colors font-medium ${
      isRouteActive(path)
        ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-200'
        : 'text-gray-700 dark:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-800'
    }`;

  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg-app)] app-scope">
      {!hideChrome && (
        <header className="bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800 shadow-sm sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors lg:hidden"
                  aria-label="Toggle menu"
                >
                  <svg className="w-6 h-6 text-gray-700 dark:text-slate-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </button>

                
                <div
                  className="p-3 flex items-center gap-3 cursor-pointer transition transform hover:scale-105 hover:shadow-lg rounded-xl py-1 hover:bg-gray-100 dark:hover:bg-slate-800"
                  onClick={() => navigate('/dashboard')}
                >
                  <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                    <span className="text-2xl">🎯</span>
                  </div>
                  <div className="hidden sm:block leading-tight">
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                      Quiz LLM
                    </h1>
                  </div>
                </div>
              </div>

              
              <nav className="hidden lg:flex items-center gap-2">
                <button
                  onClick={() => navigate('/quiz/setup')}
                  className={navButtonClass('/quiz/setup')}
                >
                  🚀 Nowy Quiz
                </button>
                <button
                  onClick={() => navigate('/quiz/questions')}
                  className={navButtonClass('/quiz/questions')}
                >
                  📚 Biblioteka
                </button>
                <button
                  onClick={() => navigate('/quiz/history')}
                  className={navButtonClass('/quiz/history')}
                >
                  📖 Historia
                </button>
                <button
                  onClick={() => navigate('/leaderboard')}
                  className={navButtonClass('/leaderboard')}
                >
                  🏆 Ranking
                </button>
                {isAdmin && (
                  <button
                    onClick={() => navigate('/admin')}
                    className={`px-4 py-2 rounded-xl transition-colors font-medium ${
                      isRouteActive('/admin')
                        ? 'bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-200'
                        : 'text-gray-700 dark:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-800'
                    }`}
                  >
                    🛠️ Admin
                  </button>
                )}
              </nav>

              
              <div className="flex items-center gap-3">
                <button
                  onClick={toggleTheme}
                  className="p-2 rounded-xl bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-slate-200 hover:bg-gray-200 dark:hover:bg-slate-700 transition-colors"
                  aria-label="Przełącz motyw"
                  title="Przełącz motyw"
                >
                  {theme === 'dark' ? '🌙' : '☀️'}
                </button>
                <div
                  className="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-gray-100 dark:hover:bg-slate-800 cursor-pointer transition-all"
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
                  <span className="font-semibold text-gray-700 dark:text-slate-200 hidden md:block text-sm">
                    {user?.username}
                  </span>
                </div>

                <button
                  onClick={handleLogout}
                  className="hidden sm:block px-4 py-2 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-all font-medium text-sm"
                >
                  Wyloguj
                </button>
              </div>
            </div>
          </div>
        </header>
      )}

      
      {!hideChrome && (
        <>
          <div
            className={`fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden transition-opacity ${sidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
            onClick={() => setSidebarOpen(false)}
          />

          <aside
            className={`fixed top-0 left-0 h-full w-80 bg-white dark:bg-slate-900 shadow-2xl z-50 transform transition-transform lg:hidden ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
          >
            <div className="p-6">
              
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                    <span className="text-2xl">🎯</span>
                  </div>
                  <div className="col-span-2 md:col-span-1">
                    <h2 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                      Menu
                    </h2>
                  </div>
                </div>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <svg className="w-6 h-6 text-gray-700 dark:text-slate-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              
              <div
                className="mb-6 p-4 bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-slate-800 dark:to-slate-800 rounded-xl border border-indigo-100 dark:border-slate-700 cursor-pointer"
                onClick={() => {
                  navigate('/profile');
                  setSidebarOpen(false);
                }}
              >
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
                    <p className="font-bold text-gray-800 dark:text-slate-100">{user?.username}</p>
                    <p className="text-sm text-gray-600 dark:text-slate-300">{user?.email}</p>
                    {isAdmin && (
                      <span className="inline-block mt-1 px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold">
                        🛠️ Administrator
                      </span>
                    )}
                  </div>
                </div>
              </div>

              
              <nav className="space-y-1.5 sm:space-y-2">
                {menuItems.map((item, index) => (
                  <div key={index}>
                    {item.divider && <div className="my-4 border-t-2 border-gray-200" />}
                    <button
                      onClick={() => {
                        navigate(item.path);
                        setSidebarOpen(false);
                      }}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-medium group ${
                        isRouteActive(item.path)
                          ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-200'
                          : 'text-gray-700 dark:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-800'
                      }`}
                    >
                      <span className="text-2xl group-hover:scale-110 transition-transform">
                        {item.icon}
                      </span>
                      <span className="group-hover:text-indigo-600 dark:group-hover:text-indigo-300 transition-colors">
                        {item.label}
                      </span>
                    </button>
                  </div>
                ))}

                
                <div className="pt-4 mt-4 border-t-2 border-gray-200 dark:border-slate-700 sm:hidden">
                  <button
                    onClick={() => {
                      handleLogout();
                      setSidebarOpen(false);
                    }}
                    className="w-full flex items-center gap-3 px-4 py-3 text-red-600 dark:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-all font-medium group"
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
        </>
      )}

      
      <main className="flex-1">{children}</main>

      {!hideChrome && showScrollTop && (
        <button
          type="button"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="fixed right-6 bottom-6 z-40 w-14 h-14 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg hover:from-indigo-700 hover:to-purple-700 transition-all"
          aria-label="Przewin do gory"
          title="Przewin do gory"
        >
          ↑
        </button>
      )}

      
      {!hideChrome && (
        <footer className="bg-white dark:bg-slate-900 border-t border-gray-200 dark:border-slate-800 mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-8">
              
              <div className="md:col-span-1">
                <div className="flex items-center gap-2 sm:gap-3 mb-2 sm:mb-4">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                    <span className="text-lg sm:text-xl">🎯</span>
                  </div>
                  <h3 className="text-base sm:text-lg font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                    Quiz LLM
                  </h3>
                </div>
                <p className="text-gray-600 text-xs sm:text-sm leading-snug sm:leading-normal">
                  Inteligentny system quizowy z adaptacyjnym poziomem trudności oparty na zaawansowanych modelach językowych.
                </p>
              </div>

              
              <div className="grid grid-cols-2 gap-4 sm:gap-8 md:col-span-2">
                
                <div>
                <h3 className="font-bold text-sm sm:text-base text-gray-800 mb-2 sm:mb-4">Szybkie linki</h3>
                <ul className="space-y-1.5 sm:space-y-2">
                  <li>
                    <button
                      onClick={() => navigate('/quiz/setup')}
                      className="text-gray-600 hover:text-indigo-600 transition-colors text-xs sm:text-sm"
                    >
                      Rozpocznij Quiz
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => navigate('/quiz/questions')}
                      className="text-gray-600 hover:text-indigo-600 transition-colors text-xs sm:text-sm"
                    >
                      Biblioteka Pytań
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => navigate('/quiz/history')}
                      className="text-gray-600 hover:text-indigo-600 transition-colors text-xs sm:text-sm"
                    >
                      Historia Quizów
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => navigate('/leaderboard')}
                      className="text-gray-600 hover:text-indigo-600 transition-colors text-xs sm:text-sm"
                    >
                      Ranking
                    </button>
                  </li>
                </ul>
              </div>

              
              <div>
                <h3 className="font-bold text-sm sm:text-base text-gray-800 mb-2 sm:mb-4">Informacje</h3>
                <ul className="space-y-1.5 sm:space-y-2 text-xs sm:text-sm text-gray-600">
                  <li className="flex items-center gap-2">
                    <span>🤖</span>
                    <span>Powered by AI (LLM)</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span>⚙️</span>
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
            </div>

            
            <div className="mt-4 sm:mt-8 pt-4 sm:pt-8 border-t border-gray-200">
              <p className="text-gray-600 text-xs sm:text-sm text-center">
                © 2026 Quiz LLM. Wszelkie prawa zastrzeżone.
              </p>
            </div>
          </div>
        </footer>
      )}
    </div>
  );
}

