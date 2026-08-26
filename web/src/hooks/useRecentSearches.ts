import { useState, useCallback } from 'react';

const STORAGE_KEY = 'alchemy-recent-searches';
const MAX_RECENT = 10;

interface UseRecentSearchesReturn {
  recentSearches: string[];
  addSearch: (query: string) => void;
  removeSearch: (query: string) => void;
  clearSearches: () => void;
}

function loadSearches(): string[] {
  if (typeof window === 'undefined') return [];
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    const parsed = JSON.parse(stored);
    if (Array.isArray(parsed)) {
      return parsed.filter((item): item is string => typeof item === 'string');
    }
    return [];
  } catch {
    return [];
  }
}

function saveSearches(searches: string[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(searches));
}

export function useRecentSearches(): UseRecentSearchesReturn {
  const [recentSearches, setRecentSearches] = useState<string[]>(loadSearches);

  const addSearch = useCallback((query: string) => {
    const trimmed = query.trim();
    if (!trimmed) return;

    setRecentSearches((prev) => {
      // Remove duplicate if it already exists
      const filtered = prev.filter((item) => item !== trimmed);
      // Add to front and trim to max
      const updated = [trimmed, ...filtered].slice(0, MAX_RECENT);
      saveSearches(updated);
      return updated;
    });
  }, []);

  const removeSearch = useCallback((query: string) => {
    setRecentSearches((prev) => {
      const updated = prev.filter((item) => item !== query);
      saveSearches(updated);
      return updated;
    });
  }, []);

  const clearSearches = useCallback(() => {
    setRecentSearches([]);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return { recentSearches, addSearch, removeSearch, clearSearches };
}
