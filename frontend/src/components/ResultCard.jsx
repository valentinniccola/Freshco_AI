import React, { useEffect } from 'react';
import { 
  CheckCircle, AlertTriangle, AlertOctagon, Clock, ShieldAlert, 
  Thermometer, Info, RotateCcw, Share2, Sparkles, Activity, Layers, 
  HelpCircle, Utensils, ChefHat, ExternalLink, Flame, BarChart2
} from 'lucide-react';
import confetti from 'canvas-confetti';

import { getImageUrl } from '../services/api';

const ResultCard = ({ result, onReset, onViewHistory }) => {
  if (!result) return null;

  const confidencePct = Math.round((result.confidence || result.confidence_score || 0) * 100);
  const isLowConfidence = result.is_low_confidence || (result.confidence && result.confidence < 0.65);
  const isUncertain = result.is_uncertain;
  
  const freshnessLabel = result.freshness || result.freshness_status || 'Fresh';
  const isFresh = freshnessLabel === 'Fresh';
  const isNearly = freshnessLabel === 'Nearly Spoiled';
  const isSpoiled = freshnessLabel === 'Spoiled';

  const showRecipes = (isNearly || result.candidate_classes?.includes('Nearly Spoiled')) && result.recipe_suggestions?.length > 0;

  // Extract all class probabilities
  const probs = result.all_probabilities || {
    Fresh: result.probabilities?.Fresh || 0,
    'Nearly Spoiled': result.probabilities?.Nearly_Spoiled || 0,
    Spoiled: result.probabilities?.Spoiled || 0,
  };

  const freshPct = Math.round((probs['Fresh'] || probs['fresh'] || 0) * 100);
  const nearlyPct = Math.round((probs['Nearly Spoiled'] || probs['Nearly_Spoiled'] || 0) * 100);
  const spoiledPct = Math.round((probs['Spoiled'] || probs['spoiled'] || 0) * 100);

  // Trigger confetti only if confidently Fresh!
  useEffect(() => {
    if (isFresh && !isUncertain && !isLowConfidence && (result.confidence || result.confidence_score) > 0.85) {
      try {
        confetti({
          particleCount: 75,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#10b981', '#34d399', '#6ee7b7', '#a7f3d0']
        });
      } catch (e) {
        // ignore
      }
    }
  }, [isFresh, isUncertain, isLowConfidence, result]);

  // Color & Badge mappings
  const getTheme = () => {
    if (isLowConfidence) {
      return {
        color: 'amber',
        badgeBg: 'bg-amber-100 dark:bg-amber-500/20 border-amber-400 dark:border-amber-500/50 text-amber-900 dark:text-amber-300',
        glow: 'shadow-amber-500/15 border-amber-300 dark:border-amber-500/40',
        icon: AlertTriangle,
      };
    }
    if (isUncertain) {
      return {
        color: 'cyan',
        badgeBg: 'bg-cyan-100 dark:bg-cyan-500/20 border-cyan-400 dark:border-cyan-500/50 text-cyan-900 dark:text-cyan-300',
        glow: 'shadow-cyan-500/15 border-cyan-300 dark:border-cyan-500/40',
        icon: Info,
      };
    }
    if (isFresh) {
      return {
        color: 'emerald',
        badgeBg: 'bg-emerald-100 dark:bg-emerald-500/20 border-emerald-400 dark:border-emerald-500/40 text-emerald-900 dark:text-emerald-300',
        glow: 'shadow-emerald-500/20 border-emerald-300 dark:border-emerald-500/30',
        icon: CheckCircle,
      };
    }
    if (isNearly) {
      return {
        color: 'amber',
        badgeBg: 'bg-amber-100 dark:bg-amber-500/20 border-amber-400 dark:border-amber-500/40 text-amber-900 dark:text-amber-300',
        glow: 'shadow-amber-500/20 border-amber-300 dark:border-amber-500/30',
        icon: AlertTriangle,
      };
    }
    return {
      color: 'rose',
      badgeBg: 'bg-rose-100 dark:bg-rose-500/20 border-rose-400 dark:border-rose-500/40 text-rose-900 dark:text-rose-300',
      glow: 'shadow-rose-500/20 border-rose-300 dark:border-rose-500/30',
      icon: AlertOctagon,
    };
  };

  const theme = getTheme();
  const StatusIcon = theme.icon;

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={onReset}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold border border-slate-700 transition-colors shadow-sm"
        >
          <RotateCcw className="w-4 h-4 text-emerald-400" />
          <span>Scan Another Food Item</span>
        </button>

        <button
          onClick={onViewHistory}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-200 dark:bg-slate-900 hover:bg-slate-300 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-300 text-xs font-bold border border-slate-300 dark:border-slate-800 transition-colors shadow-sm"
        >
          <span>View Past Scans</span>
        </button>
      </div>

      {/* 1. Low Confidence Warning Banner (< 65%) */}
      {isLowConfidence && (
        <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-500/10 border-2 border-amber-400 dark:border-amber-500/40 flex items-start space-x-3 text-amber-950 dark:text-amber-200 text-xs sm:text-sm shadow-md">
          <AlertTriangle className="w-5 h-5 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
          <div>
            <strong className="text-slate-950 dark:text-white block font-extrabold text-sm mb-0.5">
              ⚠️ Low confidence result — consider retaking the photo for a clearer analysis
            </strong>
            The top classification confidence ({confidencePct}%) is below the 65% certainty threshold. Lighting, angle, or focus might have affected this scan.
          </div>
        </div>
      )}

      {/* 2. Close Margin Banner (<= 10% between top classes) */}
      {isUncertain && !isLowConfidence && (
        <div className="p-4 rounded-2xl bg-cyan-50 dark:bg-cyan-500/10 border-2 border-cyan-400 dark:border-cyan-500/40 flex items-start space-x-3 text-cyan-950 dark:text-cyan-200 text-xs sm:text-sm shadow-md">
          <Info className="w-5 h-5 shrink-0 text-cyan-600 dark:text-cyan-400 mt-0.5" />
          <div>
            <strong className="text-slate-950 dark:text-white block font-extrabold text-sm mb-0.5">
              Borderline Classification (Within 10% Margin)
            </strong>
            The model identified close visual traits between <strong>{result.candidate_classes?.join(' and ')}</strong>. Probability breakdown shown below.
          </div>
        </div>
      )}

      {/* Main Results Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Image Preview & Main Status Card */}
        <div className="lg:col-span-5 space-y-6">
          <div className={`glass-panel rounded-3xl p-6 border ${theme.glow} shadow-xl relative overflow-hidden`}>
            
            {/* Food Image Preview */}
            <div className="relative rounded-2xl overflow-hidden bg-black border border-slate-300 dark:border-slate-800 aspect-square flex items-center justify-center mb-6">
              <img
                src={getImageUrl(result.image_url)}
                alt={result.original_filename}
                className="w-full h-full object-cover"
              />
              
              {/* Category & Food Type Tag */}
              <div className="absolute top-3 left-3 flex items-center space-x-1.5">
                <span className="px-3 py-1 rounded-full bg-slate-950/85 backdrop-blur-md border border-white/15 text-xs font-bold text-white shadow">
                  {result.food_category}
                </span>
                {result.food_type && result.food_type !== 'food item' && (
                  <span className="px-2.5 py-1 rounded-full bg-emerald-600/90 backdrop-blur-md text-xs font-black text-white capitalize shadow">
                    {result.food_type}
                  </span>
                )}
              </div>

              {/* Prominent Confidence Score Badge */}
              <div className="absolute bottom-3 right-3 px-3 py-1.5 rounded-xl bg-slate-950/90 backdrop-blur-md border border-white/15 flex items-center space-x-1.5 text-xs font-black text-white shadow">
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                <span>{confidencePct}% Confident</span>
              </div>
            </div>

            {/* Clear Primary Result Header */}
            <div className="text-center space-y-3">
              
              {/* Prominent Headline: e.g. "Nearly Spoiled — 78% confident" */}
              <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-2xl border-2 font-black text-sm sm:text-base shadow-sm bg-slate-100 dark:bg-slate-900 border-slate-300 dark:border-slate-700">
                <StatusIcon className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                <span className="text-slate-900 dark:text-white">
                  {freshnessLabel} <span className="text-emerald-700 dark:text-emerald-400 font-mono font-extrabold">— {confidencePct}% confident</span>
                </span>
              </div>

              <h2 className="text-2xl font-black text-slate-900 dark:text-white">
                {result.original_filename}
              </h2>

              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed font-medium">
                {result.action_recommendation}
              </p>
            </div>

          </div>

          {/* Full Probability Distribution Progress Bars */}
          <div className="glass-panel rounded-3xl p-6 border border-slate-200 dark:border-slate-800 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                Full Class Probability Distribution
              </h3>
              <span className="text-[10px] font-bold font-mono text-slate-500">Softmax Sum: 100%</span>
            </div>

            <div className="space-y-3 pt-1">
              
              {/* Fresh */}
              <div>
                <div className="flex justify-between text-xs font-bold mb-1">
                  <span className="text-emerald-700 dark:text-emerald-400 flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Fresh
                  </span>
                  <span className="text-slate-900 dark:text-slate-200 font-mono font-extrabold">
                    {freshPct}%
                  </span>
                </div>
                <div className="w-full h-3 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                    style={{ width: `${freshPct}%` }}
                  />
                </div>
              </div>

              {/* Nearly Spoiled */}
              <div>
                <div className="flex justify-between text-xs font-bold mb-1">
                  <span className="text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Nearly Spoiled
                  </span>
                  <span className="text-slate-900 dark:text-slate-200 font-mono font-extrabold">
                    {nearlyPct}%
                  </span>
                </div>
                <div className="w-full h-3 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-amber-500 rounded-full transition-all duration-500"
                    style={{ width: `${nearlyPct}%` }}
                  />
                </div>
              </div>

              {/* Spoiled */}
              <div>
                <div className="flex justify-between text-xs font-bold mb-1">
                  <span className="text-rose-700 dark:text-rose-400 flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Spoiled
                  </span>
                  <span className="text-slate-900 dark:text-slate-200 font-mono font-extrabold">
                    {spoiledPct}%
                  </span>
                </div>
                <div className="w-full h-3 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-rose-500 rounded-full transition-all duration-500"
                    style={{ width: `${spoiledPct}%` }}
                  />
                </div>
              </div>

            </div>
          </div>
        </div>

        {/* Right Column: Shelf-Life, Recipe Suggestions & Defect Metrics */}
        <div className="lg:col-span-7 space-y-6">
          
          {/* Estimated Shelf-Life Hero Card */}
          <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-xl relative overflow-hidden">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800/80">
              <div>
                <span className="text-xs font-extrabold uppercase tracking-wider text-slate-600 dark:text-slate-400 flex items-center gap-1.5 mb-1">
                  <Clock className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  Estimated Shelf-Life
                </span>
                <h3 className="text-3xl sm:text-4xl font-black text-slate-900 dark:text-white">
                  {result.shelf_life_days > 0 ? (
                    <>
                      ~{result.shelf_life_days} <span className="text-lg font-bold text-slate-600 dark:text-slate-300">Days Remaining</span>
                    </>
                  ) : (
                    <span className="text-rose-600 dark:text-rose-400 text-2xl font-black">0 Days (Spoiled / Expired)</span>
                  )}
                </h3>
              </div>

              <div className="flex items-center space-x-3">
                <div className="text-right hidden sm:block">
                  <div className="text-xs font-semibold text-slate-500 dark:text-slate-400">Estimated Window</div>
                  <div className="text-sm font-extrabold text-emerald-700 dark:text-emerald-300">{result.shelf_life_desc}</div>
                </div>
              </div>
            </div>

            {/* Storage Guidance */}
            <div className="pt-6 space-y-3">
              <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                <Thermometer className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                Actionable Storage Recommendation
              </h4>
              <p className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed bg-slate-100 dark:bg-slate-950/60 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 font-medium">
                {result.storage_advice}
              </p>
            </div>
          </div>

          {/* RECIPE SUGGESTIONS CARD (Shown exclusively for Nearly Spoiled items) */}
          {showRecipes && (
            <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-amber-300 dark:border-amber-500/40 shadow-xl space-y-4 bg-gradient-to-br from-amber-50 via-white to-amber-50/50 dark:from-amber-950/20 dark:via-slate-900 dark:to-slate-950">
              <div className="flex items-start justify-between">
                <div>
                  <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-100 dark:bg-amber-500/20 border border-amber-300 dark:border-amber-500/40 text-amber-900 dark:text-amber-300 text-xs font-black mb-2">
                    <ChefHat className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
                    <span>Zero-Waste Recipe Rescue</span>
                  </div>
                  <h3 className="text-base sm:text-lg font-black text-slate-900 dark:text-white">
                    Your {result.food_type} is nearly spoiled — try these recipes:
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5 font-medium">
                    Prevent food waste by cooking or prepping these quick dishes today:
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                {result.recipe_suggestions.map((recipe, idx) => (
                  <a
                    key={idx}
                    href={recipe.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-4 rounded-2xl bg-white dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800 hover:border-amber-500/50 group transition-all duration-200 flex flex-col justify-between space-y-3 shadow-sm hover:shadow-md"
                  >
                    <div>
                      <div className="flex items-center justify-between text-[11px] font-bold text-amber-700 dark:text-amber-400 mb-1.5">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" /> {recipe.prep_time}
                        </span>
                        <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[10px] font-bold">
                          {recipe.difficulty}
                        </span>
                      </div>
                      <h4 className="text-xs font-black text-slate-900 dark:text-white group-hover:text-amber-600 dark:group-hover:text-amber-300 transition-colors line-clamp-2">
                        {recipe.title}
                      </h4>
                      <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-1 line-clamp-3 leading-relaxed font-medium">
                        {recipe.description}
                      </p>
                    </div>

                    <div className="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] font-extrabold text-amber-700 dark:text-amber-400 group-hover:text-amber-600 dark:group-hover:text-amber-300">
                      <span>View Recipe</span>
                      <ExternalLink className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                    </div>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* OpenCV Defect Metrics */}
          <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 space-y-5 shadow-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-600 dark:text-slate-400 flex items-center gap-2">
                <Layers className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                OpenCV Visual Defect & Spoilage Analysis
              </h3>
              <span className="text-[11px] text-slate-500 font-mono font-bold">224x224 LAB/HSV Segmentation</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-center shadow-sm">
                <div className="text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1">Spot / Decay Coverage</div>
                <div className="text-xl font-black text-slate-900 dark:text-white font-mono">
                  {result.defect_metrics.spot_coverage_pct}%
                </div>
                <div className="text-[10px] text-slate-500 mt-1">Surface Necrosis</div>
              </div>

              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-center shadow-sm">
                <div className="text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1">Browning Index</div>
                <div className="text-xl font-black text-amber-600 dark:text-amber-400 font-mono">
                  {result.defect_metrics.browning_score} <span className="text-xs text-slate-500 font-normal">/ 10</span>
                </div>
                <div className="text-[10px] text-slate-500 mt-1">Oxidative Shift</div>
              </div>

              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-center shadow-sm">
                <div className="text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1">Discoloration Std</div>
                <div className="text-xl font-black text-teal-600 dark:text-teal-400 font-mono">
                  {result.defect_metrics.discoloration_index}
                </div>
                <div className="text-[10px] text-slate-500 mt-1">LAB Variance</div>
              </div>

              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-center shadow-sm">
                <div className="text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1">Texture Uniformity</div>
                <div className="text-xl font-black text-emerald-600 dark:text-emerald-400 font-mono">
                  {result.defect_metrics.surface_homogeneity}%
                </div>
                <div className="text-[10px] text-slate-500 mt-1">Smooth Skin</div>
              </div>
            </div>
          </div>

          {/* AI Food Safety Notice */}
          <div className="p-4 rounded-2xl bg-slate-100 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 flex items-start space-x-3 text-xs text-slate-600 dark:text-slate-400 shadow-sm">
            <ShieldAlert className="w-5 h-5 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
            <div className="leading-relaxed">
              <strong className="text-slate-900 dark:text-slate-200 font-bold">Food Safety Notice:</strong> This AI system detects visible optical signs of food deterioration from image features. It cannot detect odorless toxins, microscopic bacteria, or internal pathogens. Results and shelf-life estimates are AI-assisted guidelines, not official food-safety guarantees. When in doubt, smell and inspect carefully or discard.
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};

export default ResultCard;
