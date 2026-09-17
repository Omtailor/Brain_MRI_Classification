import { CloudUpload } from 'lucide-react';
import './UploadDropzone.css';

/**
 * UploadDropzone
 * Presents the dashed drag-and-drop area with a cloud-upload icon,
 * instructional text, an "or" divider, and the Choose File button.
 *
 * Part 2 functionality:
 *   - onDragOver / onDragLeave / onDrop handlers
 *   - onChooseFile click
 *   - isDragging state for visual feedback
 */
export default function UploadDropzone({ 
  onChooseFile, 
  onDragOver, 
  onDragLeave, 
  onDrop, 
  isDragging 
}) {
  return (
    <div 
      className={`dropzone ${isDragging ? 'dropzone--dragging' : ''}`} 
      role="region" 
      aria-label="File upload area"
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      {/* Dashed border area */}
      <div className="dropzone__area">
        {/* Cloud upload icon */}
        <span className="dropzone__icon" aria-hidden="true">
          <CloudUpload size={52} strokeWidth={1.5} />
        </span>

        <p className="dropzone__primary-text">
          Drag &amp; drop a brain MRI image here
        </p>

        <span className="dropzone__or" aria-hidden="true">or</span>

        {/* Choose File button */}
        <button
          className="dropzone__choose-btn"
          type="button"
          onClick={onChooseFile}
          aria-label="Choose a file from your device"
        >
          Choose File
        </button>

        <p className="dropzone__hint">
          Supports: JPG, JPEG, PNG, PDF &bull; Max size: 20&nbsp;MB
        </p>
      </div>
    </div>
  );
}
