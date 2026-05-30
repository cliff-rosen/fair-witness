import { scoreColor } from '../lib/ui'

interface Props {
  score: number
  size?: number
  label?: string
}

/** Circular SVG gauge for an overall fairness score (0-100). */
export default function ScoreGauge({ score, size = 160, label }: Props) {
  const stroke = 12
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - Math.max(0, Math.min(100, score)) / 100)
  const color = scoreColor(score)

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
      </svg>
      <div
        className="flex flex-col items-center"
        style={{ marginTop: -size / 2 - 24, height: size / 2 }}
      >
        <span className="text-4xl font-bold" style={{ color }}>
          {score}
        </span>
        <span className="text-xs uppercase tracking-wide text-slate-400">/ 100</span>
      </div>
      {label && (
        <span className="mt-2 text-sm font-semibold" style={{ color }}>
          {label}
        </span>
      )}
    </div>
  )
}
