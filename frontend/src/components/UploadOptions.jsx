import { Camera, Image } from 'lucide-react';
import './UploadOptions.css';

/**
 * UploadOption — single option tile (camera / gallery)
 * Part 2 will wire up onClick handlers.
 */
function UploadOption({ icon: Icon, title, subtitle, onClick, ariaLabel }) {
  return (
    <button
      className="upload-option"
      type="button"
      onClick={onClick}
      aria-label={ariaLabel}
    >
      <span className="upload-option__icon" aria-hidden="true">
        <Icon size={22} strokeWidth={1.8} />
      </span>
      <span className="upload-option__text">
        <span className="upload-option__title">{title}</span>
        <span className="upload-option__subtitle">{subtitle}</span>
      </span>
    </button>
  );
}

/**
 * UploadOptions
 * Renders the "OR" divider and the two alternate upload paths.
 */
export default function UploadOptions({ onTakePhoto, onChooseGallery }) {
  return (
    <div className="upload-options">
      {/* OR divider */}
      <div className="upload-options__divider" aria-hidden="true">
        <span className="upload-options__divider-line" />
        <span className="upload-options__divider-text">OR</span>
        <span className="upload-options__divider-line" />
      </div>

      {/* Option tiles */}
      <div className="upload-options__grid">
        <UploadOption
          icon={Camera}
          title="Take a Photo"
          subtitle="Use your camera"
          onClick={onTakePhoto}
          ariaLabel="Take a photo using your camera"
        />
        <UploadOption
          icon={Image}
          title="Choose from Gallery"
          subtitle="Select from your device"
          onClick={onChooseGallery}
          ariaLabel="Choose an image from your device gallery"
        />
      </div>
    </div>
  );
}
