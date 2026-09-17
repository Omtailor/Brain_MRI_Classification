import { AlertCircle, RefreshCw } from 'lucide-react';
import './ErrorCard.css';

/**
 * ErrorCard
 * Displays analysis errors with appropriate actions
 * @param {string} message - The error message to display
 * @param {boolean} isInvalidMRI - Whether the error is due to invalid MRI validation
 * @param {function} onRetry - Callback for retry action
 * @param {function} onChooseAnother - Callback for choosing another file
 */
export default function ErrorCard({ message, isInvalidMRI = false, onRetry, onChooseAnother }) {
  return (
    <div className="error-card" role="alert" aria-live="assertive">
      <div className="error-card__icon">
        <AlertCircle size={32} strokeWidth={2} aria-hidden="true" />
      </div>
      <h3 className="error-card__title">
        {isInvalidMRI ? 'Invalid MRI' : 'Analysis Failed'}
      </h3>
      <p className="error-card__message">{message}</p>
      <div className="error-card__actions">
        {isInvalidMRI ? (
          <button
            className="error-card__button error-card__button--primary"
            onClick={onChooseAnother}
            type="button"
            aria-label="Choose another file to upload"
          >
            Choose Another File
          </button>
        ) : (
          <>
            <button
              className="error-card__button error-card__button--primary"
              onClick={onRetry}
              type="button"
              aria-label="Retry analysis"
            >
              <RefreshCw size={16} strokeWidth={2} aria-hidden="true" />
              Try Again
            </button>
            <button
              className="error-card__button error-card__button--secondary"
              onClick={onChooseAnother}
              type="button"
              aria-label="Choose another file to upload"
            >
              Choose Another File
            </button>
          </>
        )}
      </div>
    </div>
  );
}
