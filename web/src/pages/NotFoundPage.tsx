import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';

export const NotFoundPage: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>404 — AlchemyCLI AI</title>
      </Helmet>
      <div className="max-w-xl mx-auto px-4 py-24 text-center">
        <h1 className="text-6xl font-bold mb-4" style={{ color: 'var(--accent)' }}>404</h1>
        <p className="text-xl mb-8" style={{ color: 'var(--text-secondary)' }}>
          Page not found. Try searching for a command instead.
        </p>
        <Link
          to="/"
          className="inline-block px-6 py-3 rounded-lg font-semibold transition-colors"
          style={{ background: 'var(--accent)', color: '#fff' }}
        >
          Go Home
        </Link>
      </div>
    </>
  );
};
