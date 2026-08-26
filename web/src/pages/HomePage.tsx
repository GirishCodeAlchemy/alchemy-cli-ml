import React, { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { SearchBar } from '../components/SearchBar';
import { SearchResults } from '../components/SearchResults';
import { ExampleChips } from '../components/ExampleChips';
import { RecentSearches } from '../components/RecentSearches';
import { CategoryCard } from '../components/CategoryCard';
import { useSearch } from '../hooks/useSearch';
import { useRecentSearches } from '../hooks/useRecentSearches';
import { apiClient } from '../api/client';

export const HomePage: React.FC = () => {
  const { results, isLoading, query, search } = useSearch();
  const { recentSearches, addSearch, removeSearch, clearSearches } = useRecentSearches();
  const [technologies, setTechnologies] = useState<Record<string, number>>({});
  const [searchValue, setSearchValue] = useState('');

  useEffect(() => {
    apiClient.getTechnologies().then(setTechnologies).catch(() => {});
  }, []);

  const handleSearch = (q: string) => {
    search(q);
    addSearch(q);
    setSearchValue(q);
  };

  return (
    <>
      <Helmet>
        <title>AlchemyCLI AI — Ask your terminal. Find the right command.</title>
        <meta name="description" content="Developer command search engine. Ask natural language questions, get verified shell commands." />
      </Helmet>

      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Hero */}
        {!query && (
          <div className="text-center mb-12 animate-fade-in">
            <h1 className="text-5xl font-bold mb-4">
              <span style={{ color: 'var(--accent)' }}>AlchemyCLI</span> AI
            </h1>
            <p className="text-xl mb-8" style={{ color: 'var(--text-secondary)' }}>
              Ask your terminal. Find the right command.
            </p>
          </div>
        )}

        {/* Search */}
        <SearchBar
          value={searchValue}
          onChange={setSearchValue}
          onSearch={handleSearch}
          isLoading={isLoading}
        />

        {/* Example chips */}
        {!query && (
          <div className="mt-6">
            <ExampleChips onSelect={handleSearch} />
          </div>
        )}

        {/* Recent searches */}
        {!query && recentSearches.length > 0 && (
          <div className="mt-6">
            <RecentSearches
              searches={recentSearches}
              onSelect={handleSearch}
              onRemove={removeSearch}
              onClear={clearSearches}
            />
          </div>
        )}

        {/* Results */}
        <SearchResults results={results} isLoading={isLoading} query={query} />

        {/* Technology categories */}
        {!query && Object.keys(technologies).length > 0 && (
          <div className="mt-16">
            <h2 className="text-2xl font-bold mb-6 text-center">Browse by Technology</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(technologies).map(([tech, count]) => (
                <CategoryCard key={tech} technology={tech} commandCount={count} />
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
};
