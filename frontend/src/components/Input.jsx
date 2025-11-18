export default function Input({
  label,
  type = 'text',
  name,
  value,
  onChange,
  placeholder,
  required = false,
  disabled = false,
  minLength,
  helpText,
  focusColor = 'blue', // blue, purple, indigo
  className = '',
  ...props
}) {
  const focusColorMap = {
    blue: 'focus:border-blue-500',
    purple: 'focus:border-purple-500',
    indigo: 'focus:border-indigo-500',
  };

  return (
    <div className={className}>
      {label && (
        <label className="block text-gray-700 font-semibold mb-2">
          {label}
        </label>
      )}
      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        minLength={minLength}
        className={`w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none ${focusColorMap[focusColor]} transition-all`}
        {...props}
      />
      {helpText && (
        <p className="text-xs text-gray-500 mt-1">
          {helpText}
        </p>
      )}
    </div>
  );
}