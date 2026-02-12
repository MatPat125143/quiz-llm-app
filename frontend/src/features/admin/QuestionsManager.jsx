import { useCallback, useEffect, useState } from 'react';
import {
  adminGetQuestions,
  adminGetQuestionDetail,
  adminUpdateQuestion,
  adminDeleteQuestion
} from '../../services/api';
import {
  getDifficultyBadgeClass,
  getDifficultyBadgeLabel,
  getKnowledgeBadgeClass,
  getKnowledgeBadgeLabel,
  formatDate
} from '../../services/helpers';
import LatexRenderer from '../../components/LatexRenderer';
import PaginationBar from '../../components/PaginationBar';
import QuestionsFilters from './questions/QuestionsFilters';
import QuestionEditModal from './questions/QuestionEditModal';

export default function QuestionsManager() {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterTopic, setFilterTopic] = useState('');
  const [filterDifficulty, setFilterDifficulty] = useState('');
  const [filterKnowledge, setFilterKnowledge] = useState('');
  const [filtersOpen, setFiltersOpen] = useState(false);

  const [editingQuestion, setEditingQuestion] = useState(null);
  const [editFormData, setEditFormData] = useState({});

  const loadQuestions = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page: currentPage,
        page_size: pageSize,
        ...(searchQuery && { search: searchQuery }),
        ...(filterTopic && { topic: filterTopic }),
        ...(filterDifficulty && { difficulty: filterDifficulty }),
        ...(filterKnowledge && { knowledge_level: filterKnowledge })
      };

      const data = await adminGetQuestions(params);
      setQuestions(Array.isArray(data?.questions) ? data.questions : []);
      setTotalPages(Number(data?.pagination?.total_pages || 1));
      setTotalCount(Number(data?.pagination?.total_count || data?.questions?.length || 0));
    } catch (err) {
      console.error('Error loading questions:', err);
      setError('Nie udało się załadować pytań.');
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, searchQuery, filterTopic, filterDifficulty, filterKnowledge]);

  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);


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

  const totalPagesSafe = Math.max(1, totalPages);
  const hasPrev = currentPage > 1;
  const hasNext = currentPage < totalPagesSafe;

  const toggleDifficulty = (value) => {
    setFilterDifficulty((prev) => (prev === value ? '' : value));
    setCurrentPage(1);
  };

  const toggleKnowledge = (value) => {
    setFilterKnowledge((prev) => (prev === value ? '' : value));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setSearchQuery('');
    setFilterTopic('');
    setFilterDifficulty('');
    setFilterKnowledge('');
    setCurrentPage(1);
  };

  const handleDelete = async (questionId) => {
    if (!window.confirm('Czy na pewno chcesz usunąć to pytanie?')) return;

    try {
      setLoading(true);
      await adminDeleteQuestion(questionId);
      setSuccess('🗑️ Pytanie zostało usunięte!');
      loadQuestions();
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
      {error && (
        <div className="bg-red-100 dark:bg-red-900/40 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded-xl">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-100 dark:bg-green-900/40 border border-green-400 dark:border-green-700 text-green-700 dark:text-green-200 px-4 py-3 rounded-xl">
          {success}
        </div>
      )}

      <QuestionsFilters
        filtersOpen={filtersOpen}
        setFiltersOpen={setFiltersOpen}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        filterTopic={filterTopic}
        setFilterTopic={setFilterTopic}
        setCurrentPage={setCurrentPage}
        filterDifficulty={filterDifficulty}
        toggleDifficulty={toggleDifficulty}
        filterKnowledge={filterKnowledge}
        toggleKnowledge={toggleKnowledge}
        clearFilters={clearFilters}
      />

      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-lg border border-gray-100 dark:border-slate-800 p-4 sm:p-6">
        <div className="mb-4 text-gray-700 dark:text-slate-200 font-medium">
          Znaleziono: <span className="text-indigo-600 font-bold">{totalCount}</span> pytań
        </div>

        <div className="space-y-4">
          {loading && (
            <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-md p-12 text-center text-gray-600 dark:text-slate-200">
              Ładowanie…
            </div>
          )}

          {!loading && questions.length === 0 && (
            <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-md p-12 text-center text-gray-500 dark:text-slate-300">
              Nie znaleziono pytań spełniających kryteria.
            </div>
          )}

          {!loading &&
            questions.map((question) => {
              const totalAnswers = Number(question.total_answers || 0);
              const correctAnswers = Number(question.correct_answers_count || 0);
              const wrongAnswers = Math.max(0, totalAnswers - correctAnswers);
              const timesUsed = Number(question.times_used || 0);

              return (
              <div
                key={question.id}
                className="group p-6 border-2 border-gray-100 dark:border-slate-800 rounded-xl hover:border-indigo-300 hover:shadow-lg transition-all bg-gradient-to-r from-white to-gray-50 dark:from-slate-900 dark:to-slate-800"
              >
                <div className="flex flex-col md:flex-row md:items-center gap-6">
                  <div className="flex-1">
                    <div className="mb-3">
                      <LatexRenderer
                        text={question.question_text}
                        className="text-lg font-bold text-gray-800 dark:text-slate-100 group-hover:text-indigo-600 transition-colors inline"
                        inline={true}
                      />
                    </div>

                    <div className="flex flex-wrap gap-3 mb-4">
                      <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getDifficultyBadgeClass(
                        question.difficulty_level
                      )}`}>
                        {getDifficultyBadgeLabel(question.difficulty_level)}
                      </span>

                      {question.knowledge_level && (
                        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getKnowledgeBadgeClass(
                          question.knowledge_level
                        )}`}>
                          {getKnowledgeBadgeLabel(question.knowledge_level)}
                        </span>
                      )}

                      <span className="px-3 py-1 bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-200 rounded-full text-sm font-semibold">
                        {question.topic || '-'}
                      </span>

                      {question.subtopic && (
                        <span className="px-3 py-1 bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200 rounded-full text-sm font-medium">
                          {question.subtopic}
                        </span>
                      )}

                      {question.created_at && (
                        <span className="px-3 py-1 bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200 rounded-full text-sm font-medium">
                          Utworzone: {formatDate(question.created_at)}
                        </span>
                      )}

                      {question.edited_at && (
                        <span className="px-3 py-1 bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200 rounded-full text-sm font-medium">
                          Modyfikacja: {formatDate(question.edited_at)}
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-2 mb-2">
                      <span className="px-3 py-1 rounded-full text-xs sm:text-sm font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-200">
                        Odpowiedzi: {totalAnswers}
                      </span>
                      <span className="px-3 py-1 rounded-full text-xs sm:text-sm font-semibold bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200">
                        Poprawne: {correctAnswers}
                      </span>
                      <span className="px-3 py-1 rounded-full text-xs sm:text-sm font-semibold bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200">
                        Niepoprawne: {wrongAnswers}
                      </span>
                      <span className="px-3 py-1 rounded-full text-xs sm:text-sm font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200">
                        Użycia: {timesUsed}
                      </span>
                    </div>
                  </div>

                  <div className="w-full md:w-[150px] lg:w-auto flex flex-col gap-2 md:self-center md:ml-auto lg:flex-row lg:flex-nowrap lg:justify-end">
                    <button
                      onClick={() => handleEdit(question)}
                      className="bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-400 text-white px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold flex items-center justify-center gap-1.5 min-h-[42px] w-full lg:w-[150px]"
                    >
                      ✏️ Edytuj
                    </button>
                    <button
                      onClick={() => handleDelete(question.id)}
                      className="bg-red-600 hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-400 text-white px-3 py-2 rounded-xl text-xs sm:text-sm font-semibold flex items-center justify-center gap-1.5 min-h-[42px] w-full lg:w-[150px]"
                    >
                      🗑️ Usuń
                    </button>
                  </div>
                </div>
              </div>
            );
            })}
        </div>

        {totalCount > 0 && (
          <PaginationBar
            page={currentPage}
            totalPages={totalPagesSafe}
            hasPrev={hasPrev}
            hasNext={hasNext}
            loading={loading}
            onPrev={() => setCurrentPage((p) => Math.max(1, p - 1))}
            onNext={() => setCurrentPage((p) => Math.min(totalPagesSafe, p + 1))}
            pageSize={pageSize}
            onPageSizeChange={(size) => {
              setPageSize(size);
              setCurrentPage(1);
            }}
          />
        )}
      </div>

      <QuestionEditModal
        editingQuestion={editingQuestion}
        setEditingQuestion={setEditingQuestion}
        editFormData={editFormData}
        setEditFormData={setEditFormData}
        loading={loading}
        handleSaveEdit={handleSaveEdit}
      />
    </div>
  );
}

