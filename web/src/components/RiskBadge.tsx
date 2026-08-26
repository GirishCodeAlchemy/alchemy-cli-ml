import React from "react";

type RiskLevel = "safe" | "warning" | "dangerous";

interface RiskBadgeProps {
  risk: RiskLevel;
}

const ShieldIcon: React.FC = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="h-3.5 w-3.5"
    viewBox="0 0 20 20"
    fill="currentColor"
  >
    <path
      fillRule="evenodd"
      d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
      clipRule="evenodd"
    />
  </svg>
);

const WarningIcon: React.FC = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="h-3.5 w-3.5"
    viewBox="0 0 20 20"
    fill="currentColor"
  >
    <path
      fillRule="evenodd"
      d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
      clipRule="evenodd"
    />
  </svg>
);

const ExclamationIcon: React.FC = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="h-3.5 w-3.5"
    viewBox="0 0 20 20"
    fill="currentColor"
  >
    <path
      fillRule="evenodd"
      d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
      clipRule="evenodd"
    />
  </svg>
);

const riskConfig: Record<
  RiskLevel,
  { label: string; colorClasses: string; Icon: React.FC }
> = {
  safe: {
    label: "Safe",
    colorClasses:
      "bg-emerald-500/15 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400",
    Icon: ShieldIcon,
  },
  warning: {
    label: "Warning",
    colorClasses:
      "bg-amber-500/15 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400",
    Icon: WarningIcon,
  },
  dangerous: {
    label: "Dangerous",
    colorClasses:
      "bg-red-500/15 text-red-600 dark:bg-red-500/20 dark:text-red-400",
    Icon: ExclamationIcon,
  },
};

const RiskBadge: React.FC<RiskBadgeProps> = ({ risk }) => {
  const { label, colorClasses, Icon } = riskConfig[risk];

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${colorClasses}`}
    >
      <Icon />
      {label}
    </span>
  );
};

export { RiskBadge };
export default RiskBadge;
