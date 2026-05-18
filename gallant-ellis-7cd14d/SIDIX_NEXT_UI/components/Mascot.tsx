/**
 * Mascot SVG placeholder — sampai SDXL Option B mascot ready (4 state variants).
 * Versi: full body + icon (small avatar). Pakai brand colors.
 */

interface MascotProps {
  variant?: "fullbody" | "icon" | "small";
  className?: string;
}

export default function Mascot({ variant = "fullbody", className = "" }: MascotProps) {
  if (variant === "icon" || variant === "small") {
    const size = variant === "small" ? 40 : 56;
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        className={className}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <radialGradient id="mascot-icon-grad" cx="50%" cy="40%" r="60%">
            <stop offset="0%" stopColor="#FFFFFF" />
            <stop offset="60%" stopColor="#7C5CFF" />
            <stop offset="100%" stopColor="#080F1A" />
          </radialGradient>
        </defs>
        {/* Antlers */}
        <path d="M30 25 Q22 12 18 18 Q24 22 28 30 Z" fill="#FF6EC7" opacity="0.9" />
        <path d="M70 25 Q78 12 82 18 Q76 22 72 30 Z" fill="#FF6EC7" opacity="0.9" />
        {/* Head */}
        <circle cx="50" cy="55" r="32" fill="url(#mascot-icon-grad)" stroke="#7C5CFF" strokeWidth="2" />
        {/* Visor */}
        <ellipse cx="50" cy="52" rx="22" ry="14" fill="#0B0F2A" />
        {/* Eyes */}
        <circle cx="42" cy="52" r="3" fill="#00D2FF" />
        <circle cx="58" cy="52" r="3" fill="#00D2FF" />
        {/* Smile */}
        <path d="M42 62 Q50 68 58 62" stroke="#00D2FF" strokeWidth="2" fill="none" strokeLinecap="round" />
      </svg>
    );
  }

  // Full body
  return (
    <svg
      viewBox="0 0 200 280"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <radialGradient id="mascot-fb-grad" cx="50%" cy="35%" r="55%">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="55%" stopColor="#A78BFA" />
          <stop offset="100%" stopColor="#1E2340" />
        </radialGradient>
        <linearGradient id="mascot-body-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="100%" stopColor="#8B92B4" />
        </linearGradient>
      </defs>
      {/* Antlers */}
      <path
        d="M65 50 Q50 20 38 30 Q48 38 60 60 M62 55 Q50 35 42 42"
        stroke="#FF6EC7"
        strokeWidth="6"
        fill="none"
        strokeLinecap="round"
      />
      <path
        d="M135 50 Q150 20 162 30 Q152 38 140 60 M138 55 Q150 35 158 42"
        stroke="#FF6EC7"
        strokeWidth="6"
        fill="none"
        strokeLinecap="round"
      />
      {/* Head */}
      <ellipse cx="100" cy="80" rx="56" ry="50" fill="url(#mascot-fb-grad)" stroke="#7C5CFF" strokeWidth="2" />
      {/* Visor */}
      <ellipse cx="100" cy="78" rx="42" ry="26" fill="#0B0F2A" />
      {/* Eyes (winking) */}
      <circle cx="84" cy="78" r="5" fill="#00D2FF" />
      <path d="M110 78 Q116 76 122 78" stroke="#00D2FF" strokeWidth="3" fill="none" strokeLinecap="round" />
      {/* Smile */}
      <path d="M84 92 Q100 102 116 92" stroke="#00D2FF" strokeWidth="3" fill="none" strokeLinecap="round" />
      {/* S logo on forehead */}
      <text x="100" y="62" textAnchor="middle" fill="#7C5CFF" fontSize="16" fontWeight="bold" fontFamily="Space Grotesk">
        S
      </text>
      {/* Body */}
      <rect x="68" y="135" width="64" height="80" rx="20" fill="url(#mascot-body-grad)" stroke="#7C5CFF" strokeWidth="2" />
      {/* Chest S */}
      <text x="100" y="180" textAnchor="middle" fill="#FF6EC7" fontSize="22" fontWeight="bold" fontFamily="Space Grotesk">
        S
      </text>
      {/* Arms */}
      <ellipse cx="56" cy="160" rx="14" ry="22" fill="url(#mascot-body-grad)" stroke="#7C5CFF" strokeWidth="2" />
      <ellipse cx="144" cy="160" rx="14" ry="22" fill="url(#mascot-body-grad)" stroke="#7C5CFF" strokeWidth="2" />
      {/* Legs */}
      <rect x="78" y="215" width="18" height="40" rx="9" fill="url(#mascot-body-grad)" stroke="#7C5CFF" strokeWidth="2" />
      <rect x="104" y="215" width="18" height="40" rx="9" fill="url(#mascot-body-grad)" stroke="#7C5CFF" strokeWidth="2" />
    </svg>
  );
}
