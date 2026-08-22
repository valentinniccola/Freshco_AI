import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  UploadCloud, Camera, Image as ImageIcon, Sparkles, AlertCircle, 
  RotateCcw, CheckCircle2, ChevronRight, Zap, RefreshCw, Lock, AlertTriangle, 
  Eye, Sun, SwitchCamera, VideoOff, Aperture
} from 'lucide-react';
import { predictAPI, getImageUrl } from '../services/api';
import { useAuth } from '../context/AuthContext';

const FOOD_CATEGORIES = [
  { id: 'General', name: 'Auto / General', icon: '🍽️' },
  { id: 'Fruit', name: 'Fruits', icon: '🍎' },
  { id: 'Vegetable', name: 'Vegetables', icon: '🥦' },
  { id: 'Meat', name: 'Meat & Poultry', icon: '🥩' },
  { id: 'Dairy', name: 'Dairy & Cheese', icon: '🧀' },
  { id: 'Bakery', name: 'Bakery & Bread', icon: '🍞' },
];

const ALLOWED_EXTENSIONS = ['image/jpeg', 'image/png', 'image/webp'];

const Scanner = ({ onScanComplete }) => {
  const { user, openAuth } = useAuth();

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [selectedSample, setSelectedSample] = useState(null);
  const [category, setCategory] = useState('General');
  const [samples, setSamples] = useState([]);
  
  // Webcam state
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [facingMode, setFacingMode] = useState('environment'); // 'environment' or 'user'
  const [cameraLoading, setCameraLoading] = useState(false);
  const streamRef = useRef(null);
  const videoElementRef = useRef(null);

  // Scanning & validation state
  const [analyzing, setAnalyzing] = useState(false);
  const [scanStep, setScanStep] = useState(0);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  const fileInputRef = useRef(null);

  useEffect(() => {
    const loadSamples = async () => {
      try {
        const res = await predictAPI.getSamples();
        setSamples(res.data);
      } catch (err) {
        console.warn('Could not load samples:', err);
      }
    };
    loadSamples();

    return () => {
      stopCamera();
    };
  }, []);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      processSelectedFile(e.target.files[0]);
    }
  };

  const processSelectedFile = (file) => {
    setError(null);
    setSelectedSample(null);
    stopCamera();

    if (!ALLOWED_EXTENSIONS.includes(file.type)) {
      setError({
        type: 'format',
        title: 'Invalid File Format',
        message: 'Invalid file format. Only JPG, JPEG, PNG, and WebP images are allowed.'
      });
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError({
        type: 'size',
        title: 'File Too Large',
        message: 'File size exceeds the 10MB limit. Please upload a smaller image.'
      });
      return;
    }

    const img = new Image();
    const objectUrl = URL.createObjectURL(file);
    img.onload = () => {
      if (img.width < 224 || img.height < 224) {
        setError({
          type: 'resolution',
          title: 'Low Image Resolution',
          message: `Image resolution is too low (${img.width}×${img.height} detected, minimum 224×224 required). Please provide a higher resolution image.`
        });
        setSelectedFile(null);
        setPreviewUrl(null);
      } else {
        setSelectedFile(file);
        setPreviewUrl(objectUrl);
      }
    };
    img.onerror = () => {
      setError({
        type: 'corrupt',
        title: 'Corrupted Image',
        message: 'Uploaded file is corrupted or unreadable. Please select a valid image.'
      });
    };
    img.src = objectUrl;
  };

  const handleSelectSample = (sample) => {
    setError(null);
    setSelectedFile(null);
    stopCamera();
    setSelectedSample(sample);
    setCategory(sample.category);
    setPreviewUrl(sample.url);
  };

  // Robust camera initializer with multi-tier constraint fallback
  const startCamera = async (requestedFacing = facingMode) => {
    setError(null);
    setSelectedFile(null);
    setSelectedSample(null);
    setPreviewUrl(null);
    setCameraLoading(true);

    // Stop any existing stream first
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setError({
        type: 'camera',
        title: 'Camera Not Supported',
        message: 'Your browser does not support webcam access. Please use file upload instead.'
      });
      setCameraLoading(false);
      return;
    }

    let stream = null;

    // Attempt 1: Ideal constraints with resolution and requested facingMode
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: requestedFacing },
          width: { ideal: 1280, min: 640 },
          height: { ideal: 720, min: 480 },
        },
        audio: false,
      });
    } catch (err1) {
      console.warn('Attempt 1 failed, trying fallback constraints:', err1);
      // Attempt 2: Simple video constraint
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
      } catch (err2) {
        console.error('All camera attempts failed:', err2);
        setCameraLoading(false);
        setIsCameraActive(false);

        if (err2.name === 'NotAllowedError' || err2.name === 'PermissionDeniedError') {
          setError({
            type: 'camera_permission',
            title: 'Camera Permission Denied',
            message: 'Camera access was blocked by your browser. Please click the lock/camera icon in your address bar to allow camera access, then retry.'
          });
        } else if (err2.name === 'NotFoundError' || err2.name === 'DevicesNotFoundError') {
          setError({
            type: 'camera_missing',
            title: 'No Camera Device Found',
            message: 'No webcam or camera device was detected on your computer. Please upload an image file instead.'
          });
        } else if (err2.name === 'NotReadableError' || err2.name === 'TrackStartError') {
          setError({
            type: 'camera_busy',
            title: 'Camera In Use',
            message: 'Your webcam is already in use by another application or tab. Please close other apps using the camera and retry.'
          });
        } else {
          setError({
            type: 'camera_error',
            title: 'Camera Access Error',
            message: `Unable to access webcam (${err2.message || err2.name}). Please use file upload.`
          });
        }
        return;
      }
    }

    if (stream) {
      streamRef.current = stream;
      setIsCameraActive(true);
      setCameraLoading(false);

      // Attach stream to video element if already rendered
      if (videoElementRef.current) {
        videoElementRef.current.srcObject = stream;
        videoElementRef.current.play().catch((e) => console.warn('Autoplay error:', e));
      }
    }
  };

  // Video element callback ref to attach stream immediately upon mounting
  const setVideoRef = useCallback((node) => {
    videoElementRef.current = node;
    if (node && streamRef.current) {
      node.srcObject = streamRef.current;
      node.play().catch((e) => console.warn('Play error on mount:', e));
    }
  }, []);

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoElementRef.current) {
      videoElementRef.current.srcObject = null;
    }
    setIsCameraActive(false);
    setCameraLoading(false);
  };

  const toggleCameraFacing = () => {
    const nextFacing = facingMode === 'environment' ? 'user' : 'environment';
    setFacingMode(nextFacing);
    startCamera(nextFacing);
  };

  const captureWebcamFrame = () => {
    if (!videoElementRef.current) return;
    const video = videoElementRef.current;
    
    // Ensure video has loaded dimensions
    const width = video.videoWidth || 640;
    const height = video.videoHeight || 480;

    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    
    // If front camera, mirror horizontally for natural feel
    if (facingMode === 'user') {
      ctx.translate(width, 0);
      ctx.scale(-1, 1);
    }
    ctx.drawImage(video, 0, 0, width, height);

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], 'camera_capture.jpg', { type: 'image/jpeg' });
        stopCamera();
        processSelectedFile(file);
      }
    }, 'image/jpeg', 0.95);
  };

  const handleAnalyze = async () => {
    if (!user) {
      setError({
        type: 'auth',
        title: 'Authentication Required',
        message: 'Please sign in or create an account to scan food items and save prediction history.'
      });
      openAuth('login');
      return;
    }

    if (!selectedFile && !selectedSample) {
      setError({
        type: 'missing',
        title: 'No Image Selected',
        message: 'Please upload an image, capture with webcam, or choose a sample to analyze.'
      });
      return;
    }

    setError(null);
    setAnalyzing(true);
    setScanStep(1);

    const formData = new FormData();
    formData.append('category', category);

    if (selectedFile) {
      formData.append('file', selectedFile);
    } else if (selectedSample) {
      formData.append('sample_id', selectedSample.id);
    }

    const stepTimer1 = setTimeout(() => setScanStep(2), 500);
    const stepTimer2 = setTimeout(() => setScanStep(3), 900);

    try {
      const response = await predictAPI.predictImage(formData);
      setTimeout(() => {
        setAnalyzing(false);
        setScanStep(0);
        onScanComplete(response.data);
      }, 1200);
    } catch (err) {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setAnalyzing(false);
      setScanStep(0);

      const status = err.response?.status;
      const detail = err.response?.data?.detail || err.customMessage || err.message;

      if (status === 401) {
        setError({
          type: 'auth',
          title: 'Session Expired',
          message: 'Your session has expired. Please sign in again.'
        });
        openAuth('login');
      } else if (status === 429) {
        setError({
          type: 'rate_limit',
          title: 'Upload Rate Limit Exceeded',
          message: detail
        });
      } else if (status === 422) {
        setError({
          type: 'content_validation',
          title: 'Image Validation Notice',
          message: detail
        });
      } else {
        setError({
          type: 'general',
          title: 'Analysis Error',
          message: detail || 'Failed to analyze food image. Please try again.'
        });
      }
    }
  };

  const resetAll = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setSelectedSample(null);
    setError(null);
    stopCamera();
  };

  return (
    <div className="space-y-8 animate-fade-in">
      
      {/* Hero Header */}
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-emerald-100 dark:bg-emerald-500/10 border border-emerald-300 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-400 text-xs font-bold">
          <Sparkles className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
          <span>Multi-Tier Validation & MobileNetV2 AI Engine</span>
        </div>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-slate-900 dark:text-white tracking-tight">
          AI Smart Food <span className="bg-gradient-to-r from-emerald-600 to-teal-600 dark:from-emerald-400 dark:to-teal-300 bg-clip-text text-transparent">Freshness Detection</span>
        </h1>
        <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400 font-medium">
          Upload or capture food images to instantly assess freshness level (Fresh, Nearly Spoiled, or Spoiled), estimate shelf-life, and receive optimal storage & recipe advice.
        </p>
      </div>

      {/* Auth Callout Banner if Guest */}
      {!user && (
        <div className="max-w-4xl mx-auto p-4 rounded-2xl bg-emerald-50 dark:bg-slate-900 border border-emerald-200 dark:border-emerald-500/30 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-md">
          <div className="flex items-center space-x-3 text-xs sm:text-sm text-slate-800 dark:text-slate-300">
            <div className="p-2 rounded-xl bg-emerald-100 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 shrink-0">
              <Lock className="w-5 h-5" />
            </div>
            <div>
              <strong className="text-slate-900 dark:text-white block font-bold">Authentication Required for Analysis</strong>
              Sign in or register an account to scan food images, view shelf-life estimates, and sync SQLite history.
            </div>
          </div>
          <button
            onClick={() => openAuth('login')}
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-slate-950 text-xs font-bold shadow-md transition-all shrink-0"
          >
            Sign In / Register
          </button>
        </div>
      )}

      {/* Main Upload / Camera Card */}
      <div className="max-w-4xl mx-auto glass-panel rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 relative overflow-hidden shadow-xl">
        
        {/* Category Selector */}
        <div className="mb-6">
          <label className="block text-xs font-extrabold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-3">
            Select Food Category:
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
            {FOOD_CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                type="button"
                onClick={() => setCategory(cat.id)}
                className={`flex items-center space-x-2 p-2.5 rounded-xl text-xs font-bold border transition-all duration-200 ${
                  category === cat.id
                    ? 'bg-emerald-100 dark:bg-emerald-500/20 border-emerald-500 text-emerald-900 dark:text-emerald-300 shadow-md ring-1 ring-emerald-500'
                    : 'bg-slate-100 dark:bg-slate-900/60 border-slate-300 dark:border-slate-800 text-slate-800 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-slate-950 dark:hover:text-white'
                }`}
              >
                <span className="text-base">{cat.icon}</span>
                <span className="truncate">{cat.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Upload Zone / Webcam View */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative min-h-[320px] sm:min-h-[380px] rounded-2xl border-2 border-dashed flex flex-col items-center justify-center p-6 text-center transition-all duration-200 overflow-hidden ${
            dragOver
              ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-500/10 scale-[0.99]'
              : 'border-slate-300 dark:border-slate-700 bg-slate-50/90 dark:bg-slate-950/60 hover:border-slate-400 dark:hover:border-slate-600'
          }`}
        >
          {/* Active Webcam View */}
          {isCameraActive && (
            <div className="relative w-full h-full flex flex-col items-center justify-center space-y-4">
              <div className="relative w-full max-w-lg rounded-2xl overflow-hidden border-2 border-emerald-500/60 shadow-2xl bg-black aspect-video flex items-center justify-center">
                <video
                  ref={setVideoRef}
                  autoPlay
                  playsInline
                  muted
                  className={`w-full h-full object-cover ${facingMode === 'user' ? 'scale-x-[-1]' : ''}`}
                />

                {/* Viewfinder Target Crosshairs Overlay */}
                <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                  <div className="w-48 h-48 sm:w-60 sm:h-60 border-2 border-dashed border-emerald-400/70 rounded-2xl flex items-center justify-center relative">
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded-full bg-slate-950/80 text-[10px] font-bold text-emerald-400 border border-emerald-500/30">
                      Center Food Here
                    </div>
                  </div>
                </div>

                {/* Switch Camera Button (if device has multiple cameras) */}
                <button
                  type="button"
                  onClick={toggleCameraFacing}
                  title="Switch Camera (Front / Rear)"
                  className="absolute top-3 right-3 p-2.5 rounded-xl bg-slate-950/80 backdrop-blur-md border border-white/20 text-white hover:bg-slate-900 transition-colors"
                >
                  <SwitchCamera className="w-4 h-4" />
                </button>
              </div>

              {/* Camera Action Buttons */}
              <div className="flex flex-wrap items-center justify-center gap-3">
                <button
                  type="button"
                  onClick={captureWebcamFrame}
                  className="px-6 py-3 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 dark:hover:from-emerald-400 dark:hover:to-teal-400 text-white dark:text-slate-950 font-extrabold text-sm shadow-lg shadow-emerald-500/25 flex items-center space-x-2 transition-all group"
                >
                  <Aperture className="w-5 h-5 group-hover:rotate-45 transition-transform" />
                  <span>Snap Photo for Analysis</span>
                </button>
                <button
                  type="button"
                  onClick={stopCamera}
                  className="px-5 py-3 rounded-2xl bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-300 text-sm font-bold transition-colors"
                >
                  Close Camera
                </button>
              </div>
            </div>
          )}

          {/* Camera Loading State */}
          {cameraLoading && !isCameraActive && (
            <div className="py-16 text-center text-slate-500 dark:text-slate-400 flex flex-col items-center space-y-3">
              <RefreshCw className="w-8 h-8 text-emerald-600 dark:text-emerald-400 animate-spin" />
              <span className="text-sm font-bold">Requesting webcam access from your browser...</span>
              <p className="text-xs text-slate-400">Please click "Allow" if your browser prompts for permission.</p>
            </div>
          )}

          {/* Image Preview View */}
          {!isCameraActive && !cameraLoading && previewUrl && (
            <div className="relative w-full flex flex-col items-center">
              <div className="relative group max-w-sm rounded-2xl overflow-hidden border border-slate-300 dark:border-slate-700/60 shadow-2xl bg-black">
                <img
                  src={previewUrl}
                  alt="Food item to analyze"
                  className="w-full h-64 object-contain rounded-2xl transition-transform duration-300"
                />

                {analyzing && (
                  <div className="absolute inset-0 bg-emerald-500/10 pointer-events-none">
                    <div className="w-full h-1 bg-gradient-to-r from-transparent via-emerald-400 to-transparent shadow-[0_0_15px_#10b981] animate-scan absolute" />
                  </div>
                )}
              </div>

              {!analyzing && (
                <div className="mt-4 flex items-center space-x-3">
                  <button
                    type="button"
                    onClick={resetAll}
                    className="flex items-center space-x-1.5 text-xs text-slate-600 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 font-semibold transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Clear / Choose Different Photo</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Empty Upload Prompt View */}
          {!isCameraActive && !cameraLoading && !previewUrl && (
            <div className="flex flex-col items-center space-y-4 max-w-sm">
              <div className="w-16 h-16 rounded-2xl bg-emerald-100 dark:bg-emerald-500/10 border border-emerald-300 dark:border-emerald-500/20 flex items-center justify-center text-emerald-700 dark:text-emerald-400 mb-1">
                <UploadCloud className="w-8 h-8" />
              </div>
              <div>
                <p className="text-base font-extrabold text-slate-900 dark:text-white">
                  Drag and drop food photo here
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 font-medium">
                  JPG, PNG, WebP (Max 10MB, Min 224×224 resolution)
                </p>
              </div>

              <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="px-5 py-2.5 rounded-xl bg-slate-900 dark:bg-slate-800 hover:bg-slate-800 dark:hover:bg-slate-700 text-white text-xs font-bold border border-slate-700 flex items-center space-x-2 shadow-md transition-colors"
                >
                  <ImageIcon className="w-4 h-4 text-emerald-400" />
                  <span>Browse Files</span>
                </button>
                <button
                  type="button"
                  onClick={() => startCamera()}
                  className="px-5 py-2.5 rounded-xl bg-slate-900 dark:bg-slate-800 hover:bg-slate-800 dark:hover:bg-slate-700 text-white text-xs font-bold border border-slate-700 flex items-center space-x-2 shadow-md transition-colors"
                >
                  <Camera className="w-4 h-4 text-teal-400" />
                  <span>Use Camera</span>
                </button>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>
          )}
        </div>

        {/* Validation Error Banner with Retry */}
        {error && (
          <div className="mt-5 p-4 rounded-2xl bg-rose-50 dark:bg-rose-500/10 border border-rose-300 dark:border-rose-500/30 text-rose-900 dark:text-rose-200 text-xs sm:text-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-lg">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 shrink-0 text-rose-600 dark:text-rose-400 mt-0.5" />
              <div>
                <strong className="text-rose-950 dark:text-white block font-extrabold text-sm">
                  {error.title || 'Validation Alert'}
                </strong>
                <p className="text-rose-800 dark:text-rose-300 mt-0.5 leading-relaxed font-medium">
                  {error.message}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2 shrink-0 self-end sm:self-auto">
              <button
                type="button"
                onClick={() => {
                  if (error.type?.startsWith('camera')) {
                    startCamera();
                  } else {
                    handleAnalyze();
                  }
                }}
                disabled={analyzing}
                className="px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-700 dark:bg-rose-500/20 dark:hover:bg-rose-500/30 text-white dark:text-rose-300 font-bold text-xs border border-rose-600 dark:border-rose-500/40 flex items-center space-x-1.5 transition-colors disabled:opacity-50"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retry</span>
              </button>
              <button
                type="button"
                onClick={() => setError(null)}
                className="px-3 py-1.5 rounded-xl bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-300 text-xs font-semibold transition-colors"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Quick-Test Sample Images Carousel */}
        {samples.length > 0 && !previewUrl && !isCameraActive && (
          <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-800/80">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-extrabold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
                Or Try Sample Test Images (Instant Demo):
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
              {samples.map((sample) => (
                <div
                  key={sample.id}
                  onClick={() => handleSelectSample(sample)}
                  className={`group relative p-2.5 rounded-xl border cursor-pointer transition-all duration-200 flex flex-col items-center text-center ${
                    selectedSample?.id === sample.id
                      ? 'border-emerald-500 bg-emerald-100 dark:bg-emerald-500/10 ring-1 ring-emerald-500'
                      : 'border-slate-300 dark:border-slate-800 bg-slate-100 dark:bg-slate-900/50 hover:border-slate-400 dark:hover:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-800/50'
                  }`}
                >
                  <img
                    src={getImageUrl(sample.url)}
                    alt={sample.name}
                    className="w-14 h-14 rounded-lg object-contain bg-white dark:bg-slate-950 p-1 mb-1.5 shadow-sm group-hover:scale-105 transition-transform"
                  />
                  <span className="text-[11px] font-bold text-slate-900 dark:text-slate-200 line-clamp-1">
                    {sample.name}
                  </span>
                  <span
                    className={`text-[9px] font-extrabold mt-1 px-1.5 py-0.5 rounded ${
                      sample.expected === 'Fresh'
                        ? 'bg-emerald-200 dark:bg-emerald-500/20 text-emerald-900 dark:text-emerald-400'
                        : sample.expected === 'Nearly Spoiled'
                        ? 'bg-amber-200 dark:bg-amber-500/20 text-amber-900 dark:text-amber-400'
                        : 'bg-rose-200 dark:bg-rose-500/20 text-rose-900 dark:text-rose-400'
                    }`}
                  >
                    {sample.expected}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Real-time Pipeline Progress Steps */}
        {analyzing && (
          <div className="mt-6 p-4 rounded-2xl bg-slate-100 dark:bg-slate-900/90 border border-slate-300 dark:border-slate-800 space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-800 dark:text-slate-200 font-bold">
              <span className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4 text-emerald-600 dark:text-emerald-400 animate-spin" />
                Executing Validation & Vision Pipeline...
              </span>
              <span className="text-emerald-700 dark:text-emerald-400 font-mono">
                {scanStep === 1 ? '1. OpenCV Blur & Food Check...' : scanStep === 2 ? '2. MobileNetV2 CNN...' : '3. Confidence & Margin Verifier...'}
              </span>
            </div>
            
            <div className="grid grid-cols-3 gap-2 text-[11px] font-semibold">
              <div className={`p-2 rounded-lg border text-center transition-all ${
                scanStep >= 1 ? 'border-emerald-500 bg-emerald-100 dark:bg-emerald-500/10 text-emerald-900 dark:text-emerald-300 font-bold' : 'border-slate-300 dark:border-slate-800 text-slate-500'
              }`}>
                1. Blur, Light & Food Checks
              </div>
              <div className={`p-2 rounded-lg border text-center transition-all ${
                scanStep >= 2 ? 'border-teal-500 bg-teal-100 dark:bg-teal-500/10 text-teal-900 dark:text-teal-300 font-bold' : 'border-slate-300 dark:border-slate-800 text-slate-500'
              }`}>
                2. MobileNetV2 3-Class Softmax
              </div>
              <div className={`p-2 rounded-lg border text-center transition-all ${
                scanStep >= 3 ? 'border-cyan-500 bg-cyan-100 dark:bg-cyan-500/10 text-cyan-900 dark:text-cyan-300 font-bold' : 'border-slate-300 dark:border-slate-800 text-slate-500'
              }`}>
                3. Confidence & Margin Verifier
              </div>
            </div>
          </div>
        )}

        {/* Action Button */}
        {previewUrl && !isCameraActive && (
          <div className="mt-6 flex justify-end">
            <button
              type="button"
              disabled={analyzing}
              onClick={handleAnalyze}
              className="w-full sm:w-auto px-8 py-3.5 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 dark:from-emerald-500 dark:to-teal-500 hover:from-emerald-700 hover:to-teal-700 dark:hover:from-emerald-400 dark:hover:to-teal-400 text-white dark:text-slate-950 font-extrabold text-sm shadow-xl shadow-emerald-500/25 flex items-center justify-center space-x-2 transition-all disabled:opacity-50"
            >
              {analyzing ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  <span>Validating & Analyzing...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Analyze Food Freshness</span>
                  <ChevronRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        )}

      </div>

    </div>
  );
};

export default Scanner;
