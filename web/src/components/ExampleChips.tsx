import React from "react";

interface ExampleChipsProps {
  onSelect: (query: string) => void;
}

const EXAMPLE_QUERIES = [
  "find pods using the most memory",
  "undo my last git commit",
  "find process using port 8080",
  "show kafka consumer lag",
  "list docker containers by size",
  "check terraform plan diff",
  "search git log by author",
  "find largest files in directory",
];

const ExampleChips: React.FC<ExampleChipsProps> = ({ onSelect }) => {
  return (
    <div className="flex flex-wrap justify-center gap-2">
      {EXAMPLE_QUERIES.map((query) => (
        <button
          key={query}
          onClick={() => onSelect(query)}
          className="rounded-full border border-gray-200 bg-white px-3.5 py-1.5 text-sm text-gray-600 transition-all hover:border-cyan-400 hover:bg-cyan-50 hover:text-cyan-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-cyan-500 dark:hover:bg-cyan-950/40 dark:hover:text-cyan-400"
        >
          {query}
        </button>
      ))}
    </div>
  );
};

export { ExampleChips };
export default ExampleChips;
