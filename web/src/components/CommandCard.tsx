import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { SearchResult } from '../api/types';
import { ConfidenceBadge } from './ConfidenceBadge';
import { RiskBadge } from './RiskBadge';
import { TechnologyBadge } from './TechnologyBadge';
import { CopyButton } from './CopyButton';
import { Explanation } from './Explanation';

interface CommandCardProps {
  result: SearchResult;
  rank?: number;
}

export const CommandCard: React.FC<CommandCardProps> = ({ result, rank }) => {
  const [showExplanation, setShowExplanation] = useState(false);

  return (
    <div
      className="rounded-lg p-6 transition-all hover:shadow-lg animate-fade-in"
      style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <TechnologyBadge technology={result.technology} />
        <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          › {result.category.replace(/_/g, ' ')}
        </span>
        <div className="ml-auto flex items-center gap-2">
          <ConfidenceBadge confidence={result.confidence} />
          <RiskBadge risk={result.risk} />
        </div>
      </div>

      {/* Name */}
      <h3 className="text-lg font-semibold mb-3">
        <Link
          to={`/commands/${result.technology}/${result.command_id}`}
          className="hover:underline"
          style={{ color: 'var(--text-primary)' }}
        >
          {result.name}
        </Link>
      </h3>

      {/* Command block */}
      <div className="command-block mb-3">
        <code className="font-mono text-sm" style={{ color: 'var(--accent)' }}>
          {result.command}
        </code>
        <div className="absolute top-2 right-2">
          <CopyButton text={result.command} />
        </div>
      </div>

      {/* Description */}
      <p className="text-sm mb-3" style={{ color: 'var(--text-secondary)' }}>
        {result.description.length > 200
          ? result.description.slice(0, 197) + '...'
          : result.description}
      </p>

      {/* Tags */}
      {result.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {result.tags.slice(0, 6).map((tag) => (
            <span
              key={tag}
              className="text-xs px-2 py-0.5 rounded-full"
              style={{ background: 'var(--bg-primary)', color: 'var(--text-secondary)', border: '1px solid var(--border)' }}
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Related commands */}
      {result.related_commands.length > 0 && (
        <details className="mb-2">
          <summary className="text-sm cursor-pointer" style={{ color: 'var(--text-secondary)' }}>
            Related commands ({result.related_commands.length})
          </summary>
          <ul className="mt-2 space-y-1 pl-4">
            {result.related_commands.map((cmd, i) => (
              <li key={i} className="font-mono text-xs" style={{ color: 'var(--text-secondary)' }}>
                {cmd}
              </li>
            ))}
          </ul>
        </details>
      )}

      {/* Explanation toggle */}
      {result.explanation && (
        <button
          onClick={() => setShowExplanation(!showExplanation)}
          className="text-xs mt-1"
          style={{ color: 'var(--accent)' }}
        >
          {showExplanation ? 'Hide' : 'Why this matched'}
        </button>
      )}

      {showExplanation && result.explanation && (
        <Explanation explanation={result.explanation} />
      )}

      {/* Documentation link */}
      {result.documentation_url && (
        <a
          href={result.documentation_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs block mt-2 hover:underline"
          style={{ color: 'var(--accent)' }}
        >
          Official Documentation →
        </a>
      )}
    </div>
  );
};
