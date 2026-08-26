import React, { useState, useRef, useEffect } from "react";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: (query: string) => void;
  isLoading: boolean;
  size?: "large" | "compact";
}

const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  onSearch,
  isLoading,
  size = "large",
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.key === "/" &&
        !isFocused &&
        document.activeElement?.tagName !== "INPUT" &&
        document.activeElement?.tagName !== "TEXTAREA"
      ) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isFocused]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      onSearch(value);
    }
  };

  const handleClear = () => {
    onChange("");
    inputRef.current?.focus();
  };

  const isLarge = size === "large";

  return (
    <div className="relative w-full">
      <div
        className={`relative flex items-center rounded-xl border transition-all duration-200 ${
          isLarge
            ? "border-gray-200 bg-white shadow-sm dark:border-navy-700 dark:bg-navy-800"
            : "border-gray-200 bg-white dark:border-navy-700 dark:bg-navy-800"
        } ${
          isFocused
            ? isLarge
              ? "border-brand-500 ring-4 ring-brand-500/20 dark:border-brand-400 dark:ring-brand-400/20 dark:shadow-[0_0_20px_rgba(6,182,212,0.15)]"
              : "border-brand-500 ring-2 ring-brand-500/20 dark:border-brand-400 dark:ring-brand-400/15"
            : "hover:border-gray-300 dark:hover:border-navy-600"
        }`}
      >
        {/* Search Icon */}
        <div
          className={`pointer-events-none flex items-center ${
            isLarge ? "pl-5" : "pl-3"
          }`}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className={`${
              isLarge ? "h-6 w-6" : "h-4 w-4"
            } text-gray-400 dark:text-navy-400`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        {/* Input */}
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder="What are you trying to do?"
          className={`w-full bg-transparent outline-none placeholder-gray-400 dark:placeholder-navy-400 text-gray-900 dark:text-white ${
            isLarge
              ? "px-4 py-5 text-lg font-medium"
              : "px-3 py-2.5 text-sm"
          }`}
          aria-label="Search commands"
        />

        {/* Right side controls */}
        <div
          className={`flex items-center gap-2 ${isLarge ? "pr-5" : "pr-3"}`}
        >
          {/* Spinner */}
          {isLoading && (
            <svg
              className={`animate-spin text-brand-500 dark:text-brand-400 ${
                isLarge ? "h-5 w-5" : "h-4 w-4"
              }`}
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          )}

          {/* Clear button */}
          {value && !isLoading && (
            <button
              onClick={handleClear}
              className={`rounded-lg p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:text-navy-400 dark:hover:bg-navy-700 dark:hover:text-gray-200 ${
                isLarge ? "" : "p-0.5"
              }`}
              aria-label="Clear search"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className={isLarge ? "h-5 w-5" : "h-4 w-4"}
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          )}

          {/* Keyboard shortcut hint (large mode only, when not focused and no value) */}
          {isLarge && !isFocused && !value && (
            <kbd className="hidden items-center rounded-md border border-gray-200 bg-gray-50 px-2 py-1 font-mono text-xs text-gray-400 dark:border-navy-600 dark:bg-navy-700 dark:text-navy-300 sm:inline-flex">
              /
            </kbd>
          )}
        </div>
      </div>
    </div>
  );
};

export { SearchBar };
export default SearchBar;
