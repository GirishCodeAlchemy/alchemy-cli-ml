import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import ThemeToggle from "./ThemeToggle";

interface HeaderProps {
  isDark: boolean;
  onToggleTheme: () => void;
}

const Header: React.FC<HeaderProps> = ({ isDark, onToggleTheme }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const isHomePage = location.pathname === "/";
  const [headerQuery, setHeaderQuery] = useState("");

  const handleHeaderSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (headerQuery.trim()) {
      navigate(`/?q=${encodeURIComponent(headerQuery.trim())}`);
      setHeaderQuery("");
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-brand-500/20 bg-white/80 backdrop-blur-lg dark:bg-navy-950/80">
      {/* Brand gradient accent line */}
      <div className="h-0.5 bg-gradient-to-r from-brand-400 via-brand-500 to-brand-600" />

      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        {/* Left: Logo / Brand */}
        <Link
          to="/"
          className="group flex items-center gap-2 text-navy-900 transition-colors hover:text-brand-600 dark:text-white dark:hover:text-brand-400"
        >
          {/* Terminal icon */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-7 w-7 text-brand-500"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="4 17 10 11 4 5" />
            <line x1="12" y1="19" x2="20" y2="19" />
          </svg>
          {/* Full text on sm+, icon-only on mobile */}
          <span className="hidden text-lg font-bold tracking-tight sm:inline">
            Alchemy<span className="text-brand-500">CLI</span>
          </span>
        </Link>

        {/* Center: Compact search bar (hidden on homepage) */}
        {!isHomePage && (
          <form
            onSubmit={handleHeaderSearch}
            className="mx-4 hidden max-w-md flex-1 sm:block"
          >
            <div className="relative">
              {/* Search icon */}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400 dark:text-navy-400"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                type="text"
                value={headerQuery}
                onChange={(e) => setHeaderQuery(e.target.value)}
                placeholder="Search commands..."
                className="w-full rounded-lg border border-gray-200 bg-gray-50 py-1.5 pl-9 pr-3 text-sm text-navy-900 placeholder-gray-400 transition-colors focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-navy-700 dark:bg-navy-900 dark:text-gray-200 dark:placeholder-navy-400 dark:focus:border-brand-400 dark:focus:ring-brand-400"
              />
            </div>
          </form>
        )}

        {/* Right: Theme toggle + GitHub link */}
        <div className="flex items-center gap-2">
          {/* Mobile search button (navigates to homepage) */}
          {!isHomePage && (
            <Link
              to="/"
              className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-navy-900 sm:hidden dark:text-navy-400 dark:hover:bg-navy-800 dark:hover:text-white"
              aria-label="Search"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </Link>
          )}

          <ThemeToggle isDark={isDark} onToggle={onToggleTheme} />

          {/* GitHub link */}
          <a
            href="https://github.com/GirishCodeAlchemy/alchemy-cli-ml"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-navy-900 dark:text-navy-400 dark:hover:bg-navy-800 dark:hover:text-white"
            aria-label="View on GitHub"
          >
            {/* GitHub icon */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
            </svg>
          </a>
        </div>
      </div>
    </header>
  );
};

export default Header;
