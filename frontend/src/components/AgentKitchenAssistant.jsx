import React, { useState } from 'react';
import { 
  Sparkles, ChefHat, Clock, AlertTriangle, CheckCircle, Flame, 
  Utensils, RefreshCw, Layers, ShieldCheck, ExternalLink, Lightbulb, Info
} from 'lucide-react';
import { agentAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

const AgentKitchenAssistant = () => {
  const { user, openAuth } = useAuth();

  const [recipe, setRecipe] = useState(null);
  const [loading, setLoading] = useState(false);
  const [days, setDays] = useState(7);
  const [error, setError] = useState(null);

  const handleGenerateRecipe = async () => {
    if (!user) {
      openAuth('login');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await agentAPI.getMultiItemRecipe(days);
      setRecipe(res.data);
    } catch (err) {
      console.error('Agent recipe failed:', err);
      const detail = err.response?.data?.detail || err.message || 'Failed to generate multi-item recipe.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-emerald-300/60 dark:border-emerald-500/30 shadow-xl bg-gradient-to-br from-emerald-50/60 via-white to-teal-50/40 dark:from-emerald-950/20 dark:via-slate-900 dark:to-teal-950/20 space-y-6 animate-fade-in">
      
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-emerald-100 dark:bg-emerald-500/10 border border-emerald-300 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-400 text-xs font-black mb-2">
            <ChefHat className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>AI Multi-Item Kitchen Assistant</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight">
            Combined Zero-Waste Recipe Generator
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 font-medium mt-1">
            Our AI Agent analyzes all your recently scanned <strong>Nearly Spoiled</strong> produce and designs a single delicious dish using them together.
          </p>
        </div>

        <div className="flex items-center space-x-3 self-start sm:self-auto">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 text-xs font-bold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value={3}>Last 3 Days</option>
            <option value={7}>Last 7 Days</option>
            <option value={14}>Last 14 Days</option>
          </select>

          <button
            onClick={handleGenerateRecipe}
            disabled={loading}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-extrabold text-xs shadow-lg shadow-emerald-500/25 flex items-center space-x-2 transition-all disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Chef Reasoning...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Generate Recipe</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-500/10 border border-rose-300 dark:border-rose-500/30 text-rose-900 dark:text-rose-200 text-xs sm:text-sm flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600 dark:text-rose-400" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="font-bold underline text-xs">Dismiss</button>
        </div>
      )}

      {/* Generated Recipe Display */}
      {recipe && (
        <div className="space-y-6 pt-2">
          
          {/* Main Recipe Header Card */}
          <div className="p-6 rounded-3xl bg-white dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 space-y-4 shadow-md">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-200 dark:border-slate-800">
              <div>
                <span className="text-[10px] font-black uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                  ✨ Multi-Ingredient Zero-Waste Creation
                </span>
                <h3 className="text-xl sm:text-2xl font-black text-slate-900 dark:text-white mt-0.5">
                  {recipe.recipe_title}
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 font-medium italic">
                  "{recipe.tagline}"
                </p>
              </div>

              <div className="flex items-center space-x-2 shrink-0">
                <span className="px-3 py-1 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-emerald-500" /> Prep: {recipe.prep_time}
                </span>
                <span className="px-3 py-1 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1">
                  <Flame className="w-3.5 h-3.5 text-amber-500" /> Cook: {recipe.cook_time}
                </span>
              </div>
            </div>

            {/* Rescued Produce Chips */}
            <div>
              <label className="block text-[11px] font-extrabold uppercase tracking-wider text-slate-500 mb-2">
                Rescued Expiring Produce Used ({recipe.used_ingredients.length} items):
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {recipe.used_ingredients.map((ing, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-2xl bg-amber-50 dark:bg-amber-500/10 border border-amber-300 dark:border-amber-500/30 flex items-center justify-between gap-3 text-xs"
                  >
                    <div>
                      <strong className="text-amber-950 dark:text-white font-extrabold block capitalize">
                        {ing.food_type}
                      </strong>
                      <span className="text-[11px] text-amber-800 dark:text-amber-300 font-medium">
                        {ing.reason}
                      </span>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-black bg-amber-200 dark:bg-amber-500/30 text-amber-900 dark:text-amber-300 shrink-0">
                      {ing.freshness}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Pantry Staples */}
            {recipe.pantry_staples_needed?.length > 0 && (
              <div className="pt-2">
                <label className="block text-[11px] font-extrabold uppercase tracking-wider text-slate-500 mb-1.5">
                  Common Pantry Staples Needed:
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {recipe.pantry_staples_needed.map((staple, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[11px] font-semibold text-slate-700 dark:text-slate-300"
                    >
                      {staple}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Step-by-Step Cooking Instructions */}
            <div className="pt-2 space-y-2">
              <label className="block text-[11px] font-extrabold uppercase tracking-wider text-slate-500">
                Step-by-Step Preparation:
              </label>
              <div className="space-y-2">
                {recipe.instructions.map((step, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 text-xs sm:text-sm text-slate-800 dark:text-slate-200 font-medium leading-relaxed"
                  >
                    {step}
                  </div>
                ))}
              </div>
            </div>

            {/* Chef Conservation Tip */}
            {recipe.chef_zero_waste_tip && (
              <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-300 dark:border-emerald-500/30 flex items-start space-x-3 text-xs sm:text-sm text-emerald-900 dark:text-emerald-200 font-medium shadow-sm">
                <Lightbulb className="w-5 h-5 shrink-0 text-emerald-600 dark:text-emerald-400 mt-0.5" />
                <div>
                  <strong className="text-emerald-950 dark:text-white block font-extrabold mb-0.5">
                    Zero-Waste Chef Tip:
                  </strong>
                  {recipe.chef_zero_waste_tip}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-200 dark:border-slate-800">
              <span>AI Multi-Item Reasoning Model</span>
              <span>Daily AI Recipe Quota Remaining: <strong>{recipe.calls_remaining_today} / 5</strong></span>
            </div>

          </div>

        </div>
      )}

    </div>
  );
};

export default AgentKitchenAssistant;
