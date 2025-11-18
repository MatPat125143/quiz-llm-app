export default function Card({
  children,
  variant = 'default', // default, auth, stat, gradient
  className = '',
  gradient = 'from-blue-500 to-purple-600', // dla auth i gradient
  icon,
  title,
  ...props
}) {
  // Auth card - pełny ekran z gradientem w tle + biały box w środku
  if (variant === 'auth') {
    return (
      <div className={`min-h-screen flex items-center justify-center bg-gradient-to-br ${gradient} p-4`}>
        <div className={`bg-white p-8 rounded-2xl shadow-2xl w-full max-w-md ${className}`} {...props}>
          {children}
        </div>
      </div>
    );
  }

  // Stat card - małe karty ze statystykami
  if (variant === 'stat') {
    return (
      <div
        className={`bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all border border-gray-100 ${className}`}
        {...props}
      >
        {children}
      </div>
    );
  }

  // Gradient card - kolorowy gradient w tle
  if (variant === 'gradient') {
    return (
      <div
        className={`bg-gradient-to-r ${gradient} rounded-2xl p-8 text-white shadow-xl ${className}`}
        {...props}
      >
        {children}
      </div>
    );
  }

  // Default card - standardowy biały box z cieniem
  return (
    <div
      className={`bg-white rounded-2xl shadow-lg border border-gray-100 p-8 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

// Alert/Error Message Component (optional sub-component)
Card.Alert = function Alert({ children, type = 'error', className = '' }) {
  const typeStyles = {
    error: 'bg-red-100 border-red-400 text-red-700',
    success: 'bg-green-100 border-green-400 text-green-700',
    info: 'bg-blue-50 border-blue-500 text-blue-800',
  };

  return (
    <div className={`${typeStyles[type]} border px-4 py-3 rounded-xl ${className}`}>
      {children}
    </div>
  );
};