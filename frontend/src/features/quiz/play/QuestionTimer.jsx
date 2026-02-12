export default function QuestionTimer({ timeLeft }) {
  return (
    <div
      className={`text-3xl font-bold ${
        timeLeft <= 5 ? 'text-red-600 animate-pulse' : timeLeft <= 10 ? 'text-yellow-600' : 'text-green-600'
      }`}
    >
      ⏳ {timeLeft}s
    </div>
  );
}
