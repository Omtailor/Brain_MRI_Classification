import FeatureHighlights from './FeatureHighlights';
import brainImage from '../assets/brain.webp';
import './Hero.css';

/**
 * Hero
 * Two-column layout on desktop: text/features left, brain visual right.
 * Collapses to stacked layout on mobile (brain visual below heading).
 */
export default function Hero() {
  return (
    <section className="hero" aria-label="Hero">
      <div className="hero__inner container">
        {/* ── Left column: text content ── */}
        <div className="hero__content">
          {/* Small eyebrow label */}
          <p className="hero__eyebrow" aria-label="Tagline">
            AI FOR A HEALTHIER TOMORROW
          </p>

          {/* Main heading */}
          <h1 className="hero__heading">
            Understand<br />
            Your Brain Health<br />
            with <span className="hero__heading-accent">AI</span>
          </h1>

          {/* Supporting text */}
          <p className="hero__subtext">
            Upload a brain MRI and get AI-powered insights using advanced deep
            learning and Gemini. Fast, private and reliable.
          </p>

          {/* Feature highlights */}
          <FeatureHighlights />
        </div>

        {/* ── Right column: brain visual ── */}
        <div className="hero__visual" aria-hidden="true">
          <img className="hero__brain-image" src={brainImage} alt="" />
        </div>
      </div>
    </section>
  );
}
