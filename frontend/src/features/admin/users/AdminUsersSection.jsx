import FiltersPanel from '../../../components/FiltersPanel';
import PaginationBar from '../../../components/PaginationBar';

export default function AdminUsersSection({
  users,
  loading,
  searchQuery,
  setSearchQuery,
  roleFilter,
  setRoleFilter,
  statusFilter,
  setStatusFilter,
  userFiltersOpen,
  setUserFiltersOpen,
  clearFilters,
  userPage,
  setUserPage,
  userPageSize,
  setUserPageSize,
  openUserQuizzes,
  handleChangeRole,
  handleToggleStatus,
  handleDeleteUser,
}) {
  return (
    <>
      <FiltersPanel
        title="Filtry i sortowanie"
        icon=""
        isOpen={userFiltersOpen}
        onToggle={() => setUserFiltersOpen((prev) => !prev)}
        className="mb-10"
      >
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-semibold text-gray-700 mb-2">Szukaj</label>
            <input
              type="text"
              placeholder="Wpisz nazwę lub e-mail..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="ui-input"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Rola</label>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="ui-select"
            >
              <option value="">Wszystkie</option>
              <option value="admin">👑 Admin</option>
              <option value="user">👤 Gracz</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="ui-select"
            >
              <option value="">Wszystkie</option>
              <option value="true">🔓 Aktywny</option>
              <option value="false">🔒 Nieaktywny</option>
            </select>
          </div>

          <div className="md:col-span-4 mt-2 flex justify-end">
            <button
              onClick={clearFilters}
              className="px-4 py-2 bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200 rounded-xl hover:bg-gray-200 dark:hover:bg-slate-700 transition font-semibold flex items-center gap-2"
            >
              🗑️ Wyczyść filtry
            </button>
          </div>
        </div>
      </FiltersPanel>

      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-lg p-6">
        <div className="mb-6 text-gray-700 dark:text-slate-200 font-medium">
          Znaleziono: <span className="text-indigo-600 font-bold">{users.length}</span> graczy
        </div>

        {users.length === 0 ? (
          <div className="text-center py-10 text-gray-500 dark:text-slate-300">
            Brak graczy do wyświetlenia
          </div>
        ) : (
          <div className="space-y-4">
            {users
              .slice((userPage - 1) * userPageSize, userPage * userPageSize)
              .map((user) => {
                const avatarUrl = user.avatar_url || user.profile?.avatar_url || null;
                return (
                  <div
                    key={user.id}
                    className="group p-6 border-2 border-gray-100 dark:border-slate-800 rounded-xl hover:border-indigo-300 hover:shadow-lg transition-all bg-gradient-to-r from-white to-gray-50 dark:from-slate-900 dark:to-slate-800"
                  >
                    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="w-14 h-14 rounded-full bg-indigo-100 dark:bg-slate-800 flex items-center justify-center overflow-hidden border border-indigo-200 dark:border-slate-700 shrink-0">
                            {avatarUrl ? (
                              <img
                                src={avatarUrl}
                                alt={user.username}
                                className="w-full h-full object-cover"
                                loading="lazy"
                              />
                            ) : (
                              <span className="text-lg font-bold text-indigo-700 dark:text-indigo-300">
                                {user.username?.charAt(0)?.toUpperCase() || '?'}
                              </span>
                            )}
                          </div>
                          <div className="text-left min-w-0 flex-1">
                            <h3 className="text-lg sm:text-xl font-bold text-gray-800 dark:text-slate-100 break-words">
                              {user.username}
                            </h3>
                            <p className="text-xs sm:text-sm text-gray-600 dark:text-slate-300 break-all">
                              {user.email}
                            </p>
                            <div className="mt-2 flex flex-wrap gap-2">
                              <span
                                className={`px-3 py-1.5 rounded-full text-xs sm:text-sm text-center whitespace-nowrap font-semibold ${
                                  user.role === 'admin'
                                    ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200'
                                    : 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200'
                                }`}
                              >
                                {user.role === 'admin' ? '👑 Admin' : '👤 Gracz'}
                              </span>
                              <span
                                className={`px-3 py-1.5 rounded-full text-xs sm:text-sm text-center whitespace-nowrap font-semibold ${
                                  user.is_active
                                    ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200'
                                    : 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200'
                                }`}
                              >
                                {user.is_active ? '🔓 Aktywny' : '🔒 Nieaktywny'}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-2 w-full md:w-[280px] lg:w-[300px] xl:w-auto xl:flex xl:flex-wrap xl:items-center xl:justify-end xl:gap-3">
                        <button
                          onClick={() => openUserQuizzes(user)}
                          className="bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-400 text-white px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold flex items-center justify-center gap-1.5 min-h-[42px] w-full xl:w-[150px]"
                        >
                          📜 Historia
                        </button>
                        <button
                          onClick={() => handleChangeRole(user.id, user.role)}
                          className="bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-400 text-white px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold flex items-center justify-center gap-1.5 min-h-[42px] w-full xl:w-[150px]"
                        >
                          🔁 Rola
                        </button>
                        <button
                          onClick={() => handleToggleStatus(user.id, user.is_active)}
                          className="bg-yellow-500 hover:bg-yellow-600 dark:bg-yellow-400 dark:hover:bg-yellow-300 text-white px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold flex items-center justify-center gap-1.5 min-h-[42px] w-full xl:w-[150px]"
                        >
                          {user.is_active ? '🔒 Zablokuj' : '🔓 Odblokuj'}
                        </button>
                        <button
                          onClick={() => handleDeleteUser(user.id, user.email)}
                          className="bg-red-600 hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-400 text-white px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold flex items-center justify-center gap-1.5 min-h-[42px] w-full xl:w-[150px]"
                        >
                          🗑️ Usuń
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
        )}

        {users.length > 0 && (
          <PaginationBar
            page={userPage}
            totalPages={Math.max(1, Math.ceil(users.length / userPageSize))}
            hasPrev={userPage > 1}
            hasNext={userPage < Math.max(1, Math.ceil(users.length / userPageSize))}
            loading={loading}
            onPrev={() => setUserPage((p) => Math.max(1, p - 1))}
            onNext={() =>
              setUserPage((p) => Math.min(Math.max(1, Math.ceil(users.length / userPageSize)), p + 1))
            }
            pageSize={userPageSize}
            onPageSizeChange={(size) => {
              setUserPageSize(size);
              setUserPage(1);
            }}
          />
        )}
      </div>
    </>
  );
}
