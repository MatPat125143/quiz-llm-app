import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  updateProfile,
  changePassword,
  uploadAvatar,
  updateProfileSettings,
  deleteAvatar,
  deleteMyAccount,
  getQuizHistory,
  logout
} from '../../services/api';
import MainLayout from '../../layouts/MainLayout';
import { KNOWLEDGE_LEVELS } from '../../services/constants';
import useCurrentUser from '../../hooks/useCurrentUser';
import LoadingState from '../../components/LoadingState';
import ProfileDataSection from './profile/ProfileDataSection';
import ProfileSettingsSection from './profile/ProfileSettingsSection';

export default function UserProfile() {
  const navigate = useNavigate();
  const { user, loading: userLoading, refreshUser } = useCurrentUser();
  const [lastQuiz, setLastQuiz] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [, setSuccessMsg] = useState('');
  const [, setErrorMsg] = useState('');
  const [activeTab, setActiveTab] = useState('data');

  const [profileData, setProfileData] = useState({
    username: '',
    email: ''
  });

  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: ''
  });

  const [settingsData, setSettingsData] = useState({
    default_knowledge_level: 'high_school'
  });

  const loadLastQuiz = async () => {
    try {
      const history = await getQuizHistory({ limit: 1 });
      setLastQuiz(history?.results?.[0] || null);
    } catch (err) {
      console.error('Error loading last quiz:', err);
    }
  };

  useEffect(() => {
    loadLastQuiz();
  }, []);

  useEffect(() => {
    if (!user) return;
    setProfileData({
      username: user.username,
      email: user.email
    });
    setSettingsData({
      default_knowledge_level: user.profile?.default_knowledge_level || 'high_school'
    });
  }, [user]);

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSuccessMsg('');
    setErrorMsg('');

    try {
      await updateProfile(profileData);
      setSuccessMsg('Profil został zaktualizowany pomyślnie.');
    } catch (err) {
      console.error('Profile update failed:', err);
      setErrorMsg('Nie udało się zaktualizować profilu.');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    if (passwordData.new_password !== passwordData.confirm_password) {
      setErrorMsg('Hasła nie są identyczne.');
      return;
    }

    setLoading(true);
    setSuccessMsg('');
    setErrorMsg('');

    try {
      await changePassword(passwordData);
      setSuccessMsg('Hasło zostało zmienione pomyślnie.');
      setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      console.error('Password change failed:', err);
      setErrorMsg('Nie udało się zmienić hasła.');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setPreview(URL.createObjectURL(file));

    try {
      await uploadAvatar(file);
      setSuccessMsg('Avatar został zaktualizowany.');
      await refreshUser();
      await loadLastQuiz();
    } catch (err) {
      console.error('Avatar upload failed:', err);
      setErrorMsg('Nie udało się przesłać avatara.');
    }
  };

  const handleAvatarDelete = async () => {
    setLoading(true);
    setSuccessMsg('');
    setErrorMsg('');

    try {
      await deleteAvatar();
      setPreview(null);
      setSuccessMsg('Avatar został usunięty.');
      await refreshUser();
      await loadLastQuiz();
    } catch (err) {
      console.error('Avatar delete failed:', err);
      setErrorMsg('Nie udało się usunąć avatara.');
    } finally {
      setLoading(false);
    }
  };

  const handleSettingsUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSuccessMsg('');
    setErrorMsg('');

    try {
      await updateProfileSettings(settingsData);
      setSuccessMsg('Ustawienia zostały zaktualizowane pomyślnie.');
      await refreshUser();
      await loadLastQuiz();
    } catch (err) {
      console.error('Settings update failed:', err);
      setErrorMsg('Nie udało się zaktualizować ustawień.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!window.confirm('Czy na pewno chcesz usunąć konto? Tej operacji nie można cofnąć.')) {
      return;
    }

    setLoading(true);
    setSuccessMsg('');
    setErrorMsg('');

    try {
      await deleteMyAccount();
      logout();
      navigate('/login');
    } catch (err) {
      console.error('Account delete failed:', err);
      setErrorMsg('Nie udało się usunąć konta.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (value) => {
    if (!value) return 'Brak danych';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return 'Brak danych';
    return date.toLocaleString('pl-PL');
  };

  if (!user || userLoading) {
    return <LoadingState message="Ładowanie profilu..." fullScreen={true} />;
  }

  const stats = [
    { label: 'Rozegrane gry', value: user.profile?.total_quizzes_played ?? 0 },
    { label: 'Łącznie poprawne', value: user.profile?.total_correct_answers ?? 0 },
    { label: 'Najwyższa passa', value: user.profile?.highest_streak ?? 0 },
    { label: 'Dokładność', value: `${user.profile?.accuracy ?? 0}%` }
  ];

  const roleDisplay = user.profile?.role === 'admin' ? '👑 Admin' : '👤 Gracz';
  const lastQuizDate = lastQuiz?.ended_at || lastQuiz?.completed_at || lastQuiz?.started_at;

  return (
    <MainLayout user={user}>
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        <div className="mb-2 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl p-8 text-white shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-2">👤 Profil użytkownika</h1>
              <p className="text-indigo-100 text-lg">Zarządzaj danymi konta, ustawieniami i bezpieczeństwem.</p>
            </div>
            <div className="hidden md:block text-8xl opacity-20">👤</div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-lg border border-gray-100 dark:border-slate-800 p-2">
          <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('data')}
            className={`flex-1 py-3 px-6 rounded-xl font-semibold transition-all ${
              activeTab === 'data'
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                : 'bg-gray-50 dark:bg-slate-800 text-gray-700 dark:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-700'
            }`}
          >
            👤 Dane użytkownika
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('settings')}
            className={`flex-1 py-3 px-6 rounded-xl font-semibold transition-all ${
              activeTab === 'settings'
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                : 'bg-gray-50 dark:bg-slate-800 text-gray-700 dark:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-700'
            }`}
          >
            ⚙️ Ustawienia
          </button>
          </div>
        </div>

        {activeTab === 'data' && (
          <ProfileDataSection
            user={user}
            preview={preview}
            handleAvatarUpload={handleAvatarUpload}
            handleAvatarDelete={handleAvatarDelete}
            stats={stats}
            roleDisplay={roleDisplay}
            formatDate={formatDate}
            lastQuizDate={lastQuizDate}
          />
        )}

        {activeTab === 'settings' && (
          <ProfileSettingsSection
            loading={loading}
            profileData={profileData}
            setProfileData={setProfileData}
            passwordData={passwordData}
            setPasswordData={setPasswordData}
            settingsData={settingsData}
            setSettingsData={setSettingsData}
            handleProfileUpdate={handleProfileUpdate}
            handleSettingsUpdate={handleSettingsUpdate}
            handlePasswordChange={handlePasswordChange}
            handleDeleteAccount={handleDeleteAccount}
            knowledgeLevels={KNOWLEDGE_LEVELS}
          />
        )}
      </div>
    </MainLayout>
  );
}

