# BrainScan AI Frontend

Brain MRI analysis application with AI-powered insights using deep learning and Gemini.

## Features

- **File Upload**: Drag & drop, file picker, camera, and gallery support
- **File Validation**: Supports JPG, JPEG, PNG, PDF (max 20MB)
- **Real-time Preview**: Image and PDF preview with file information
- **AI Analysis**: Integration with FastAPI backend for MRI classification
- **Results Display**: Model prediction, confidence, class probabilities, and AI-generated explanations
- **Responsive Design**: Works seamlessly on mobile (320px+) to desktop (1920px+)
- **Theme Support**: Light and dark mode with localStorage persistence
- **Accessibility**: ARIA labels, keyboard navigation, and screen reader support

## Prerequisites

- Node.js 18+ and npm
- FastAPI backend running on configured URL

## Setup

1. Install dependencies:

```bash
npm install
```

2. Create environment file:

```bash
cp .env.example .env
```

3. Configure backend URL in `.env`:

```
VITE_API_BASE_URL=http://localhost:8000
```

## Development

Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Build

Create production build:

```bash
npm run build
```

Preview production build:

```bash
npm run preview
```

## Backend Integration

The frontend connects to the FastAPI backend via:

- `POST /api/analyze` - Main MRI analysis endpoint
- Environment variable: `VITE_API_BASE_URL`

## File Structure

```
src/
├── components/          # React components
│   ├── AnalyzeButton.jsx
│   ├── ConfidenceBar.jsx
│   ├── ErrorCard.jsx
│   ├── ExplanationCard.jsx
│   ├── FileError.jsx
│   ├── FilePreview.jsx
│   ├── Header.jsx
│   ├── Hero.jsx
│   ├── LoadingState.jsx
│   ├── ProbabilityList.jsx
│   ├── ResultCard.jsx
│   ├── ThemeToggle.jsx
│   ├── UploadCard.jsx
│   ├── UploadDropzone.jsx
│   └── UploadOptions.jsx
├── services/
│   └── api.js          # API service layer
├── styles/
│   └── global.css      # Global design system
├── App.jsx             # Root component
└── main.jsx            # Entry point
```

## Design System

The application uses a comprehensive design system with:

- CSS custom properties for theming
- Responsive breakpoints: 320px, 375px, 425px, 768px, 1024px, 1280px, 1440px, 1920px+
- Blue medical-AI aesthetic with premium minimal appearance
- Consistent spacing, typography, and rounded corners
- Smooth transitions and subtle shadows
