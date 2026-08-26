import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { CommandDetail } from '../components/CommandDetail';
import { apiClient } from '../api/client';
import { SearchResult } from '../api/types';

export const CommandPage: React.FC = () => {
  const { technology, id } = useParams<{ technology: string; id: string }>();
  const [command, setCommand] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    apiClient
      .getCommand(id)
      .then((cmd) => {
        setCommand(cmd as unknown as SearchResult);
        setLoading(false);
      })
      .catch((err) => {
        setError('Command not found');
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12">
        <div className="skeleton h-8 w-48 mb-4" />
        <div className="skeleton h-12 w-full mb-4" />
        <div className="skeleton h-24 w-full mb-4" />
        <div className="skeleton h-4 w-64" />
      </div>
    );
  }

  if (error || !command) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 text-center">
        <h1 className="text-2xl font-bold mb-4">Command Not Found</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          The command you're looking for doesn't exist.
        </p>
        <a href="/" className="mt-4 inline-block" style={{ color: 'var(--accent)' }}>
          ← Back to search
        </a>
      </div>
    );
  }

  return (
    <>
      <Helmet>
        <title>{command.name} — AlchemyCLI AI</title>
        <meta name="description" content={`${command.name}: ${command.command}`} />
      </Helmet>
      <div className="px-4 py-12">
        <CommandDetail command={command} />
      </div>
    </>
  );
};
