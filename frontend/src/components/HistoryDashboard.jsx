import React, { useState, useEffect } from 'react';
import { 
  History, Search, Trash2, Calendar, Sparkles, Filter, 
  CheckCircle, AlertTriangle, AlertOctagon, ArrowUpRight, 
  Layers, Clock, RefreshCw, BarChart3, ShieldCheck, X
} from 'lucide-react';
import { historyAPI, getImageUrl } from '../services/api';

const HistoryDashboard = ({ onSelectScan }) => {
  const [historyItems, setHistoryItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItemModal, setSelectedItemModal] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const fetchHistoryAndStats = async () => {
    setLoading(true);
    try {
      const [historyRes, statsRes] = await Promise.all([
        historyAPI.getHistory({
          status_filter: statusFilter === 'all' ? undefined : statusFilter,
          search: searchTerm || undefined,
        }),
        historyAPI.getStats(),
      ]);
      setHistoryItems(historyRes.data.items || []);
      setStats(statsRes.data);
    } catch (err) {
      console.warn('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistoryAndStats();
  }, [statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchHistoryAndStats();
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this scan record from SQLite database?')) return;
    setDeletingId(id);
    try {
      await historyAPI.deleteRecord(id);
      setHistoryItems((prev) => prev.filter((item) => item.id !== id));
      if (selectedItemModal?.id === id) {
        setSelectedItemModal(null);
      }
      const statsRes = await historyAPI.getStats();
      setStats(statsRes.data);
    } catch (err) {
      alert('Failed to delete scan record.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to clear all scan history? This action cannot be undone.')) return;
    try {
      await historyAPI.clearHistory();
      setHistoryItems([]);
      setSelectedItemModal(null);
      const statsRes = await historyAPI.getStats();
      setStats(statsRes.data);
    } catch (err) {
      alert('Failed to clear history.');
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs font-semibold mb-2">
            <History className="w-3.5 h-3.5" />
            <span>SQLite Database History Logs</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white">
            Prediction History & Analytics
          </h1>
        </div>

        {historyItems.length > 0 && (
          <button
            onClick={handleClearAll}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-300 text-xs font-semibold border border-rose-500/30 transition-colors self-start sm:self-auto"
          >
            <Trash2 className="w-4 h-4 text-rose-500 dark:text-rose-400" />
            <span>Clear All History</span>
          </button>
        )}
      </div>

      {/* Analytics Summary Stats Widgets */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          
          <div className="glass-panel p-5 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-1 shadow-lg">
            <div className="text-xs font-semibold text-slate-500 dark:text-slate-400">Total Scans</div>
            <div className="text-2xl font-black text-slate-900 dark:text-white font-mono">{stats.total_scans}</div>
            <div className="text-[11px] text-slate-500">Persistent Records</div>
          </div>

          <div className="glass-panel p-5 rounded-2xl border border-emerald-500/20 space-y-1 shadow-lg">
            <div className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
              <CheckCircle className="w-3.5 h-3.5" /> Fresh Items
            </div>
            <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400 font-mono">{stats.fresh_count}</div>
            <div className="text-[11px] text-slate-500">
              {stats.total_scans > 0 ? Math.round((stats.fresh_count / stats.total_scans) * 100) : 0}% of scans
            </div>
          </div>

          <div className="glass-panel p-5 rounded-2xl border border-amber-500/20 space-y-1 shadow-lg">
            <div className="text-xs font-semibold text-amber-600 dark:text-amber-400 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" /> Nearly Spoiled
            </div>
            <div className="text-2xl font-black text-amber-600 dark:text-amber-400 font-mono">{stats.nearly_spoiled_count}</div>
            <div className="text-[11px] text-slate-500">
              {stats.total_scans > 0 ? Math.round((stats.nearly_spoiled_count / stats.total_scans) * 100) : 0}% of scans
            </div>
          </div>

          <div className="glass-panel p-5 rounded-2xl border border-rose-500/20 space-y-1 shadow-lg">
            <div className="text-xs font-semibold text-rose-600 dark:text-rose-400 flex items-center gap-1.5">
              <AlertOctagon className="w-3.5 h-3.5" /> Spoiled Items
            </div>
            <div className="text-2xl font-black text-rose-600 dark:text-rose-400 font-mono">{stats.spoiled_count}</div>
            <div className="text-[11px] text-slate-500">
              {stats.total_scans > 0 ? Math.round((stats.spoiled_count / stats.total_scans) * 100) : 0}% of scans
            </div>
          </div>

          <div className="glass-panel p-5 rounded-2xl border border-teal-500/20 space-y-1 col-span-2 sm:col-span-1 shadow-lg">
            <div className="text-xs font-semibold text-teal-600 dark:text-teal-400 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" /> Avg Confidence
            </div>
            <div className="text-2xl font-black text-teal-600 dark:text-teal-300 font-mono">{stats.avg_confidence}%</div>
            <div className="text-[11px] text-slate-500">MobileNetV2 Softmax</div>
          </div>

        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-200 dark:border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        
        {/* Status Filter Tabs */}
        <div className="flex items-center space-x-1.5 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
          {[
            { id: 'all', label: 'All Scans' },
            { id: 'Fresh', label: 'Fresh' },
            { id: 'Nearly Spoiled', label: 'Nearly Spoiled' },
            { id: 'Spoiled', label: 'Spoiled' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                statusFilter === tab.id
                  ? 'bg-emerald-500 text-white dark:text-slate-950 shadow-md shadow-emerald-500/20'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-950 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search Form */}
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-72">
          <input
            type="text"
            placeholder="Search by filename..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-white dark:bg-slate-950/70 border border-slate-300 dark:border-slate-800 rounded-xl text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-emerald-500"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
        </form>

      </div>

      {/* Scan Records Grid */}
      {loading ? (
        <div className="py-16 text-center text-slate-400 flex flex-col items-center space-y-3">
          <RefreshCw className="w-8 h-8 text-emerald-500 animate-spin" />
          <span className="text-sm">Loading scan records from SQLite...</span>
        </div>
      ) : historyItems.length === 0 ? (
        <div className="glass-panel rounded-3xl p-12 text-center border border-slate-200 dark:border-slate-800 space-y-3">
          <History className="w-12 h-12 text-slate-400 dark:text-slate-600 mx-auto" />
          <h3 className="text-lg font-bold text-slate-800 dark:text-white">No scan records found</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
            {searchTerm || statusFilter !== 'all'
              ? 'No results match your current filter. Try changing your search query or filter.'
              : 'Scan food images using the Scanner tab to view predictions and shelf-life logs here.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {historyItems.map((item) => {
            const isFresh = item.freshness_status === 'Fresh';
            const isNearly = item.freshness_status === 'Nearly Spoiled';
            const badgeClass = isFresh
              ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/30'
              : isNearly
              ? 'bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30'
              : 'bg-rose-500/15 text-rose-700 dark:text-rose-400 border-rose-500/30';

            return (
              <div
                key={item.id}
                onClick={() => setSelectedItemModal(item)}
                className="glass-panel rounded-2xl p-4 border border-slate-200 dark:border-slate-800 hover:border-emerald-500/40 cursor-pointer group transition-all duration-200 shadow-lg flex flex-col justify-between space-y-4"
              >
                <div>
                  {/* Thumbnail & Header */}
                  <div className="relative rounded-xl overflow-hidden bg-black aspect-video mb-3 flex items-center justify-center">
                    <img
                      src={getImageUrl(item.image_url)}
                      alt={item.original_filename}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-black/70 backdrop-blur-md text-[10px] font-semibold text-white">
                      {item.food_category}
                    </div>
                    <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/80 text-[10px] font-bold font-mono text-emerald-400">
                      {Math.round(item.confidence_score * 100)}% Conf
                    </div>
                  </div>

                  {/* Title & Status */}
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900 dark:text-white line-clamp-1 group-hover:text-emerald-600 dark:group-hover:text-emerald-300 transition-colors">
                        {item.original_filename}
                      </h4>
                      <div className="flex items-center space-x-1.5 text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                        <Calendar className="w-3 h-3 text-slate-400" />
                        <span>{new Date(item.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold border ${badgeClass}`}>
                      {item.freshness_status}
                    </span>
                  </div>
                </div>

                {/* Shelf-Life Info & Delete Action */}
                <div className="pt-3 border-t border-slate-200 dark:border-slate-800/80 flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-1.5 text-slate-700 dark:text-slate-300">
                    <Clock className="w-3.5 h-3.5 text-emerald-500 dark:text-emerald-400" />
                    <span className="font-semibold">
                      {item.shelf_life_days > 0 ? `~${item.shelf_life_days} Days` : '0 Days (Expired)'}
                    </span>
                  </div>

                  <button
                    onClick={(e) => handleDelete(item.id, e)}
                    disabled={deletingId === item.id}
                    title="Delete Scan Record"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-500/10 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>

              </div>
            );
          })}
        </div>
      )}

      {/* Detail Modal */}
      {selectedItemModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-2xl space-y-5">
            
            <button
              onClick={() => setSelectedItemModal(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-900 dark:hover:text-white p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-3">
              <img
                src={getImageUrl(selectedItemModal.image_url)}
                alt={selectedItemModal.original_filename}
                className="w-16 h-16 rounded-2xl object-cover bg-black border border-slate-200 dark:border-slate-800"
              />
              <div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  {selectedItemModal.original_filename}
                </h3>
                <div className="text-xs text-slate-500 dark:text-slate-400">
                  Scanned on {new Date(selectedItemModal.created_at).toLocaleString()}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800">
                <div className="text-slate-500 dark:text-slate-400 mb-0.5">Freshness Status</div>
                <div className="text-sm font-bold text-slate-900 dark:text-white">{selectedItemModal.freshness_status}</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800">
                <div className="text-slate-500 dark:text-slate-400 mb-0.5">AI Confidence</div>
                <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400 font-mono">
                  {Math.round(selectedItemModal.confidence_score * 100)}%
                </div>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 col-span-2">
                <div className="text-slate-500 dark:text-slate-400 mb-0.5">Shelf-Life Window</div>
                <div className="text-sm font-bold text-slate-800 dark:text-slate-200">{selectedItemModal.shelf_life_desc || `${selectedItemModal.shelf_life_days} days`}</div>
              </div>
            </div>

            {selectedItemModal.storage_advice && (
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                <strong className="text-emerald-600 dark:text-emerald-400 block mb-1">Storage Recommendation:</strong>
                {selectedItemModal.storage_advice}
              </div>
            )}

            <div className="flex justify-end space-x-3 pt-2">
              <button
                onClick={(e) => handleDelete(selectedItemModal.id, e)}
                className="px-4 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-300 text-xs font-semibold border border-rose-500/30 flex items-center space-x-1.5 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Delete Record</span>
              </button>
              <button
                onClick={() => setSelectedItemModal(null)}
                className="px-5 py-2 rounded-xl bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-900 dark:text-white text-xs font-semibold transition-colors"
              >
                Close
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
};

export default HistoryDashboard;
