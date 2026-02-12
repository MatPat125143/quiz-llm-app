export default function ProfileSettingsSection({
  loading,
  profileData,
  setProfileData,
  passwordData,
  setPasswordData,
  settingsData,
  setSettingsData,
  handleProfileUpdate,
  handleSettingsUpdate,
  handlePasswordChange,
  handleDeleteAccount,
  knowledgeLevels
}) {
  return (
    <div className="grid lg:grid-cols-2 gap-6 items-stretch">
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-lg border border-gray-100 dark:border-slate-800 flex flex-col min-h-[360px]">
        <h2 className="text-lg font-bold text-gray-800 dark:text-slate-100 mb-4">Dane konta</h2>
        <form onSubmit={handleProfileUpdate} className="flex flex-col gap-4 h-full">
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-1">
              Nazwa użytkownika
            </label>
            <input
              type="text"
              value={profileData.username}
              onChange={(e) => setProfileData({ ...profileData, username: e.target.value })}
              className="ui-input"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-1">
              Adres e-mail
            </label>
            <input
              type="email"
              value={profileData.email}
              onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
              className="ui-input"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="mt-auto px-6 py-3 w-full sm:w-[200px] bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all shadow-md disabled:opacity-50 self-start"
          >
            Zapisz zmiany
          </button>
        </form>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-lg border border-gray-100 dark:border-slate-800 flex flex-col min-h-[360px]">
        <h2 className="text-lg font-bold text-gray-800 dark:text-slate-100 mb-4">Ustawienia profilu</h2>
        <form onSubmit={handleSettingsUpdate} className="flex flex-col gap-4 h-full">
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-1">
              Domyślny poziom wiedzy
            </label>
            <select
              value={settingsData.default_knowledge_level}
              onChange={(e) =>
                setSettingsData({ ...settingsData, default_knowledge_level: e.target.value })
              }
              className="ui-select"
            >
              {knowledgeLevels.map((level) => (
                <option key={level.key} value={level.key}>
                  {level.emoji} {level.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">
              Pytania będą domyślnie dostosowane do tego poziomu edukacji.
            </p>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="mt-auto px-6 py-3 w-full sm:w-[200px] bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl font-semibold hover:from-indigo-600 hover:to-purple-700 transition-all shadow-md disabled:opacity-50 self-start"
          >
            Zapisz ustawienia
          </button>
        </form>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-lg border border-gray-100 dark:border-slate-800 flex flex-col min-h-[360px]">
        <h2 className="text-lg font-bold text-gray-800 dark:text-slate-100 mb-4">Zmień hasło</h2>
        <form onSubmit={handlePasswordChange} className="flex flex-col gap-4 h-full">
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-1">
              Stare hasło
            </label>
            <input
              type="password"
              value={passwordData.old_password}
              onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
              className="ui-input"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-1">
              Nowe hasło
            </label>
            <input
              type="password"
              value={passwordData.new_password}
              onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
              className="ui-input"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-1">
              Powtórz nowe hasło
            </label>
            <input
              type="password"
              value={passwordData.confirm_password}
              onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
              className="ui-input"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="mt-auto px-6 py-3 w-full sm:w-[200px] bg-gradient-to-r from-blue-500 to-cyan-600 text-white rounded-xl font-semibold hover:from-blue-600 hover:to-cyan-700 transition-all shadow-md disabled:opacity-50 self-start"
          >
            Zmień hasło
          </button>
        </form>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-lg border border-red-200 dark:border-red-500/40 flex flex-col min-h-[360px]">
        <h2 className="text-lg font-bold text-gray-800 dark:text-slate-100 mb-2">Usuń konto</h2>
        <p className="text-sm text-gray-600 dark:text-slate-300 mb-4">
          Usunięcie konta jest nieodwracalne. Wszystkie Twoje dane zostaną skasowane.
        </p>
        <button
          type="button"
          onClick={handleDeleteAccount}
          disabled={loading}
          className="mt-auto px-6 py-3 w-full sm:w-[200px] bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700 transition-all shadow-md disabled:opacity-50 self-start"
        >
          Usuń konto
        </button>
      </div>
    </div>
  );
}
