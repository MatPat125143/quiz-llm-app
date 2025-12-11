import { useState, useEffect } from 'react';
import {
  adminGetQuestions,
  adminGetQuestionDetail,
  adminUpdateQuestion,
  adminDeleteQuestion,
  adminGetQuestionStats
} from '../../services/api';
import LatexRenderer from '../../components/LatexRenderer';

export default function QuestionsManager() {
  const [questions, setQuestions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Paginacja i filtrowanie
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterTopic, setFilterTopic] = useState('');
  const [filterDifficulty, setFilterDifficulty] = useState('');
  const [filterKnowledge, setFilterKnowledge] = useState('');

  // Edycja
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [editFormData, setEditFormData] = useState({});

  useEffect(() => {
    loadQuestions();
    loadStats();
  }, [currentPage, searchQuery, filterTopic, filterDifficulty, filterKnowledge]);

  const loadQuestions = async () => {
    try {
      setLoading(true);
      const params = {
        page: currentPage,
        page_size: 20,
        ...(searchQuery && { search: searchQuery }),
        ...(filterTopic && { topic: filterTopic }),
        ...(filterDifficulty && { difficulty: filterDifficulty }),
        ...(filterKnowledge && { knowledge_level: filterKnowledge })
      };

      const data = await adminGetQuestions(params);
      setQuestions(data.questions);
      setTotalPages(data.pagination.total_pages);
    } catch (err) {
      console.error('Error loading questions:', err);
      setError('Nie udało się załadować pytań.');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await adminGetQuestionStats();
      setStats(data);
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  const handleEdit = async (question) => {
    try {
      const detail = await adminGetQuestionDetail(question.id);
      setEditingQuestion(detail);
      setEditFormData({
        question_text: detail.question_text,
        correct_answer: detail.correct_answer,
        wrong_answer_1: detail.wrong_answer_1,
        wrong_answer_2: detail.wrong_answer_2,
        wrong_answer_3: detail.wrong_answer_3,
        explanation: detail.explanation,
        topic: detail.topic,
        subtopic: detail.subtopic || '',
        difficulty_level: detail.difficulty_level,
        knowledge_level: detail.knowledge_level
      });
    } catch (err) {
      console.error('Error loading question detail:', err);
      setError('Nie udało się załadować szczegółów pytania.');
    }
  };

  const handleSaveEdit = async () => {
    try {
      setLoading(true);
      await adminUpdateQuestion(editingQuestion.id, editFormData);
      setSuccess('✅ Pytanie zostało zaktualizowane!');
      setEditingQuestion(null);
      loadQuestions();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      console.error('Error updating question:', err);
      setError('❌ Nie udało się zaktualizować pytania.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (questionId) => {
    if (!window.confirm('Czy na pewno chcesz usunąć to pytanie?')) return;

    try {
      setLoading(true);
      await adminDeleteQuestion(questionId);
      setSuccess('🗑️ Pytanie zostało usunięte!');
      loadQuestions();
      loadStats();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      console.error('Error deleting question:', err);
      setError('❌ Nie udało się usunąć pytania. Może być używane w aktywnej sesji.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Nagłówek i statystyki */}
      <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
        <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          📚 Zarządzanie pytaniami
        </h2>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <div className="text-3xl font-bold text-blue-600">{stats.total_questions}</div>
              <div className="text-sm text-blue-800">Wszystkich pytań</div>
            </div>
            {stats.by_difficulty && stats.by_difficulty.map((item) => (
              <div key={item.difficulty_level} className="bg-purple-50 border border-purple-200 rounded-xl p-4">
                <div className="text-3xl font-bold text-purple-600">{item.count}</div>
                <div className="text-sm text-purple-800">Poziom: {item.difficulty_level}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Komunikaty */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-xl">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-xl">
          {success}
        </div>
      )}

      {/* Filtry i wyszukiwanie */}
      <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
        <h3 className="text-lg font-bold text-gray-800 mb-4">🔍 Filtruj i wyszukaj</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <input
            type="text"
            placeholder="Szukaj w treści pytania..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            className="px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400"
          />
          <input
            type="text"
            placeholder="Filtruj po temacie..."
            value={filterTopic}
            onChange={(e) => {
              setFilterTopic(e.target.value);
              setCurrentPage(1);
            }}
            className="px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400"
          />
          <select
            value={filterDifficulty}
            onChange={(e) => {
              setFilterDifficulty(e.target.value);
              setCurrentPage(1);
            }}
            className="px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 bg-white"
          >
            <option value="">Wszystkie trudności</option>
            <option value="łatwy">Łatwy</option>
            <option value="średni">Średni</option>
            <option value="trudny">Trudny</option>
          </select>
          <select
            value={filterKnowledge}
            onChange={(e) => {
              setFilterKnowledge(e.target.value);
              setCurrentPage(1);
            }}
            className="px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 bg-white"
          >
            <option value="">Wszystkie poziomy</option>
            <option value="elementary">Podstawówka</option>
            <option value="high_school">Liceum</option>
            <option value="university">Studia</option>
            <option value="expert">Ekspert</option>
          </select>
          <button
            onClick={() => {
              setSearchQuery('');
              setFilterTopic('');
              setFilterDifficulty('');
              setFilterKnowledge('');
              setCurrentPage(1);
            }}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-xl hover:bg-gray-300 font-semibold"
          >
            Wyczyść filtry
          </button>
        </div>
      </div>

      {/* Lista pytań */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Ładowanie pytań...</p>
          </div>
        ) : questions.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            Nie znaleziono pytań spełniających kryteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b-2 border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">ID</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Pytanie</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Temat</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Trudność</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Poziom</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Statystyki</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Akcje</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {questions.map((question) => (
                  <tr key={question.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-700">{question.id}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 max-w-md">
                      <div className="line-clamp-2">
                        <LatexRenderer text={question.question_text} inline={true} />
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      <div className="font-semibold">{question.topic}</div>
                      {question.subtopic && (
                        <div className="text-xs text-gray-500">{question.subtopic}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        question.difficulty_level === 'łatwy' ? 'bg-green-100 text-green-700' :
                        question.difficulty_level === 'średni' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {question.difficulty_level}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      {question.knowledge_level === 'elementary' && '🎒 Podstawówka'}
                      {question.knowledge_level === 'high_school' && '🎓 Liceum'}
                      {question.knowledge_level === 'university' && '🏛️ Studia'}
                      {question.knowledge_level === 'expert' && '🔬 Ekspert'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      <div>{question.total_answers} odpowiedzi</div>
                      <div className="text-xs text-gray-500">
                        {question.success_rate}% poprawnych
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(question)}
                          className="px-3 py-1 bg-blue-500 text-white rounded-lg hover:bg-blue-600 font-semibold text-xs"
                        >
                          ✏️ Edytuj
                        </button>
                        <button
                          onClick={() => handleDelete(question.id)}
                          className="px-3 py-1 bg-red-500 text-white rounded-lg hover:bg-red-600 font-semibold text-xs"
                        >
                          🗑️ Usuń
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Paginacja */}
        {totalPages > 1 && (
          <div className="flex justify-center items-center gap-2 p-4 border-t border-gray-200">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 font-semibold"
            >
              ← Poprzednia
            </button>
            <span className="text-gray-600">
              Strona {currentPage} z {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 font-semibold"
            >
              Następna →
            </button>
          </div>
        )}
      </div>

      {/* Modal edycji */}
      {editingQuestion && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto p-8">
            <h3 className="text-2xl font-bold text-gray-800 mb-6">✏️ Edytuj pytanie #{editingQuestion.id}</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Treść pytania</label>
                <textarea
                  value={editFormData.question_text}
                  onChange={(e) => setEditFormData({ ...editFormData, question_text: e.target.value })}
                  className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400"
                  rows="3"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Poprawna odpowiedź</label>
                <input
                  type="text"
                  value={editFormData.correct_answer}
                  onChange={(e) => setEditFormData({ ...editFormData, correct_answer: e.target.value })}
                  className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Błędna odpowiedź 1</label>
                <input
                  type="text"
                  value={editFormData.wrong_answer_1}
                  onChange={(e) => setEditFormData({ ...editFormData, wrong_answer_1: e.target.value })}
                  className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Błędna odpowiedź 2</label>
                <input
                  type="text"
                  value={editFormData.wrong_answer_2}
                  onChange={(e) => setEditFormData({ ...editFormData, wrong_answer_2: e.target.value })}
                  className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Błędna odpowiedź 3</label>
                <input
                  type="text"
                  value={editFormData.wrong_answer_3}
                  onChange={(e) => setEditFormData({ ...editFormData, wrong_answer_3: e.target.value })}
                  className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Wyjaśnienie</label>
                <textarea
                  value={editFormData.explanation}
                  onChange={(e) => setEditFormData({ ...editFormData, explanation: e.target.value })}
                  className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400"
                  rows="3"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Temat</label>
                  <input
                    type="text"
                    value={editFormData.topic}
                    onChange={(e) => setEditFormData({ ...editFormData, topic: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Podtemat (opcjonalnie)</label>
                  <input
                    type="text"
                    value={editFormData.subtopic}
                    onChange={(e) => setEditFormData({ ...editFormData, subtopic: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Poziom trudności</label>
                  <select
                    value={editFormData.difficulty_level}
                    onChange={(e) => setEditFormData({ ...editFormData, difficulty_level: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 bg-white"
                  >
                    <option value="łatwy">Łatwy</option>
                    <option value="średni">Średni</option>
                    <option value="trudny">Trudny</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Poziom wiedzy</label>
                  <select
                    value={editFormData.knowledge_level}
                    onChange={(e) => setEditFormData({ ...editFormData, knowledge_level: e.target.value })}
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 bg-white"
                  >
                    <option value="elementary">Podstawówka</option>
                    <option value="high_school">Liceum</option>
                    <option value="university">Studia</option>
                    <option value="expert">Ekspert</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="flex gap-4 mt-6">
              <button
                onClick={() => setEditingQuestion(null)}
                className="flex-1 px-6 py-3 bg-gray-200 text-gray-700 rounded-xl hover:bg-gray-300 font-semibold"
              >
                Anuluj
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={loading}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 font-semibold disabled:opacity-50"
              >
                {loading ? 'Zapisywanie...' : '💾 Zapisz zmiany'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
