import { KNOWLEDGE_LEVELS, QUESTION_DIFFICULTY_LEVELS } from '../../../services/constants';
import { getDifficultyBadgeClass } from '../../../services/helpers';
import FiltersPanel from '../../../components/FiltersPanel';

export default function QuestionsFilters({
  filtersOpen,
  setFiltersOpen,
  searchQuery,
  setSearchQuery,
  filterTopic,
  setFilterTopic,
  setCurrentPage,
  filterDifficulty,
  toggleDifficulty,
  filterKnowledge,
  toggleKnowledge,
  clearFilters
}) {
  return (
    <FiltersPanel
      title="Filtry i sortowanie"
      icon=""
      isOpen={filtersOpen}
      onToggle={() => setFiltersOpen((prev) => !prev)}
      className="mb-2"
    >
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="md:col-span-2">
          <label className="block text-sm font-semibold text-gray-700 mb-2">Szukaj w treści pytania</label>
          <input
            type="text"
            placeholder="np. pochodna, trójkąt..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            className="ui-input"
          />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-semibold text-gray-700 mb-2">Temat</label>
          <input
            type="text"
            placeholder="np. Matematyka"
            value={filterTopic}
            onChange={(e) => {
              setFilterTopic(e.target.value);
              setCurrentPage(1);
            }}
            className="ui-input"
          />
        </div>

        <div className="md:col-span-4 mt-2">
          <label className="block text-sm font-semibold text-gray-700 mb-2">Poziom trudności</label>
          <div className="flex flex-wrap gap-2">
            {QUESTION_DIFFICULTY_LEVELS.map((opt) => {
              const active = filterDifficulty === opt.key;
              const base = getDifficultyBadgeClass(opt.key);
              return (
                <button
                  key={opt.key}
                  type="button"
                  onClick={() => toggleDifficulty(opt.key)}
                  className={`px-3 py-2 rounded-full border-2 text-sm font-semibold transition-all ${
                    active ? `${base} border-transparent shadow` : `${base} border-transparent opacity-80 hover:opacity-100`
                  }`}
                >
                  {opt.emoji} {opt.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="md:col-span-4 mt-2">
          <label className="block text-sm font-semibold text-gray-700 mb-2">Poziom wiedzy</label>
          <div className="flex flex-wrap gap-2 items-center">
            {KNOWLEDGE_LEVELS.map((opt) => {
              const active = filterKnowledge === opt.key;
              return (
                <button
                  key={opt.key}
                  type="button"
                  onClick={() => toggleKnowledge(opt.key)}
                  className={`px-3 py-2 rounded-full border-2 text-sm font-semibold transition-all ${
                    active
                      ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-indigo-600 shadow'
                      : 'bg-gray-100 text-gray-800 border-gray-300 hover:bg-gray-200 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700 dark:hover:bg-slate-700'
                  }`}
                >
                  {opt.emoji} {opt.label}
                </button>
              );
            })}

            <button
              type="button"
              onClick={clearFilters}
              className="ml-auto px-4 py-2 bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200 rounded-xl hover:bg-gray-200 dark:hover:bg-slate-700 transition font-semibold flex items-center gap-2"
            >
              🗑️ Wyczyść filtry
            </button>
          </div>
        </div>
      </div>
    </FiltersPanel>
  );
}
