import React from 'react';
import { 
  Cpu, Layers, Code, ShieldCheck, Database, Zap, 
  Eye, CheckCircle2, ArrowDown, Sparkles, Activity
} from 'lucide-react';

const ModelArchitecture = () => {
  const steps = [
    {
      step: '01',
      title: 'Food Image Input & Validation',
      tool: 'React.js + Axios + FastAPI',
      desc: 'User uploads a photo via drag & drop, file picker, or real-time webcam stream. FastAPI receives the multipart payload and validates file integrity.',
      icon: Eye,
      color: 'emerald',
    },
    {
      step: '02',
      title: 'OpenCV Preprocessing & Defect Segmentation',
      tool: 'OpenCV (cv2) + NumPy',
      desc: 'Resizes image to 224x224 RGB, isolates foreground food regions, maps discoloration indices in LAB color space, and quantifies dark/browning/mold spots.',
      icon: Layers,
      color: 'teal',
    },
    {
      step: '03',
      title: 'MobileNetV2 CNN Feature Extraction',
      tool: 'TensorFlow / Keras + MobileNetV2',
      desc: 'Processes spatial feature maps using Depthwise Separable Convolutions and Inverted Residual blocks with linear bottlenecks pre-trained on ImageNet.',
      icon: Cpu,
      color: 'cyan',
    },
    {
      step: '04',
      title: '3-Class Softmax Classification',
      tool: 'Dense Neural Head & Softmax',
      desc: 'Outputs probability distributions across Fresh, Nearly Spoiled, and Spoiled classes with a calibrated confidence score and margin verifier.',
      icon: Activity,
      color: 'amber',
    },
    {
      step: '05',
      title: 'Zero-Waste Recipe & Shelf-Life Rules',
      tool: 'Recipe Engine & Expert Heuristics',
      desc: 'Generates rescue recipe suggestions for Nearly Spoiled items and cross-references food category to calculate approximate days remaining.',
      icon: Zap,
      color: 'emerald',
    },
    {
      step: '06',
      title: 'SQL Analytics & Dashboard Rendering',
      tool: 'SQLite + Recharts + React UI',
      desc: 'Saves prediction records and metrics in SQLite DB, computes SQL aggregations for time-series analytics, and presents the interactive dashboard.',
      icon: Database,
      color: 'teal',
    },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-10 animate-fade-in">
      
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs font-semibold">
          <Cpu className="w-3.5 h-3.5" />
          <span>Complete System Architecture & Technical Specifications</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white">
          How Freshco AI Evaluates Food Freshness
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
          A seamless synergy between OpenCV computer vision algorithms, MobileNetV2 Deep Convolutional Neural Networks, and rule-based shelf-life heuristics.
        </p>
      </div>

      {/* Pipeline Flowchart Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {steps.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.step}
              className="glass-panel p-6 rounded-3xl border border-slate-200 dark:border-slate-800 hover:border-emerald-500/40 transition-all duration-300 relative flex flex-col justify-between group shadow-xl"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-black font-mono text-emerald-500/30 dark:text-emerald-400/40 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                    {item.step}
                  </span>
                  <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                    <Icon className="w-5 h-5" />
                  </div>
                </div>

                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-300 transition-colors">
                    {item.title}
                  </h3>
                  <div className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">
                    {item.tool}
                  </div>
                </div>

                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  {item.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Technical Highlights Section */}
      <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 space-y-6 shadow-2xl">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <Code className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          Technical Stack & Role Distinction
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="font-bold text-emerald-700 dark:text-emerald-300 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" /> OpenCV (Computer Vision)
            </div>
            <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
              Handles raw image reading, aspect-ratio preservation, color space conversions (BGR to RGB, HSV, LAB), surface defect masking, and browning spot density calculation.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="font-bold text-teal-700 dark:text-teal-300 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400" /> MobileNetV2 (CNN Transfer Learning)
            </div>
            <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
              Lightweight, high-speed deep convolutional network utilizing inverted residual blocks and linear bottlenecks for optimal food freshness classification.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="font-bold text-cyan-700 dark:text-cyan-300 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-cyan-600 dark:text-cyan-400" /> FastAPI & SQLite
            </div>
            <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
              High-performance asynchronous Python web framework managing JWT authentication, image uploads, inference coordination, and persistent SQLite scan logs.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 space-y-2">
            <div className="font-bold text-amber-700 dark:text-amber-300 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-amber-600 dark:text-amber-400" /> React & Tailwind CSS + Recharts
            </div>
            <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
              Modern, responsive user interface with drag-and-drop file inputs, live webcam capture, dynamic confidence gauges, shelf-life indicators, and history tables.
            </p>
          </div>
        </div>
      </div>

    </div>
  );
};

export default ModelArchitecture;
