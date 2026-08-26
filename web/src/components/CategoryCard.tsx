import React from 'react';
import { Link } from 'react-router-dom';

const TECH_ICONS: Record<string, string> = {
  kubernetes: '☸',
  docker: '🐳',
  git: '🔀',
  linux: '🐧',
  python: '🐍',
  go: '🔵',
  rust: '🦀',
  kafka: '📨',
  terraform: '🏗️',
};

const TECH_DESCRIPTIONS: Record<string, string> = {
  kubernetes: 'Container orchestration, pods, deployments, services',
  docker: 'Containers, images, compose, volumes, networks',
  git: 'Version control, branches, commits, merges',
  linux: 'System admin, processes, files, networking',
  python: 'Package management, virtual environments, testing',
  go: 'Build, test, modules, formatting',
  rust: 'Cargo, build, test, clippy, rustup',
  kafka: 'Topics, consumer groups, offsets, lag',
  terraform: 'Infrastructure as code, state, plan, apply',
};

interface CategoryCardProps {
  technology: string;
  commandCount: number;
}

export const CategoryCard: React.FC<CategoryCardProps> = ({ technology, commandCount }) => {
  const icon = TECH_ICONS[technology] || '📦';
  const description = TECH_DESCRIPTIONS[technology] || '';

  return (
    <Link
      to={`/categories/${technology}`}
      className="block rounded-lg p-5 transition-all hover:shadow-lg hover:-translate-y-0.5"
      style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
    >
      <div className="text-3xl mb-2">{icon}</div>
      <h3 className="font-semibold text-lg capitalize mb-1">{technology}</h3>
      <p className="text-sm mb-2" style={{ color: 'var(--text-secondary)' }}>{description}</p>
      <span className="text-xs" style={{ color: 'var(--accent)' }}>{commandCount} commands</span>
    </Link>
  );
};
