import './ConfidenceBar.css';

/**
 * ConfidenceBar
 * Displays model confidence as a percentage with a visual progress bar
 * @param {number} confidence - Confidence value between 0 and 1
 */
export default function ConfidenceBar({ confidence }) {
  const percentage = Math.round(confidence * 100);

  return (
    <div className="confidence-bar">
      <div className="confidence-bar__header">
        <span className="confidence-bar__label">Model Confidence</span>
        <span className="confidence-bar__value">{percentage}%</span>
      </div>
      <div className="confidence-bar__track">
        <div
          className="confidence-bar__fill"
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin="0"
          aria-valuemax="100"
          aria-label={`Model confidence: ${percentage}%`}
        />
      </div>
    </div>
  );
}
