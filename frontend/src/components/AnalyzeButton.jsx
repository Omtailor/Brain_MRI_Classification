import { ArrowRight } from 'lucide-react';
import './AnalyzeButton.css';

/**
 * AnalyzeButton
 * @param {boolean} disabled  - true when no file is selected (Part 1: always true)
 * @param {boolean} loading   - true while analysis is in progress (Part 2+)
 * @param {function} onClick  - handler (Part 2+)
 */
export default function AnalyzeButton({ disabled = true, loading = false, onClick }) {
  return (
    <button
      className={`analyze-btn ${disabled ? 'analyze-btn--disabled' : 'analyze-btn--active'} ${loading ? 'analyze-btn--loading' : ''}`}
      disabled={disabled || loading}
      onClick={onClick}
      aria-label="Analyze brain MRI scan"
      type="button"
    >
      <span className="analyze-btn__label">
        {loading ? 'Analyzing…' : 'Analyze'}
      </span>
      {!loading && <ArrowRight size={20} strokeWidth={2.5} className="analyze-btn__icon" />}
    </button>
  );
}
