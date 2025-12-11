import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser, updateProfile, changePassword, uploadAvatar, updateProfileSettings, logout } from '../../services/api';
import MainLayout from '../../layouts/MainLayout';

export default function UserProfile() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [avatarFile, setAvatarFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const [profileData, setProfileData] = useState({
    username: '',
    email: '',
  });

  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });

  const [settingsData, setSettingsData] = useState({
    default_knowledge_level: 'high_school',
  });

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const me = await getCurrentUser();
      setUser(me);
      setProfileData({
        username: me.username,
        email: me.email,
      });
      setSettingsData({
        default_knowledge_level: me.profile?.default_knowledge_level || 'high_school',
      });
    } catch (err) {
      console.error('Error loading user:', err);
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSuccessMsg('');
    setErrorMsg('');

    try {
      await updateProfile(profileData);
      setSuccessMsg('✅ Profil został zaktualizowany pomyślnie!');
    } catch (err) {
      console.error('Profile update failed:', err);
      setErrorMsg('❌ Nie udało się zaktualizować profilu.');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    if (passwordData.new_password !== passwordData.confirm_password) {
      setErrorMsg('❌ Hasła nie są identyczne!');
      return;
    }

    setLoading(true);
    setSuccessMsg('');
    setErrorMsg('');

    try {
      await changePassword(passwordData);
      setSuccessMsg('🔒 Hasło zostało zmienione pomyślnie!');
      setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      console.error('Password change failed:', err);
      setErrorMsg('❌ Nie udało się zmienić hasła.');
    } finally {
      setLoading(false);
    }
  };

const handleAvatarUpload = async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  setPreview(URL.createObjectURL(file));

  try {
    await uploadAvatar(file);
    setSuccessMsg('🖼️ Avatar został zaktualizowany!');
    await loadUser();
  } catch (err) {
    console.error('Avatar upload failed:', err);
    setErrorMsg('❌ Nie udało się przesłać avatara.');
  }
};

  const handleSettingsUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSuccessMsg('');
    setErrorMsg('');

    try {
      await updateProfileSettings(settingsData);
      setSuccessMsg('⚙️ Ustawienia zostały zaktualizowane pomyślnie!');
      await loadUser();
    } catch (err) {
      console.error('Settings update failed:', err);
      setErrorMsg('❌ Nie udało się zaktualizować ustawień.');
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-lg text-gray-600 font-medium">Ładowanie profilu...</p>
        </div>
      </div>
    );
  }

  return (
    <MainLayout user={user}>
      <div className="max-w-6xl mx-auto px-6 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Lewy panel */}
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 text-center">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">👤 Twój profil</h2>
            <div className="relative inline-block mb-4">
              {preview || user.profile?.avatar_url ? (
                <img
                  src={preview || user.profile.avatar_url}
                  alt="Avatar"
                  className="w-32 h-32 rounded-full border-4 border-indigo-500 object-cover mx-auto"
                />
              ) : (
                <div className="w-32 h-32 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mx-auto border-4 border-indigo-400 text-white text-3xl font-bold">
                  {user.username ? user.username[0].toUpperCase() : '?'}
                </div>
              )}
              <label className="absolute bottom-0 right-0 bg-indigo-600 text-white rounded-full p-2 cursor-pointer shadow-lg hover:bg-indigo-700 transition">
                <input type="file" accept="image/*" onChange={handleAvatarUpload} className="hidden" />
                ✏️
              </label>
            </div>
            <h3 className="text-lg font-semibold text-gray-700">{user.username}</h3>
            <p className="text-sm text-gray-500">{user.email}</p>
          </div>

          {/* Prawy panel */}
          <div className="lg:col-span-2 space-y-8">
            {/* Formularz profilu */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100">
              <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                <span className="text-2xl">🧩</span> Dane konta
              </h2>
              <form onSubmit={handleProfileUpdate} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Nazwa użytkownika</label>
                  <input
                    type="text"
                    value={profileData.username}
                    onChange={(e) => setProfileData({ ...profileData, username: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 transition"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Adres e-mail</label>
                  <input
                    type="email"
                    value={profileData.email}
                    onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 transition"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all shadow-md disabled:opacity-50"
                >
                  💾 Zapisz zmiany
                </button>
              </form>
            </div>

            {/* Formularz ustawień quizu */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100">
              <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                <span className="text-2xl">⚙️</span> Ustawienia quizu
              </h2>
              <form onSubmit={handleSettingsUpdate} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Domyślny poziom wiedzy</label>
                  <select
                    value={settingsData.default_knowledge_level}
                    onChange={(e) => setSettingsData({ ...settingsData, default_knowledge_level: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 transition bg-white"
                  >
                    <option value="elementary">🎒 Szkoła podstawowa</option>
                    <option value="high_school">🎓 Liceum</option>
                    <option value="university">🏛️ Studia</option>
                    <option value="expert">🔬 Ekspert</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Pytania będą domyślnie dostosowane do tego poziomu edukacji. Możesz to zmienić podczas tworzenia quizu.
                  </p>
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-600 text-white rounded-xl font-semibold hover:from-blue-600 hover:to-cyan-700 transition-all shadow-md disabled:opacity-50"
                >
                  💾 Zapisz ustawienia
                </button>
              </form>
            </div>

            {/* Formularz zmiany hasła */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100">
              <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                <span className="text-2xl">🔒</span> Zmień hasło
              </h2>
              <form onSubmit={handlePasswordChange} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Stare hasło</label>
                  <input
                    type="password"
                    value={passwordData.old_password}
                    onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 transition"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Nowe hasło</label>
                  <input
                    type="password"
                    value={passwordData.new_password}
                    onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 transition"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Powtórz nowe hasło</label>
                  <input
                    type="password"
                    value={passwordData.confirm_password}
                    onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 transition"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-3 bg-gradient-to-r from-green-500 to-green-700 text-white rounded-xl font-semibold hover:from-green-600 hover:to-green-800 transition-all shadow-md disabled:opacity-50"
                >
                  🔑 Zmień hasło
                </button>
              </form>
            </div>

            {(successMsg || errorMsg) && (
              <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
                {successMsg && <p className="text-green-600 font-semibold">{successMsg}</p>}
                {errorMsg && <p className="text-red-600 font-semibold">{errorMsg}</p>}
              </div>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}