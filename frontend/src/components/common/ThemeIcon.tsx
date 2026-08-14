
interface ThemeIconProps {
  darkMode: boolean;
  className?: string;
  size?: number;
}

export default function ThemeIcon({ darkMode, className = '', size = 20 }: ThemeIconProps) {
  if (darkMode) {
    // Sun Icon extracted from theme_icons.svg
    return (
      <svg
        className={`theme-svg-icon theme-sun-icon ${className}`}
        width={size}
        height={size}
        viewBox="0 0 309 309"
        fill="none"
        stroke="currentColor"
        strokeWidth="22"
        strokeLinecap="round"
        strokeMiterlimit="10"
        style={{ display: 'block', transition: 'transform 0.3s ease' }}
        aria-hidden="true"
      >
        <circle cx="154.5" cy="154.5" r="95" />
        <line x1="154.5" y1="301.5" x2="154.5" y2="264.5" />
        <line x1="154.5" y1="44.5" x2="154.5" y2="7.5" />
        <line x1="7.5" y1="154.5" x2="44.5" y2="154.5" />
        <line x1="264.5" y1="154.5" x2="301.5" y2="154.5" />
        <line x1="50.56" y1="258.44" x2="76.72" y2="232.28" />
        <line x1="232.28" y1="76.72" x2="258.44" y2="50.55" />
        <line x1="50.56" y1="50.55" x2="76.72" y2="76.72" />
        <line x1="232.28" y1="232.28" x2="258.44" y2="258.44" />
      </svg>
    );
  }

  // Moon Icon extracted from theme_icons.svg
  return (
    <svg
      className={`theme-svg-icon theme-moon-icon ${className}`}
      width={size}
      height={size}
      viewBox="0 0 309 265"
      fill="none"
      stroke="currentColor"
      strokeWidth="22"
      strokeLinecap="round"
      strokeMiterlimit="10"
      style={{ display: 'block', transition: 'transform 0.3s ease' }}
      aria-hidden="true"
    >
      <path d="M276.22,133.29c-2.14,65.32-55.74,117.61-121.57,117.67-67.04.06-121.98-54.92-121.87-121.96.11-65.91,52.59-119.54,118.05-121.5.1,0,.15.11.09.18-13.47,15.58-21.61,35.88-21.61,58.1,0,49.07,39.78,88.85,88.86,88.85,22.11,0,42.33-8.07,57.88-21.43.07-.06.19,0,.18.09Z" />
    </svg>
  );
}
