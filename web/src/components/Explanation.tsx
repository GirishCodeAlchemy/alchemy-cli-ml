import React, { useState } from "react";

interface ExplanationData {
  technology_detected: string;
  intent_detected: string;
  matched_tags: string[];
  semantic_score: number;
  keyword_score: number;
}

interface ExplanationProps {
  explanation: ExplanationData;
}

const ScoreBar: React.FC<{ label: string; score: number }> = ({
  label,
  score,
}) => {
  const percentage = Math.round(score * 100);

  return (
    <div className="flex items-center gap-2">
      <span className="w-20 flex-shrink-0 text-xs text-gray-500 dark:text-gray-400">
        {label}
      </span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
        <div
          className="h-full rounded-full bg-cyan-500 transition-all duration-500 dark:bg-cyan-400"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="w-8 flex-shrink-0 text-right text-xs text-gray-500 dark:text-gray-400">
        {percentage}%
      </span>
    </div>
  );
};

const Explanation: React.FC<ExplanationProps> = ({ explanation }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="mt-2 border-t border-gray-100 pt-2 dark:border-gray-700/50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center gap-1 text-xs text-gray-400 transition-colors hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
      >
        {/* Chevron */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className={`h-3.5 w-3.5 transition-transform duration-200 ${
            isOpen ? "rotate-90" : "rotate-0"
          }`}
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
            clipRule="evenodd"
          />
        </svg>
        Why this matched
      </button>

      {isOpen && (
        <div className="mt-2 space-y-2.5 pl-5">
          {/* Technology detected */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Technology:
            </span>
            <span className="text-xs font-medium text-gray-700 dark:text-gray-200">
              {explanation.technology_detected}
            </span>
          </div>

          {/* Intent detected */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Intent:
            </span>
            <span className="text-xs font-medium text-gray-700 dark:text-gray-200">
              {explanation.intent_detected}
            </span>
          </div>

          {/* Matched tags */}
          {explanation.matched_tags.length > 0 && (
            <div>
              <span className="mb-1 block text-xs text-gray-500 dark:text-gray-400">
                Matched tags:
              </span>
              <div className="flex flex-wrap gap-1">
                {explanation.matched_tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded bg-gray-100 px-1.5 py-0.5 text-[0.65rem] text-gray-600 dark:bg-gray-700 dark:text-gray-300"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Score bars */}
          <div className="space-y-1.5">
            <ScoreBar label="Semantic" score={explanation.semantic_score} />
            <ScoreBar label="Keyword" score={explanation.keyword_score} />
          </div>
        </div>
      )}
    </div>
  );
};

export { Explanation };
export default Explanation;
