import React from "react";

interface TechnologyBadgeProps {
  technology: string;
  className?: string;
}

interface TechStyle {
  colorClasses: string;
  icon: string;
}

const techMap: Record<string, TechStyle> = {
  kubernetes: {
    colorClasses: "bg-blue-500/15 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400",
    icon: "☸",
  },
  docker: {
    colorClasses: "bg-sky-500/15 text-sky-600 dark:bg-sky-500/20 dark:text-sky-400",
    icon: "🐳",
  },
  git: {
    colorClasses: "bg-orange-500/15 text-orange-600 dark:bg-orange-500/20 dark:text-orange-400",
    icon: "🔀",
  },
  linux: {
    colorClasses: "bg-green-500/15 text-green-600 dark:bg-green-500/20 dark:text-green-400",
    icon: "🐧",
  },
  python: {
    colorClasses: "bg-yellow-500/15 text-yellow-600 dark:bg-yellow-500/20 dark:text-yellow-400",
    icon: "🐍",
  },
  go: {
    colorClasses: "bg-cyan-500/15 text-cyan-600 dark:bg-cyan-500/20 dark:text-cyan-400",
    icon: "Go",
  },
  rust: {
    colorClasses: "bg-orange-500/15 text-orange-600 dark:bg-orange-500/20 dark:text-orange-400",
    icon: "🦀",
  },
  kafka: {
    colorClasses: "bg-red-500/15 text-red-600 dark:bg-red-500/20 dark:text-red-400",
    icon: "K",
  },
  terraform: {
    colorClasses: "bg-purple-500/15 text-purple-600 dark:bg-purple-500/20 dark:text-purple-400",
    icon: "🟪",
  },
};

const defaultStyle: TechStyle = {
  colorClasses: "bg-gray-500/15 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400",
  icon: "",
};

const TechnologyBadge: React.FC<TechnologyBadgeProps> = ({
  technology,
  className = "",
}) => {
  const key = technology.toLowerCase();
  const style = techMap[key] || defaultStyle;
  const icon = style.icon || technology.charAt(0).toUpperCase();

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${style.colorClasses} ${className}`}
    >
      <span className="text-[0.7rem]">{icon}</span>
      {technology}
    </span>
  );
};

export { TechnologyBadge };
export default TechnologyBadge;
