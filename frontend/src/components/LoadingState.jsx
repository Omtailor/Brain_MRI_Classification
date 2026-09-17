import { Loader2 } from 'lucide-react';
import './LoadingState.css';

/**
 * LoadingState
 * Displays a polished loading state during MRI analysis
 */
export default function LoadingState() {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <div className="loading-state__spinner">
        <Loader2 size={48} strokeWidth={2} className="loading-state__icon" aria-hidden="true" />
      </div>
      <h2 className="loading-state__title">Analyzing MRI...</h2>
      <p className="loading-state__subtitle">
        Validating the image and generating AI-powered insights.
      </p>
    </div>
  );
}
