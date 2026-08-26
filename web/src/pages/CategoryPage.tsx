import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { apiClient } from '../api/client';
import { CopyButton } from '../components/CopyButton';
import { RiskBadge } from '../components/RiskBadge';

interface CommandItem {
  id: string;
  name: string;
  command: string;
  category: string;
  risk: 'safe' | 'warning' | 'dangerous';
  description: string;
}

const TECH_ICONS: Record<string, string> = {
  kubernetes: '☸', docker: '🐳', git: '🔀', linux: '🐧',
  python: '🐍', go: '🔵', rust: '🦀', kafka: '📨', terraform: '🏗️',
};

export const CategoryPage: React.FC = () => {
  const { technology } = useParams<{ technology: string }>();
  const [commands, setCommands] = useState<CommandItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    if (!technology) return;
    apiClient
      .getCommands(technology)
      .then((cmds) => {
        setCommands(cmds as unknown as CommandItem[]);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [technology]);

  const filtered = filter
    ? commands.filter((c) =>
        c.name.toLowerCase().includes(filter.toLowerCase()) ||
        c.command.toLowerCase().includes(filter.toLowerCase()) ||
        c.category.toLowerCase().includes(filter.toLowerCase())
      )
    : commands;

  const categories = [...new Set(filtered.map((c) => c.category))].sort();

  if (!technology) return null;

  return (
    <>
      <Helmet>
        <title>{technology.charAt(0).toUpperCase() + technology.slice(1)} Commands — AlchemyCLI AI</title>
      </Helmet>

      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <nav className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
          <Link to="/" style={{ color: 'var(--accent)' }}>Home</Link> › {technology}
        </nav>

        <h1 className="text-3xl font-bold mb-2">
          {TECH_ICONS[technology] || '📦'} {technology.charAt(0).toUpperCase() + technology.slice(1)} Commands
        </h1>
        <p className="mb-6" style={{ color: 'var(--text-secondary)' }}>
          {commands.length} verified commands
        </p>

        {/* Filter */}
        <input
          type="text"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter commands..."
          className="w-full px-4 py-2 rounded-lg mb-8 outline-none focus:ring-2"
          style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
            color: 'var(--text-primary)',
          }}
        />

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="skeleton h-16 w-full" />
            ))}
          </div>
        ) : (
          categories.map((category) => {
            const catCommands = filtered.filter((c) => c.category === category);
            return (
              <div key={category} className="mb-8">
                <h2 className="text-lg font-semibold mb-3 capitalize" style={{ color: 'var(--accent)' }}>
                  {category.replace(/_/g, ' ')}
                </h2>
                <div className="space-y-2">
                  {catCommands.map((cmd) => (
                    <div
                      key={cmd.id}
                      className="flex items-center gap-4 p-3 rounded-lg hover:shadow transition-all"
                      style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
                    >
                      <div className="flex-1 min-w-0">
                        <Link
                          to={`/commands/${technology}/${cmd.id}`}
                          className="font-medium hover:underline block truncate"
                        >
                          {cmd.name}
                        </Link>
                        <code className="text-sm font-mono block truncate" style={{ color: 'var(--accent)' }}>
                          {cmd.command}
                        </code>
                      </div>
                      <RiskBadge risk={cmd.risk} />
                      <CopyButton text={cmd.command} />
                    </div>
                  ))}
                </div>
              </div>
            );
          })
        )}
      </div>
    </>
  );
};
