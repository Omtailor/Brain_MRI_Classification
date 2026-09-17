import { AlertCircle } from 'lucide-react';
import './FileError.css';

/**
 * FileError
 * Displays file validation errors with appropriate styling.
 * 
 * Props:
 *   - error: The error message string to display
 *   - onDismiss: Callback when user dismisses the error
 */
export default function FileError({ error, onDismiss }) {
  if (!error) return null;

  return (
    <div className="file-error" role="alert" aria-live="polite">
      <div className="file-error__content">
        <AlertCircle size={20} strokeWidth={2} className="file-error__icon" />
        <span className="file-error__message">{error}</span>
      </div>
      {onDismiss && (
        <button
          className="file-error__dismiss"
          type="button"
          onClick={() => onDismiss && onDismiss()}
          aria-label="Dismiss error"
        >
          ×
        </button>
      )}
    </div>
  );
}