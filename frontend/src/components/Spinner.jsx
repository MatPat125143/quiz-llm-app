export default function Spinner({
  size = 'medium', // small, medium, large
  text,
  subtext,
  overlay = false,
  showPulsingDots = false,
  pulsingSteps = []
}) {
  // Size mappings
  const sizeMap = {
    small: 'w-8 h-8 border-2',
    medium: 'w-16 h-16 border-4',
    large: 'w-20 h-20 border-4'
  };

  const spinnerSize = sizeMap[size] || sizeMap.medium;

  // Pulsing dots component (used in QuizSetup and QuestionDisplay)
  const PulsingDots = () => (
    <div className="mt-6 space-y-2">
      {pulsingSteps.map((step, index) => (
        <div key={index} className="flex items-center justify-center gap-2 text-sm text-gray-500">
          <div
            className={`w-2 h-2 rounded-full animate-pulse ${
              index === 0 ? 'bg-blue-500' : 
              index === 1 ? 'bg-purple-500' : 
              'bg-pink-500'
            }`}
            style={{ animationDelay: `${index * 100}ms` }}
          ></div>
          <span>{step}</span>
        </div>
      ))}
    </div>
  );

  // Overlay variant (full screen with white box)
  if (overlay) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600">
        <div className="bg-white p-12 rounded-2xl shadow-2xl text-center max-w-md">
          <div className={`animate-spin rounded-full ${spinnerSize} border-blue-600 border-t-transparent mx-auto mb-6`}></div>
          {text && (
            <h2 className="text-2xl font-bold text-gray-800 mb-3">
              {text}
            </h2>
          )}
          {subtext && (
            <p className="text-gray-600 mb-4">
              {subtext}
            </p>
          )}
          {showPulsingDots && pulsingSteps.length > 0 && <PulsingDots />}
        </div>
      </div>
    );
  }

  // Inline variant (simple spinner with text)
  return (
    <div className="flex items-center justify-center">
      <div className="text-center">
        <div className={`${spinnerSize} border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4`}></div>
        {text && <p className="text-lg text-gray-600 font-medium">{text}</p>}
      </div>
    </div>
  );
}