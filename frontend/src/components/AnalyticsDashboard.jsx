import React, { useState, useEffect } from 'react';
import { 
  BarChart3, TrendingDown, PieChart as PieIcon, Calendar, 
  Sparkles, RefreshCw, AlertTriangle, CheckCircle, AlertOctagon, 
  HelpCircle, ArrowUpRight, ShieldCheck, Flame
} from 'lucide-react';
import { 
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip as RechartsTooltip, 
  Legend, LineChart, Line, XAxis, YAxis, CartesianGrid 
} from 'recharts';
import { analyticsAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';

const STATUS_COLORS = {
  Fresh: '#10b981',       // Emerald
  Nearly_Spoiled: '#f59e0b', // Amber
  Spoiled: '#f43f5e',     // Rose
};

const AnalyticsDashboard = () => {
  const { isDark } = useTheme();
  const [range, setRange] = useState('week'); // 'week', 'month', 'all'
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalytics = async (selectedRange) => {
    setLoading(true);
    setError(null);
    try {
      const res = await analyticsAPI.getAnalytics(selectedRange);
      setAnalyticsData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load analytics data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics(range);
  }, [range]);

  const rangeLabels = {
    week: 'this week (last 7 days)',
    month: 'this month (last 30 days)',
    all: 'across all recorded scans',
  };

  // Prepare Pie Chart Data
  const pieData = analyticsData?.status_breakdown ? [
    { name: 'Fresh', value: analyticsData.status_breakdown.counts.Fresh, color: STATUS_COLORS.Fresh },
    { name: 'Nearly Spoiled', value: analyticsData.status_breakdown.counts.Nearly_Spoiled, color: STATUS_COLORS.Nearly_Spoiled },
    { name: 'Spoiled', value: analyticsData.status_breakdown.counts.Spoiled, color: STATUS_COLORS.Spoiled },
  ].filter(item => item.value > 0) : [];

  // Prepare Line Chart Data
  const lineData = analyticsData?.daily_trends || [];

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      
      {/* Header with Range Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-500/10 border border-emerald-300 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-400 text-xs font-bold mb-2">
            <BarChart3 className="w-3.5 h-3.5" />
            <span>SQL Aggregated Freshness Metrics</span>
          </div>
          <h1 className="text-3xl font-black text-slate-900 dark:text-white">
            Food Freshness Analytics Dashboard
          </h1>
        </div>

        {/* Range Dropdown / Tab Group */}
        <div className="flex items-center space-x-1.5 bg-slate-200 dark:bg-slate-900/90 p-1.5 rounded-xl border border-slate-300 dark:border-slate-800 self-start sm:self-auto shadow-sm">
          {[
            { id: 'week', label: 'Last 7 Days' },
            { id: 'month', label: 'Last 30 Days' },
            { id: 'all', label: 'All Time' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setRange(tab.id)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                range === tab.id
                  ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-slate-950 shadow-md shadow-emerald-500/20'
                  : 'text-slate-700 dark:text-slate-400 hover:text-slate-950 dark:hover:text-white hover:bg-slate-300 dark:hover:bg-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="py-24 text-center text-slate-500 dark:text-slate-400 flex flex-col items-center space-y-3">
          <RefreshCw className="w-8 h-8 text-emerald-600 dark:text-emerald-400 animate-spin" />
          <span className="text-sm font-semibold">Calculating SQL aggregations and time-series trends...</span>
        </div>
      ) : error ? (
        <div className="glass-panel rounded-3xl p-8 text-center border border-rose-300 dark:border-rose-500/30 text-rose-800 dark:text-rose-300 space-y-3 shadow-lg">
          <AlertTriangle className="w-10 h-10 text-rose-500 mx-auto" />
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">Error loading analytics</h3>
          <p className="text-xs text-slate-600 dark:text-slate-400">{error}</p>
          <button
            onClick={() => fetchAnalytics(range)}
            className="px-4 py-2 rounded-xl bg-slate-900 dark:bg-slate-800 text-xs font-bold text-white shadow"
          >
            Retry
          </button>
        </div>
      ) : analyticsData?.total_scans === 0 ? (
        <div className="glass-panel rounded-3xl p-12 text-center border border-slate-200 dark:border-slate-800 space-y-3 shadow-lg">
          <Calendar className="w-12 h-12 text-slate-400 dark:text-slate-600 mx-auto" />
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">No scans recorded for this period</h3>
          <p className="text-xs text-slate-600 dark:text-slate-400 max-w-md mx-auto font-medium">
            You haven't scanned any food items {rangeLabels[range]}. Try switching to "All Time" or scan new food items using the Scanner tab!
          </p>
        </div>
      ) : (
        <>
          {/* Main Stat Card: Food Wasted Percentage */}
          <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-xl relative overflow-hidden bg-gradient-to-r from-emerald-50 via-white to-teal-50 dark:from-slate-900 dark:via-slate-900 dark:to-slate-950">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
              
              <div className="md:col-span-8 space-y-2">
                <div className="text-xs font-extrabold uppercase tracking-wider text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                  <Flame className="w-4 h-4 text-rose-500" />
                  Food Waste & Preservation Impact
                </div>
                <h2 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white">
                  You've wasted <span className="text-rose-600 dark:text-rose-400 font-mono font-black">{analyticsData.wasted_percentage}%</span> of scanned items {rangeLabels[range]}
                </h2>
                <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                  {analyticsData.wasted_percentage === 0
                    ? '🎉 Incredible job! Zero food waste recorded in this timeframe. All scanned items remain fresh or were consumed in time.'
                    : analyticsData.wasted_percentage < 25
                    ? '🌿 Great preservation rate! Keep checking shelf-life estimates and using Nearly Spoiled rescue recipes to keep waste minimal.'
                    : '⚠️ Spoilage rate is elevated. Make sure to refrigerate produce promptly and utilize recipe suggestions before expiration.'}
                </p>
              </div>

              {/* Total Count Widget */}
              <div className="md:col-span-4 flex md:justify-end">
                <div className="w-full sm:w-auto p-4 sm:p-5 rounded-2xl bg-white dark:bg-slate-950/70 border border-slate-300 dark:border-slate-800 text-center space-y-1 shadow-md">
                  <div className="text-xs text-slate-600 dark:text-slate-400 font-bold">Total Scans Evaluated</div>
                  <div className="text-3xl font-black text-slate-900 dark:text-white font-mono">{analyticsData.total_scans}</div>
                  <div className="text-[11px] text-emerald-700 dark:text-emerald-400 font-bold">SQL Aggregated</div>
                </div>
              </div>

            </div>
          </div>

          {/* Quick Metrics Breakdown */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            
            <div className="glass-panel p-5 rounded-2xl border border-emerald-300 dark:border-emerald-500/20 space-y-2 shadow-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-700 dark:text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4" /> Fresh Ratio
                </span>
                <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-300">
                  {analyticsData.status_breakdown.percentages.Fresh}%
                </span>
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white font-mono">
                {analyticsData.status_breakdown.counts.Fresh} <span className="text-xs text-slate-500 font-normal">items</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full"
                  style={{ width: `${analyticsData.status_breakdown.percentages.Fresh}%` }}
                />
              </div>
            </div>

            <div className="glass-panel p-5 rounded-2xl border border-amber-300 dark:border-amber-500/20 space-y-2 shadow-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4" /> Nearly Spoiled Ratio
                </span>
                <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-300">
                  {analyticsData.status_breakdown.percentages.Nearly_Spoiled}%
                </span>
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white font-mono">
                {analyticsData.status_breakdown.counts.Nearly_Spoiled} <span className="text-xs text-slate-500 font-normal">items</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-amber-500 rounded-full"
                  style={{ width: `${analyticsData.status_breakdown.percentages.Nearly_Spoiled}%` }}
                />
              </div>
            </div>

            <div className="glass-panel p-5 rounded-2xl border border-rose-300 dark:border-rose-500/20 space-y-2 shadow-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-rose-700 dark:text-rose-400 flex items-center gap-1.5">
                  <AlertOctagon className="w-4 h-4" /> Spoiled Ratio
                </span>
                <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-300">
                  {analyticsData.status_breakdown.percentages.Spoiled}%
                </span>
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white font-mono">
                {analyticsData.status_breakdown.counts.Spoiled} <span className="text-xs text-slate-500 font-normal">items</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-rose-500 rounded-full"
                  style={{ width: `${analyticsData.status_breakdown.percentages.Spoiled}%` }}
                />
              </div>
            </div>

          </div>

          {/* Visual Charts Grid (Recharts) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Donut Chart */}
            <div className="lg:col-span-5 glass-panel rounded-3xl p-6 border border-slate-200 dark:border-slate-800 space-y-4 shadow-xl flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <PieIcon className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  Freshness Distribution Ratio
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 font-medium">
                  Proportional share of scanned items by condition
                </p>
              </div>

              <div className="w-full h-64 flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={85}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} stroke={isDark ? '#0b1120' : '#ffffff'} strokeWidth={2} />
                      ))}
                    </Pie>
                    <RechartsTooltip
                      contentStyle={{ 
                        backgroundColor: isDark ? '#0f172a' : '#ffffff', 
                        borderColor: isDark ? '#334155' : '#cbd5e1', 
                        borderRadius: '12px', 
                        fontSize: '12px',
                        color: isDark ? '#f8fafc' : '#0f172a'
                      }}
                      formatter={(val, name) => [`${val} items`, name]}
                    />
                    <Legend 
                      verticalAlign="bottom" 
                      iconType="circle"
                      wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Line / Area Chart */}
            <div className="lg:col-span-7 glass-panel rounded-3xl p-6 border border-slate-200 dark:border-slate-800 space-y-4 shadow-xl flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <TrendingDown className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                  Freshness Trends Over Time
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 font-medium">
                  Daily scan counts grouped by status ({rangeLabels[range]})
                </p>
              </div>

              <div className="w-full h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={lineData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#1e293b' : '#e2e8f0'} />
                    <XAxis 
                      dataKey="date" 
                      stroke={isDark ? '#64748b' : '#475569'} 
                      fontSize={10} 
                      tickFormatter={(d) => d.slice(5)} 
                    />
                    <YAxis stroke={isDark ? '#64748b' : '#475569'} fontSize={10} allowDecimals={false} />
                    <RechartsTooltip
                      contentStyle={{ 
                        backgroundColor: isDark ? '#0f172a' : '#ffffff', 
                        borderColor: isDark ? '#334155' : '#cbd5e1', 
                        borderRadius: '12px', 
                        fontSize: '12px',
                        color: isDark ? '#f8fafc' : '#0f172a'
                      }}
                    />
                    <Legend 
                      verticalAlign="bottom" 
                      iconType="circle"
                      wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="Fresh" 
                      stroke={STATUS_COLORS.Fresh} 
                      strokeWidth={2.5} 
                      dot={{ r: 4, fill: STATUS_COLORS.Fresh }} 
                      activeDot={{ r: 6 }} 
                    />
                    <Line 
                      type="monotone" 
                      dataKey="Nearly_Spoiled" 
                      name="Nearly Spoiled" 
                      stroke={STATUS_COLORS.Nearly_Spoiled} 
                      strokeWidth={2.5} 
                      dot={{ r: 4, fill: STATUS_COLORS.Nearly_Spoiled }} 
                      activeDot={{ r: 6 }} 
                    />
                    <Line 
                      type="monotone" 
                      dataKey="Spoiled" 
                      stroke={STATUS_COLORS.Spoiled} 
                      strokeWidth={2.5} 
                      dot={{ r: 4, fill: STATUS_COLORS.Spoiled }} 
                      activeDot={{ r: 6 }} 
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        </>
      )}

    </div>
  );
};

export default AnalyticsDashboard;
