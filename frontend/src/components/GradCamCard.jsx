import { ScanSearch } from 'lucide-react';
import './GradCamCard.css';

/**
 * Displays the model attention overlay returned for a verified brain MRI.
 */
export default function GradCamCard({ image }) {
  if (!image) {
    return null;
  }

  return (
    <section className="grad-cam-card" aria-label="Grad-CAM attention map">
      <div className="grad-cam-card__header">
        <ScanSearch size={20} strokeWidth={2} aria-hidden="true" />
        <h3>Model Attention Map</h3>
      </div>
      <img
        className="grad-cam-card__image"
        src={image}
        alt="Grad-CAM overlay showing the image regions that influenced the model prediction"
      />
      <p className="grad-cam-card__caption">
        Highlighted areas show regions that contributed to the model prediction.
        This visualization is informational and is not a medical diagnosis.
      </p>
    </section>
  );
}
