import { X, FileImage, FileText } from 'lucide-react';
import './FilePreview.css';

/**
 * FilePreview
 * Displays the selected file preview (image or PDF) with remove/change options.
 * 
 * Props:
 *   - file: The selected File object
 *   - previewUrl: The URL for previewing the file
 *   - onRemove: Callback when user removes the file
 *   - onChange: Callback when user wants to change the file
 */
export default function FilePreview({ file, previewUrl, onRemove, onChange }) {
  if (!file || !previewUrl) return null;

  const isImage = file.type.startsWith('image/');
  const isPdf = file.type === 'application/pdf';

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="file-preview" role="region" aria-label="File preview">
      <div className="file-preview__container">
        {/* Remove button */}
        <button
          className="file-preview__remove"
          type="button"
          onClick={onRemove}
          aria-label="Remove file"
        >
          <X size={20} strokeWidth={2} />
        </button>

        {/* Preview content */}
        <div className="file-preview__content">
          {isImage && (
            <img
              src={previewUrl}
              alt="Selected MRI scan preview"
              className="file-preview__image"
            />
          )}
          
          {isPdf && (
            <div className="file-preview__pdf">
              <div className="file-preview__pdf-icon">
                <FileText size={48} strokeWidth={1.5} />
              </div>
              <div className="file-preview__pdf-info">
                <p className="file-preview__pdf-label">PDF Document</p>
                <p className="file-preview__pdf-name">{file.name}</p>
              </div>
            </div>
          )}
        </div>

        {/* File info and actions */}
        <div className="file-preview__info">
          <div className="file-preview__details">
            <div className="file-preview__name">
              {isImage && <FileImage size={16} strokeWidth={2} />}
              {isPdf && <FileText size={16} strokeWidth={2} />}
              <span>{file.name}</span>
            </div>
            <div className="file-preview__size">
              {formatFileSize(file.size)}
            </div>
          </div>
          
          <button
            className="file-preview__change"
            type="button"
            onClick={onChange}
            aria-label="Change file"
          >
            Change File
          </button>
        </div>
      </div>
    </div>
  );
}