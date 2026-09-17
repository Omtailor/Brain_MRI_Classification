import UploadDropzone from './UploadDropzone';
import UploadOptions from './UploadOptions';
import AnalyzeButton from './AnalyzeButton';
import FilePreview from './FilePreview';
import FileError from './FileError';
import LoadingState from './LoadingState';
import ResultCard from './ResultCard';
import ErrorCard from './ErrorCard';
import './UploadCard.css';

/**
 * UploadCard
 * The main rounded card that contains the full upload flow:
 *   1. UploadDropzone  — drag-and-drop + choose file
 *   2. UploadOptions   — OR / Take a Photo / Choose from Gallery
 *   3. FilePreview     — shows selected file (Part 2)
 *   4. FileError       — shows validation errors (Part 2)
 *   5. AnalyzeButton   — disabled until file selected (Part 2+)
 *   6. LoadingState    — shows loading during analysis (Part 3)
 *   7. ResultCard      — shows analysis results (Part 3)
 *   8. ErrorCard       — shows analysis errors (Part 3)
 *
 * Props (wired up in Part 2+3):
 *   onChooseFile, onTakePhoto, onChooseGallery, onAnalyze, onRemoveFile, onDismissError,
 *   hasFile, isAnalyzing, selectedFile, previewUrl, fileError, isDragging,
 *   onDragOver, onDragLeave, onDrop, analysisResult, analysisError,
 *   onAnalyzeAnother, onRetry
 */
export default function UploadCard({
  onChooseFile,
  onTakePhoto,
  onChooseGallery,
  onAnalyze,
  onRemoveFile,
  onDismissError,
  hasFile = false,
  isAnalyzing = false,
  selectedFile,
  previewUrl,
  fileError,
  isDragging,
  onDragOver,
  onDragLeave,
  onDrop,
  analysisResult,
  analysisError,
  onAnalyzeAnother,
  onRetry,
}) {

  return (
    <section className="upload-card" aria-label="MRI upload section">
      <div className="upload-card__inner">
        {/* Loading State */}
        {isAnalyzing && <LoadingState />}

        {/* Analysis Result */}
        {!isAnalyzing && analysisResult && (
          <ResultCard
            result={analysisResult}
            onAnalyzeAnother={onAnalyzeAnother}
          />
        )}

        {/* Analysis Error */}
        {!isAnalyzing && analysisError && (
          <ErrorCard
            message={analysisError.message}
            isInvalidMRI={analysisError.isInvalidMRI}
            onRetry={onRetry}
            onChooseAnother={onAnalyzeAnother}
          />
        )}

        {/* Upload Flow (only show when not analyzing and no result/error) */}
        {!isAnalyzing && !analysisResult && !analysisError && (
          <>
            {!hasFile && (
              <>
                <UploadDropzone
                  onChooseFile={onChooseFile}
                  onDragOver={onDragOver}
                  onDragLeave={onDragLeave}
                  onDrop={onDrop}
                  isDragging={isDragging}
                />
                <UploadOptions
                  onTakePhoto={onTakePhoto}
                  onChooseGallery={onChooseGallery}
                />
              </>
            )}

            {hasFile && (
              <FilePreview
                file={selectedFile}
                previewUrl={previewUrl}
                onRemove={onRemoveFile}
                onChange={onChooseFile}
              />
            )}

            {fileError && (
              <FileError
                error={fileError}
                onDismiss={onDismissError || (() => {})}
              />
            )}

            <AnalyzeButton
              disabled={!hasFile}
              loading={isAnalyzing}
              onClick={onAnalyze}
            />
          </>
        )}
      </div>
    </section>
  );
}
