import { Sparkles } from 'lucide-react';
import './ExplanationCard.css';

/**
 * ExplanationCard
 * Displays the AI-generated explanation from Gemini
 * @param {string} explanation - The explanation text from the backend
 */
export default function ExplanationCard({ explanation }) {
  if (!explanation) {
    return null;
  }

  return (
    <div className="explanation-card" role="region" aria-label="AI analysis explanation">
      <div className="explanation-card__header">
        <Sparkles size={20} strokeWidth={2} className="explanation-card__icon" aria-hidden="true" />
        <h3 className="explanation-card__title">AI-generated Explanation</h3>
      </div>
      <div className="explanation-card__content">
        <p className="explanation-card__text" aria-live="polite">
          {explanation}
        </p>
      </div>
    </div>
  );
}
