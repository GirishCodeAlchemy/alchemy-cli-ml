import React from 'react';
import { SearchResult } from '../api/types';
import { ConfidenceBadge } from './ConfidenceBadge';
import { RiskBadge } from './RiskBadge';
import { TechnologyBadge } from './TechnologyBadge';
import { CopyButton } from './CopyButton';

interface CommandDetailProps {
  command: SearchResult & { aliases?: string[]; examples?: string[] };
}

export const CommandDetail: React.FC<CommandDetailProps> = ({ command }) => {
  return (
    <div className="max-w-3xl mx-auto animate-fade-in">
      {/* Breadcrumb */}
      <nav className="text-sm mb-6" style={{ color: 'var(--text-secondary)' }}>
        <a href="/" className="hover:underline" style={{ color: 'var(--accent)' }}>Home</a>
        {' › '}
        <a href={`/categories/${command.technology}`} className="hover:underline" style={{ color: 'var(--accent)' }}>
          {command.technology.charAt(0).toUpperCase() + command.technology.slice(1)}
        </a>
        {' › '}
        <span>{command.name}</span>
      </nav>

      {/* Header */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <TechnologyBadge technology={command.technology} />
        <span style={{ color: 'var(--text-secondary)' }}>›</span>
        <span style={{ color: 'var(--text-secondary)' }}>{command.category.replace(/_/g, ' ')}</span>
      </div>

      <h1 className="text-3xl font-bold mb-6">{command.name}</h1>

      {/* Command */}
      <div className="command-block mb-6 text-lg">
        <code className="font-mono" style={{ color: 'var(--accent)' }}>
          {command.command}
        </code>
        <div className="absolute top-3 right-3">
          <CopyButton text={command.command} size="lg" />
        </div>
      </div>

      {/* Description */}
      <p className="text-lg mb-6" style={{ color: 'var(--text-secondary)' }}>
        {command.description}
      </p>

      {/* Metadata */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 rounded-lg" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
          <span className="text-sm block mb-1" style={{ color: 'var(--text-secondary)' }}>Confidence</span>
          <ConfidenceBadge confidence={command.confidence} />
        </div>
        <div className="p-4 rounded-lg" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
          <span className="text-sm block mb-1" style={{ color: 'var(--text-secondary)' }}>Risk Level</span>
          <RiskBadge risk={command.risk} />
        </div>
      </div>

      {/* Tags */}
      {command.tags.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-secondary)' }}>Tags</h3>
          <div className="flex flex-wrap gap-2">
            {command.tags.map((tag) => (
              <span key={tag} className="text-sm px-3 py-1 rounded-full" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Related commands */}
      {command.related_commands.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-secondary)' }}>Related Commands</h3>
          <div className="space-y-2">
            {command.related_commands.map((cmd, i) => (
              <div key={i} className="command-block">
                <code className="font-mono text-sm" style={{ color: 'var(--text-secondary)' }}>{cmd}</code>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Documentation */}
      {command.documentation_url && (
        <div className="mt-6 p-4 rounded-lg" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
          <a
            href={command.documentation_url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold hover:underline"
            style={{ color: 'var(--accent)' }}
          >
            📖 Official Documentation →
          </a>
        </div>
      )}
    </div>
  );
};
