import { Zap, ShieldCheck, BarChart2 } from 'lucide-react';
import './FeatureHighlights.css';

const FEATURES = [
  {
    icon: Zap,
    label: 'Fast Response',
    mobileLabel: 'Fast',
  },
  {
    icon: ShieldCheck,
    label: 'Privacy First',
    mobileLabel: 'Private',
  },
  {
    icon: BarChart2,
    label: 'Simple & Reliable',
    mobileLabel: 'Reliable',
  },
];

export default function FeatureHighlights() {
  return (
    <ul className="features" aria-label="Key features" role="list">
      {FEATURES.map(({ icon: Icon, label, mobileLabel }) => (
        <li key={label} className="features__item">
          <span className="features__icon-wrap" aria-hidden="true">
            <Icon size={16} strokeWidth={2.5} />
          </span>
          <span className="features__label">
            <span className="features__label--full">{label}</span>
            <span className="features__label--short">{mobileLabel}</span>
          </span>
        </li>
      ))}
    </ul>
  );
}
