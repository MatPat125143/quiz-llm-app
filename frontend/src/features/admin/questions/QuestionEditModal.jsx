export default function QuestionEditModal({
  editingQuestion,
  setEditingQuestion,
  editFormData,
  setEditFormData,
  loading,
  handleSaveEdit
}) {
  if (!editingQuestion) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-3 sm:p-4 z-50">
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl max-w-5xl w-full max-h-[92vh] overflow-hidden relative flex flex-col">
        <div className="sticky top-0 z-10 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 p-5 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl sm:text-3xl font-bold">✏️ Edytuj pytanie #{editingQuestion.id}</h3>
            </div>
            <button
              type="button"
              onClick={() => setEditingQuestion(null)}
              className="text-white/90 hover:text-red-200 text-2xl font-bold transition-colors"
              aria-label="Zamknij"
              title="Zamknij"
            >
              ✖
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-7">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="grid grid-cols-1 lg:grid-rows-2 gap-4 lg:min-h-[460px]">
              <div className="bg-gradient-to-br from-gray-50 to-indigo-50/50 dark:from-slate-900 dark:to-slate-800 rounded-xl p-4 flex flex-col">
                <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-2">
                  📝 Treść pytania
                </label>
                <textarea
                  value={editFormData.question_text}
                  onChange={(e) => setEditFormData({ ...editFormData, question_text: e.target.value })}
                  className="ui-input resize-none flex-1 min-h-[200px] bg-white/80 dark:bg-slate-900/70"
                />
              </div>

              <div className="bg-gradient-to-br from-gray-50 to-blue-50/40 dark:from-slate-900 dark:to-slate-800 rounded-xl p-4 flex flex-col">
                <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-2">
                  💡 Wyjaśnienie
                </label>
                <textarea
                  value={editFormData.explanation}
                  onChange={(e) => setEditFormData({ ...editFormData, explanation: e.target.value })}
                  className="ui-input resize-none flex-1 min-h-[200px] bg-white/80 dark:bg-slate-900/70"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
              <div className="bg-gradient-to-br from-gray-50 to-green-50/40 dark:from-slate-900 dark:to-slate-800 rounded-xl p-4">
                <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-2">
                  ✅ Poprawna odpowiedź
                </label>
                <input
                  type="text"
                  value={editFormData.correct_answer}
                  onChange={(e) => setEditFormData({ ...editFormData, correct_answer: e.target.value })}
                  className="ui-input bg-white/80 dark:bg-slate-900/70"
                />

                <div className="grid grid-cols-1 gap-3 mt-3">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-2">
                      ❌ Błędna odpowiedź 1
                    </label>
                    <input
                      type="text"
                      value={editFormData.wrong_answer_1}
                      onChange={(e) => setEditFormData({ ...editFormData, wrong_answer_1: e.target.value })}
                      className="ui-input bg-white/80 dark:bg-slate-900/70"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-2">
                      ❌ Błędna odpowiedź 2
                    </label>
                    <input
                      type="text"
                      value={editFormData.wrong_answer_2}
                      onChange={(e) => setEditFormData({ ...editFormData, wrong_answer_2: e.target.value })}
                      className="ui-input bg-white/80 dark:bg-slate-900/70"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-2">
                      ❌ Błędna odpowiedź 3
                    </label>
                    <input
                      type="text"
                      value={editFormData.wrong_answer_3}
                      onChange={(e) => setEditFormData({ ...editFormData, wrong_answer_3: e.target.value })}
                      className="ui-input bg-white/80 dark:bg-slate-900/70"
                    />
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-gray-50 to-purple-50/40 dark:from-slate-900 dark:to-slate-800 rounded-xl p-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-2">
                      🗂️ Temat
                    </label>
                    <input
                      type="text"
                      value={editFormData.topic}
                      onChange={(e) => setEditFormData({ ...editFormData, topic: e.target.value })}
                      className="ui-input bg-white/80 dark:bg-slate-900/70"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-2">
                      📚 Podtemat (opcjonalnie)
                    </label>
                    <input
                      type="text"
                      value={editFormData.subtopic}
                      onChange={(e) => setEditFormData({ ...editFormData, subtopic: e.target.value })}
                      className="ui-input bg-white/80 dark:bg-slate-900/70"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-3">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-2">
                      🎚️ Poziom trudności
                    </label>
                    <select
                      value={editFormData.difficulty_level}
                      onChange={(e) => setEditFormData({ ...editFormData, difficulty_level: e.target.value })}
                      className="ui-select bg-white/80 dark:bg-slate-900/70"
                    >
                      <option value="łatwy">🟢 Łatwy</option>
                      <option value="średni">🟡 Średni</option>
                      <option value="trudny">🔴 Trudny</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-slate-200 mb-2">
                      🎓 Poziom wiedzy
                    </label>
                    <select
                      value={editFormData.knowledge_level}
                      onChange={(e) => setEditFormData({ ...editFormData, knowledge_level: e.target.value })}
                      className="ui-select bg-white/80 dark:bg-slate-900/70"
                    >
                      <option value="elementary">🏫 Podstawówka</option>
                      <option value="high_school">🎓 Liceum</option>
                      <option value="university">🏛️ Studia</option>
                      <option value="expert">⭐ Ekspert</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end mt-6">
            <button
              onClick={handleSaveEdit}
              disabled={loading}
              className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 font-semibold disabled:opacity-50"
            >
              {loading ? 'Zapisywanie...' : '💾 Zapisz zmiany'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
