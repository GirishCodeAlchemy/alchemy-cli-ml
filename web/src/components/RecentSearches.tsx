import React from "react";

interface RecentSearchesProps {
  searches: string[];
  onSelect: (query: string) => void;
  onRemove: (query: string) => void;
  onClear: () => void;
}

const RecentSearches: React.FC<RecentSearchesProps> = ({
  searches,
  onSelect,
  onRemove,
  onClear,
}) => {
  if (searches.length === 0) {
    return null;
  }

  return (
    <div className="w-full">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
          Recent Searches
        </h3>
        <button
          onClick={onClear}
          className="text-xs text-gray-400 transition-colors hover:text-red-400 dark:text-gray-500 dark:hover:text-red-400"
        >
          Clear all
        </button>
      </div>
      <ul className="space-y-1">
        {searches.map((query) => (
          <li key={query} className="group flex items-center gap-2">
            {/* Clock icon */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4 flex-shrink-0 text-gray-400 dark:text-gray-500"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.828a1 1 0 101.415-1.414L11 9.586V6z"
                clipRule="evenodd"
              />
            </svg>

            <button
              onClick={() => onSelect(query)}
              className="flex-1 truncate text-left text-sm text-gray-600 transition-colors hover:text-cyan-600 dark:text-gray-300 dark:hover:text-cyan-400"
            >
              {query}
            </button>

            {/* Remove button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove(query);
              }}
              className="flex-shrink-0 text-gray-300 opacity-0 transition-all hover:text-red-400 group-hover:opacity-100 dark:text-gray-600 dark:hover:text-red-400"
              aria-label={`Remove "${query}" from recent searches`}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4"
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
          </li>
        ))}
      </ul>
    </div>
  );
};

export { RecentSearches };
export default RecentSearches;
