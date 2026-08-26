import React from "react";

interface ConfidenceBadgeProps {
  confidence: number;
}

const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ confidence }) => {
  const percentage = Math.round(confidence * 100);

  let colorClasses: string;
  if (confidence >= 0.9) {
    colorClasses = "bg-emerald-500/15 text-emerald-500 dark:bg-emerald-500/20 dark:text-emerald-400";
  } else if (confidence >= 0.75) {
    colorClasses = "bg-amber-500/15 text-amber-500 dark:bg-amber-500/20 dark:text-amber-400";
  } else {
    colorClasses = "bg-orange-500/15 text-orange-500 dark:bg-orange-500/20 dark:text-orange-400";
  }

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colorClasses}`}
    >
      {percentage}%
    </span>
  );
};

export { ConfidenceBadge };
export default ConfidenceBadge;
