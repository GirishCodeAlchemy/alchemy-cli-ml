import React from 'react';
import { SearchResult } from '../api/types';
import { CommandCard } from './CommandCard';

interface SearchResultsProps {
  results: SearchResult[];
  isLoading: boolean;
  query: string;
}

export const SearchResults: React.FC<SearchResultsProps> = ({ results, isLoading, query }) => {
  if (isLoading) {
    return (
      <div className="space-y-4 mt-8 animate-fade-in">
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg p-6" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            <div className="skeleton h-4 w-32 mb-3" />
            <div className="skeleton h-6 w-64 mb-4" />
            <div className="skeleton h-12 w-full mb-3" />
            <div className="skeleton h-3 w-48" />
          </div>
        ))}
      </div>
    );
  }

  if (!query) return null;

  if (results.length === 0) {
    return (
      <div className="text-center py-12 mt-8 animate-fade-in">
        <p className="text-xl mb-2" style={{ color: 'var(--text-secondary)' }}>No results found</p>
        <p style={{ color: 'var(--text-secondary)' }}>Try rephrasing your question or specifying a technology.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 mt-8 animate-fade-in">
      <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
        {results.length} result{results.length !== 1 ? 's' : ''} for "{query}"
      </p>
      {results.map((result, index) => (
        <CommandCard key={result.command_id} result={result} rank={index + 1} />
      ))}
    </div>
  );
};
