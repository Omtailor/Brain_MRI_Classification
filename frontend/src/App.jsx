import { useState, useEffect, useRef } from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import UploadCard from './components/UploadCard';
import { analyzeMRI } from './services/api';
import './styles/global.css';
import './App.css';

/**
 * App — root component
 *
 * Manages:
 *  - dark theme state
 *  - file upload state and handlers (Part 2)
 *  - API integration and analysis state (Part 3)
 *
 * Props passed down to children for Part 2+3 expansion:
 *  - UploadCard receives real file handlers and analysis state
 */
export default function App() {
  /* ── Theme ─────────────────────────────────────────────── */
  const theme = 'dark';

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'dark');
  }, []);

  /* ── File Upload State (Part 2+3) ─────────────────────────────────────────────── */
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [fileError, setFileError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError] = useState(null);
  
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const galleryInputRef = useRef(null);

  // File validation constants
  const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20 MB in bytes
  const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
  const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf'];

  // Validate file type and size
  const validateFile = (file) => {
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return 'File size exceeds 20 MB limit';
    }

    // Check file type
    if (!ALLOWED_TYPES.includes(file.type)) {
      return 'Invalid file type. Only JPG, JPEG, PNG, and PDF files are allowed';
    }

    // Check file extension as additional validation
    const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
    if (!ALLOWED_EXTENSIONS.includes(fileExtension)) {
      return 'Invalid file extension. Only .jpg, .jpeg, .png, and .pdf files are allowed';
    }

    return null; // No error
  };

  // Create preview URL for file
  const createPreviewUrl = (file) => {
    if (file.type.startsWith('image/')) {
      return URL.createObjectURL(file);
    } else if (file.type === 'application/pdf') {
      return URL.createObjectURL(file);
    }
    return null;
  };

  // Handle file selection
  const handleFileSelect = (file) => {
    setFileError(null);
    setAnalysisResult(null);
    setAnalysisError(null);

    const error = validateFile(file);
    if (error) {
      setFileError(error);
      return;
    }

    // Revoke previous object URL to free memory
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setSelectedFile(file);
    const url = createPreviewUrl(file);
    setPreviewUrl(url);
  };

  // Handle file input change
  const handleFileInputChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      handleFileSelect(file);
    }
    // Reset input value to allow selecting the same file again
    event.target.value = '';
  };

  // Handle drag and drop
  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);

    const file = event.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  // Handle file removal
  const handleRemoveFile = () => {
    // Revoke object URL to free memory
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setFileError(null);
    setAnalysisResult(null);
    setAnalysisError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (cameraInputRef.current) {
      cameraInputRef.current.value = '';
    }
    if (galleryInputRef.current) {
      galleryInputRef.current.value = '';
    }
  };

  // Handle error dismissal
  const handleDismissError = () => {
    setFileError(null);
  };

  // Handle choose file button click
  const handleChooseFile = () => {
    fileInputRef.current?.click();
  };

  // Handle take photo button click
  const handleTakePhoto = () => {
    cameraInputRef.current?.click();
  };

  // Handle choose from gallery button click
  const handleChooseGallery = () => {
    galleryInputRef.current?.click();
  };

  // Handle analyze button click (Part 3: Real API integration)
  const handleAnalyze = async () => {
    if (!selectedFile) return;

    // Prevent duplicate submission
    if (isAnalyzing) return;

    setIsAnalyzing(true);
    setAnalysisError(null);
    setAnalysisResult(null);

    try {
      const result = await analyzeMRI(selectedFile);

      if (result.success === false && result.valid_mri === false) {
        setAnalysisError({
          message: result.message || 'This image does not appear to be a brain MRI. Please upload a valid brain MRI image.',
          isInvalidMRI: true,
        });
        return;
      }

      // Validate response structure
      if (!result.success) {
        throw new Error(result.message || 'Analysis failed');
      }

      // Handle invalid MRI case
      if (!result.valid_mri) {
        setAnalysisError({
          message: result.message || 'This image does not appear to be a brain MRI. Please upload a valid brain MRI image.',
          isInvalidMRI: true,
        });
        return;
      }

      // Validate required fields
      if (!result.prediction || !result.probabilities || !result.explanation) {
        throw new Error('Invalid response format from server');
      }

      setAnalysisResult(result);
    } catch (error) {
      setAnalysisError({
        message: error.message || 'Something went wrong while analyzing the MRI. Please try again.',
        isInvalidMRI: false,
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Handle analyze another MRI
  const handleAnalyzeAnother = () => {
    // Revoke object URL to free memory
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setFileError(null);
    setAnalysisResult(null);
    setAnalysisError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (cameraInputRef.current) {
      cameraInputRef.current.value = '';
    }
    if (galleryInputRef.current) {
      galleryInputRef.current.value = '';
    }
  };

  // Handle retry analysis
  const handleRetry = () => {
    handleAnalyze();
  };



  // Cleanup preview URL on unmount
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  /* ── Render ─────────────────────────────────────────────── */
  return (
    <div className="app" data-theme={theme}>
      <Header />

      <main className="main" id="main-content">
        {/* Hero + brain visual */}
        <Hero />

        {/* Upload section */}
        <section className="upload-section">
          <div className="container">
            {/* Hidden file inputs */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".jpg,.jpeg,.png,.pdf"
              onChange={handleFileInputChange}
              style={{ display: 'none' }}
              aria-hidden="true"
            />
            <input
              ref={cameraInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleFileInputChange}
              style={{ display: 'none' }}
              aria-hidden="true"
            />
            <input
              ref={galleryInputRef}
              type="file"
              accept="image/*,.pdf"
              onChange={handleFileInputChange}
              style={{ display: 'none' }}
              aria-hidden="true"
            />

            <UploadCard
              onChooseFile={handleChooseFile}
              onTakePhoto={handleTakePhoto}
              onChooseGallery={handleChooseGallery}
              onAnalyze={handleAnalyze}
              onRemoveFile={handleRemoveFile}
              onDismissError={handleDismissError}
              hasFile={!!selectedFile}
              isAnalyzing={isAnalyzing}
              selectedFile={selectedFile}
              previewUrl={previewUrl}
              fileError={fileError}
              isDragging={isDragging}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              analysisResult={analysisResult}
              analysisError={analysisError}
              onAnalyzeAnother={handleAnalyzeAnother}
              onRetry={handleRetry}
            />
          </div>
        </section>
      </main>
    </div>
  );
}
