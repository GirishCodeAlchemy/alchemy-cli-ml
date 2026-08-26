import React from "react";
import { Link } from "react-router-dom";

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-gray-200 bg-gray-50 dark:border-navy-800 dark:bg-navy-950">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Top section: tagline and links */}
        <div className="flex flex-col items-center gap-6 sm:flex-row sm:justify-between">
          {/* Brand tagline */}
          <div className="text-center sm:text-left">
            <Link
              to="/"
              className="group inline-flex items-center gap-2 text-navy-900 transition-colors hover:text-brand-600 dark:text-white dark:hover:text-brand-400"
            >
              {/* Terminal icon */}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5 text-brand-500"
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
              <span className="text-sm font-semibold">
                Alchemy<span className="text-brand-500">CLI</span> AI
              </span>
            </Link>
            <p className="mt-1 text-xs text-gray-500 dark:text-navy-400">
              Ask your terminal. Find the right command.
            </p>
          </div>

          {/* Navigation links */}
          <nav className="flex items-center gap-6">
            <a
              href="https://github.com/GirishCodeAlchemy/alchemy-cli-ml"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-gray-500 transition-colors hover:text-brand-600 dark:text-navy-400 dark:hover:text-brand-400"
            >
              {/* GitHub icon */}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
              </svg>
              GitHub
            </a>
            <a
              href="#"
              className="text-sm text-gray-500 transition-colors hover:text-brand-600 dark:text-navy-400 dark:hover:text-brand-400"
            >
              Documentation
            </a>
            <a
              href="#"
              className="text-sm text-gray-500 transition-colors hover:text-brand-600 dark:text-navy-400 dark:hover:text-brand-400"
            >
              API Reference
            </a>
          </nav>
        </div>

        {/* Bottom section: version + copyright */}
        <div className="mt-6 flex flex-col items-center gap-2 border-t border-gray-200 pt-4 sm:flex-row sm:justify-between dark:border-navy-800">
          <p className="text-xs text-gray-400 dark:text-navy-500">
            v1.0.0
          </p>
          <p className="text-xs text-gray-400 dark:text-navy-500">
            &copy; {currentYear} AlchemyCLI AI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
