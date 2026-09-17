import { CheckCircle, RefreshCw } from 'lucide-react';
import ConfidenceBar from './ConfidenceBar';
import ProbabilityList from './ProbabilityList';
import ExplanationCard from './ExplanationCard';
import GradCamCard from './GradCamCard';
import './ResultCard.css';

/**
 * ResultCard
 * Displays the complete analysis result including prediction, confidence, probabilities, and explanation
 * @param {Object} result - The analysis result from the backend
 * @param {function} onAnalyzeAnother - Callback to analyze another MRI
 */
export default function ResultCard({ result, onAnalyzeAnother }) {
  if (!result || !result.prediction) {
    return null;
  }

  const { prediction, probabilities, explanation, grad_cam_image: gradCamImage } = result;

  return (
    <div className="result-card" role="region" aria-label="Analysis results">
      <div className="result-card__header">
        <div className="result-card__success-icon">
          <CheckCircle size={32} strokeWidth={2} aria-hidden="true" />
        </div>
        <h2 className="result-card__title">Analysis Complete</h2>
      </div>

      <div className="result-card__content">
        {/* Predicted Class */}
        <div className="result-card__prediction">
          <h3 className="result-card__prediction-label">Model Prediction</h3>
          <p className="result-card__prediction-value" aria-live="polite">
            {prediction.class_name}
          </p>
        </div>

        {/* Confidence Bar */}
        {prediction.confidence !== undefined && (
          <ConfidenceBar confidence={prediction.confidence} />
        )}

        {/* Probability List */}
        {probabilities && (
          <ProbabilityList probabilities={probabilities} />
        )}

        {/* Explanation */}
        {explanation && (
          <ExplanationCard explanation={explanation} />
        )}

        {result.valid_mri && <GradCamCard image={gradCamImage} />}
      </div>

      {/* Action Button */}
      <div className="result-card__actions">
        <button
          className="result-card__button"
          onClick={onAnalyzeAnother}
          type="button"
          aria-label="Analyze another MRI scan"
        >
          <RefreshCw size={16} strokeWidth={2} aria-hidden="true" />
          Analyze Another MRI
        </button>
      </div>
    </div>
  );
}
