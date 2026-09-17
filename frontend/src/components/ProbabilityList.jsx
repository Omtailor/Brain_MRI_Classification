import './ProbabilityList.css';

/**
 * ProbabilityList
 * Displays all class probabilities with visual progress bars
 * @param {Object} probabilities - Object with class names as keys and probabilities as values
 */
export default function ProbabilityList({ probabilities }) {
  if (!probabilities || typeof probabilities !== 'object') {
    return null;
  }

  const entries = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);

  return (
    <div className="probability-list">
      <h3 className="probability-list__title">Class Probabilities</h3>
      <div className="probability-list__items">
        {entries.map(([className, probability]) => {
          const percentage = Math.round(probability * 100);
          return (
            <div key={className} className="probability-item">
              <div className="probability-item__header">
                <span className="probability-item__label">{className}</span>
                <span className="probability-item__value">{percentage}%</span>
              </div>
              <div className="probability-item__track">
                <div
                  className="probability-item__fill"
                  style={{ width: `${percentage}%` }}
                  role="progressbar"
                  aria-valuenow={percentage}
                  aria-valuemin="0"
                  aria-valuemax="100"
                  aria-label={`${className}: ${percentage}%`}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
