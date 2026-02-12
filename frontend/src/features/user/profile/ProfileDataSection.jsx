export default function ProfileDataSection({
  user,
  preview,
  handleAvatarUpload,
  handleAvatarDelete,
  stats,
  roleDisplay,
  formatDate,
  lastQuizDate
}) {
  return (
    <>
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 shadow-lg border border-gray-100 dark:border-slate-800 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-800 dark:text-slate-100 leading-none">Avatar</h2>
          </div>
          <div className="flex-1 flex items-center justify-center">
            <label className="group relative block w-36 h-36 mx-auto cursor-pointer">
              {preview || user.profile?.avatar_url ? (
                <img
                  src={preview || user.profile.avatar_url}
                  alt="Avatar"
                  className="w-36 h-36 rounded-full border-4 border-indigo-500 object-cover"
                />
              ) : (
                <div className="w-36 h-36 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center border-4 border-indigo-400 text-white text-3xl font-bold">
                  {user.username ? user.username[0].toUpperCase() : '?'}
                </div>
              )}
              {user.profile?.avatar_url && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleAvatarDelete();
                  }}
                  className="absolute bottom-0 right-0 -translate-x-1/6 -translate-y-1/6 w-9 h-9 rounded-full bg-red-600 text-white shadow-md hover:bg-red-700 transition"
                  title="Usuń avatar"
                >
                  ✕
                </button>
              )}
              {!user.profile?.avatar_url && (
                <>
                  <div className="absolute inset-0 rounded-full bg-black/55 text-white text-xs font-semibold flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                    Wybierz avatar
                  </div>
                  <input type="file" accept="image/*" onChange={handleAvatarUpload} className="hidden" />
                </>
              )}
            </label>
          </div>
        </div>

        <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-lg border border-gray-100 dark:border-slate-800">
          <h2 className="text-lg font-bold text-gray-800 dark:text-slate-100 mb-4">Statystyki</h2>
          <div className="grid grid-cols-2 gap-4">
            {stats.map((item) => (
              <div
                key={item.label}
                className="bg-gray-50 dark:bg-slate-800 rounded-xl p-4 border border-gray-100 dark:border-slate-700"
              >
                <div className="text-sm text-gray-500 dark:text-slate-300">{item.label}</div>
                <div className="text-xl font-bold text-gray-800 dark:text-slate-100">{item.value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-lg border border-gray-100 dark:border-slate-800">
        <h2 className="text-lg font-bold text-gray-800 dark:text-slate-100 mb-4">Dane gracza</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-gray-50 dark:bg-slate-800 rounded-xl p-4 border border-gray-100 dark:border-slate-700">
            <div className="text-xs text-gray-500 dark:text-slate-300">Nazwa użytkownika</div>
            <div className="font-semibold text-gray-800 dark:text-slate-100">{user.username}</div>
          </div>
          <div className="bg-gray-50 dark:bg-slate-800 rounded-xl p-4 border border-gray-100 dark:border-slate-700">
            <div className="text-xs text-gray-500 dark:text-slate-300">E-mail</div>
            <div className="font-semibold text-gray-800 dark:text-slate-100">{user.email}</div>
          </div>
          <div className="bg-gray-50 dark:bg-slate-800 rounded-xl p-4 border border-gray-100 dark:border-slate-700">
            <div className="text-xs text-gray-500 dark:text-slate-300">Status</div>
            <div className="font-semibold text-gray-800 dark:text-slate-100">{roleDisplay}</div>
          </div>
        </div>
        <div className="grid md:grid-cols-2 gap-4 mt-4">
          <div className="bg-gray-50 dark:bg-slate-800 rounded-xl p-4 border border-gray-100 dark:border-slate-700">
            <div className="text-xs text-gray-500 dark:text-slate-300">Ostatnie logowanie</div>
            <div className="font-semibold text-gray-800 dark:text-slate-100">{formatDate(user.last_login)}</div>
          </div>
          <div className="bg-gray-50 dark:bg-slate-800 rounded-xl p-4 border border-gray-100 dark:border-slate-700">
            <div className="text-xs text-gray-500 dark:text-slate-300">Ostatnia gra</div>
            <div className="font-semibold text-gray-800 dark:text-slate-100">{formatDate(lastQuizDate)}</div>
          </div>
        </div>
      </div>
    </>
  );
}
