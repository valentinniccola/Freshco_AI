import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, Users, Activity, AlertTriangle, CheckCircle, Search, 
  Filter, Eye, UserX, UserCheck, Clock, RefreshCw, Layers, ShieldAlert,
  ChevronRight, X, Calendar, Phone, Mail, Award, Lock, Sparkles
} from 'lucide-react';
import { adminAPI, getImageUrl } from '../services/api';
import { useAuth } from '../context/AuthContext';

const AdminDashboard = () => {
  const { user, isAdmin } = useAuth();

  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeSubTab, setActiveSubTab] = useState('users'); // 'users' or 'logs'

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Selected User for Detail Drawer
  const [selectedUserDetail, setSelectedUserDetail] = useState(null);
  const [loadingUserDetail, setLoadingUserDetail] = useState(false);

  // Status Toggle Confirmation Modal
  const [statusModalUser, setStatusModalUser] = useState(null);
  const [actionReason, setActionReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Alert message
  const [alertMsg, setAlertMsg] = useState(null);

  useEffect(() => {
    if (isAdmin) {
      fetchAdminData();
    }
  }, [isAdmin, statusFilter]);

  const fetchAdminData = async () => {
    setLoading(true);
    try {
      const [statsRes, usersRes, logsRes] = await Promise.all([
        adminAPI.getStats(),
        adminAPI.getUsers({ status_filter: statusFilter }),
        adminAPI.getLogs(50),
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data);
      setLogs(logsRes.data);
    } catch (err) {
      console.error('Failed to load admin data:', err);
      setAlertMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to load administrator data. Check connection.'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleOpenUserDetail = async (userId) => {
    setLoadingUserDetail(true);
    try {
      const res = await adminAPI.getUserDetail(userId);
      setSelectedUserDetail(res.data);
    } catch (err) {
      setAlertMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to load user details.'
      });
    } finally {
      setLoadingUserDetail(false);
    }
  };

  const handleToggleStatus = async () => {
    if (!statusModalUser) return;
    setActionLoading(true);
    const newStatus = !statusModalUser.is_active;

    try {
      await adminAPI.toggleUserStatus(statusModalUser.id, {
        is_active: newStatus,
        reason: actionReason || (newStatus ? 'Account re-activated by admin' : 'Account suspended by admin')
      });
      
      setAlertMsg({
        type: 'success',
        text: `User ${statusModalUser.username} has been ${newStatus ? 're-activated' : 'suspended'} successfully.`
      });

      setStatusModalUser(null);
      setActionReason('');
      fetchAdminData();

      if (selectedUserDetail && selectedUserDetail.user.id === statusModalUser.id) {
        handleOpenUserDetail(statusModalUser.id);
      }
    } catch (err) {
      setAlertMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to update user status.'
      });
    } finally {
      setActionLoading(false);
    }
  };

  if (!isAdmin) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-4 animate-fade-in">
        <div className="w-16 h-16 rounded-2xl bg-rose-100 dark:bg-rose-500/10 border border-rose-300 dark:border-rose-500/30 flex items-center justify-center mx-auto text-rose-600 dark:text-rose-400">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-black text-slate-900 dark:text-white">
          Administrator Access Required
        </h2>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          This area is restricted to system administrators. Please sign in with an authorized administrator account to view platform diagnostics and user management.
        </p>
      </div>
    );
  }

  const filteredUsers = users.filter((u) => {
    const q = searchQuery.toLowerCase();
    return (
      u.username.toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q) ||
      (u.phone_number && u.phone_number.toLowerCase().includes(q))
    );
  });

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-fade-in">
      
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-500/10 border border-emerald-300 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-400 text-xs font-bold mb-2">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Master Admin Console</span>
          </div>
          <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">
            Platform Administration & Management
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">
            Monitor platform-wide food freshness metrics, manage user accounts, and review audit logs.
          </p>
        </div>

        <button
          onClick={fetchAdminData}
          disabled={loading}
          className="self-start md:self-auto px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold border border-slate-700 flex items-center space-x-2 shadow-sm transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-emerald-400 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* Global Alert Notification */}
      {alertMsg && (
        <div className={`p-4 rounded-2xl border flex items-center justify-between text-xs sm:text-sm font-semibold shadow-md ${
          alertMsg.type === 'success'
            ? 'bg-emerald-50 dark:bg-emerald-500/10 border-emerald-300 dark:border-emerald-500/40 text-emerald-900 dark:text-emerald-300'
            : 'bg-rose-50 dark:bg-rose-500/10 border-rose-300 dark:border-rose-500/40 text-rose-900 dark:text-rose-300'
        }`}>
          <div className="flex items-center space-x-2">
            {alertMsg.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
            <span>{alertMsg.text}</span>
          </div>
          <button onClick={() => setAlertMsg(null)} className="p-1 hover:opacity-75">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Top Platform Metric Cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          
          <div className="glass-panel p-5 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-lg space-y-2">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-bold">
              <span>Total Registered Users</span>
              <Users className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white font-mono">
              {stats.total_users}
            </div>
            <div className="text-[11px] text-slate-600 dark:text-slate-400 flex items-center gap-1.5 font-medium">
              <span className="text-emerald-600 font-bold">{stats.active_users} Active</span>
              <span>•</span>
              <span className="text-rose-500 font-bold">{stats.disabled_users} Suspended</span>
            </div>
          </div>

          <div className="glass-panel p-5 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-lg space-y-2">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-bold">
              <span>Platform-Wide Scans</span>
              <Activity className="w-4 h-4 text-teal-600 dark:text-teal-400" />
            </div>
            <div className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white font-mono">
              {stats.total_scans_platform}
            </div>
            <div className="text-[11px] text-slate-500 font-medium">
              Total AI freshness inferences recorded
            </div>
          </div>

          <div className="glass-panel p-5 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-lg space-y-2">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-bold">
              <span>System Fresh Ratio</span>
              <Award className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div className="text-2xl sm:text-3xl font-black text-emerald-600 dark:text-emerald-400 font-mono">
              {stats.platform_fresh_pct}%
            </div>
            <div className="text-[11px] text-slate-500 font-medium">
              {stats.platform_nearly_spoiled_pct}% Nearly Spoiled • {stats.platform_spoiled_pct}% Spoiled
            </div>
          </div>

          <div className="glass-panel p-5 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-lg space-y-2">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-bold">
              <span>Food Waste Prevented</span>
              <Sparkles className="w-4 h-4 text-amber-500 dark:text-amber-400" />
            </div>
            <div className="text-2xl sm:text-3xl font-black text-amber-600 dark:text-amber-400 font-mono">
              {stats.total_waste_prevented_est} Items
            </div>
            <div className="text-[11px] text-slate-500 font-medium">
              Rescued from landfill via timely consumption
            </div>
          </div>

        </div>
      )}

      {/* Sub-Tabs: Users Directory vs Audit Logs */}
      <div className="flex items-center space-x-2 border-b border-slate-200 dark:border-slate-800 pb-3">
        <button
          onClick={() => setActiveSubTab('users')}
          className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
            activeSubTab === 'users'
              ? 'bg-emerald-500 text-white dark:text-slate-950 shadow-md shadow-emerald-500/20'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-900'
          }`}
        >
          User Accounts Directory ({users.length})
        </button>
        <button
          onClick={() => setActiveSubTab('logs')}
          className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
            activeSubTab === 'logs'
              ? 'bg-emerald-500 text-white dark:text-slate-950 shadow-md shadow-emerald-500/20'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-900'
          }`}
        >
          Security Audit Logs ({logs.length})
        </button>
      </div>

      {/* Sub-Tab 1: Users Directory */}
      {activeSubTab === 'users' && (
        <div className="glass-panel rounded-3xl p-6 border border-slate-200 dark:border-slate-800 space-y-5 shadow-xl">
          
          {/* Filter & Search Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search by username, email, phone..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-800 text-xs font-semibold text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div className="flex items-center space-x-2 w-full sm:w-auto">
              <span className="text-xs font-bold text-slate-500 flex items-center gap-1">
                <Filter className="w-3.5 h-3.5" /> Status:
              </span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-800 text-xs font-semibold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="all">All Accounts</option>
                <option value="active">Active Only</option>
                <option value="disabled">Suspended Only</option>
              </select>
            </div>
          </div>

          {/* User Table */}
          <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-100 dark:bg-slate-900/80 border-b border-slate-200 dark:border-slate-800 text-[11px] font-extrabold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Phone Number</th>
                  <th className="py-3 px-4">Registered</th>
                  <th className="py-3 px-4">Total Scans</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-xs">
                {filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="py-8 text-center text-slate-500 font-medium">
                      No users match the search criteria.
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors">
                      
                      {/* User Info */}
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-bold flex items-center justify-center shrink-0">
                            {u.avatar_url ? (
                              <img src={u.avatar_url} alt="" className="w-full h-full rounded-full object-cover" />
                            ) : (
                              u.username.charAt(0).toUpperCase()
                            )}
                          </div>
                          <div>
                            <span className="font-extrabold text-slate-900 dark:text-white block">
                              {u.username}
                            </span>
                            <span className="text-[11px] text-slate-500 flex items-center gap-1 font-medium">
                              <Mail className="w-3 h-3" /> {u.email}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Role Badge */}
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider ${
                          u.role === 'admin'
                            ? 'bg-purple-100 dark:bg-purple-500/20 text-purple-800 dark:text-purple-300 border border-purple-300 dark:border-purple-500/40'
                            : 'bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                        }`}>
                          {u.role}
                        </span>
                      </td>

                      {/* Phone */}
                      <td className="py-3 px-4 text-slate-600 dark:text-slate-400 font-medium">
                        {u.phone_number || <span className="text-slate-400 italic">None</span>}
                      </td>

                      {/* Registered Date */}
                      <td className="py-3 px-4 text-slate-600 dark:text-slate-400 font-medium">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>

                      {/* Scans Count */}
                      <td className="py-3 px-4">
                        <span className="font-black text-slate-900 dark:text-white font-mono">
                          {u.total_scans}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          u.is_active
                            ? 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-300'
                            : 'bg-rose-100 dark:bg-rose-500/20 text-rose-800 dark:text-rose-300'
                        }`}>
                          {u.is_active ? 'Active' : 'Suspended'}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => handleOpenUserDetail(u.id)}
                            title="View User Scans & History"
                            className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
                          >
                            <Eye className="w-4 h-4" />
                          </button>

                          {u.id !== user?.id && (
                            <button
                              onClick={() => setStatusModalUser(u)}
                              title={u.is_active ? 'Suspend Account' : 'Re-activate Account'}
                              className={`p-1.5 rounded-lg transition-colors ${
                                u.is_active
                                  ? 'bg-rose-100 dark:bg-rose-500/20 hover:bg-rose-200 dark:hover:bg-rose-500/30 text-rose-600 dark:text-rose-400'
                                  : 'bg-emerald-100 dark:bg-emerald-500/20 hover:bg-emerald-200 dark:hover:bg-emerald-500/30 text-emerald-600 dark:text-emerald-400'
                              }`}
                            >
                              {u.is_active ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                            </button>
                          )}
                        </div>
                      </td>

                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

        </div>
      )}

      {/* Sub-Tab 2: Security Audit Logs */}
      {activeSubTab === 'logs' && (
        <div className="glass-panel rounded-3xl p-6 border border-slate-200 dark:border-slate-800 space-y-4 shadow-xl">
          <h3 className="text-sm font-extrabold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-2">
            <Lock className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            Administrative Action Audit Log Trail
          </h3>

          <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-100 dark:bg-slate-900/80 border-b border-slate-200 dark:border-slate-800 text-[11px] font-extrabold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Admin</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Target User</th>
                  <th className="py-3 px-4">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-xs">
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="py-8 text-center text-slate-500 font-medium">
                      No administrative actions logged yet.
                    </td>
                  </tr>
                ) : (
                  logs.map((l) => (
                    <tr key={l.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50">
                      <td className="py-3 px-4 text-slate-500 font-mono text-[11px]">
                        {new Date(l.created_at).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-900 dark:text-white">
                        {l.admin_username}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 font-mono font-bold text-[10px] text-slate-800 dark:text-slate-200">
                          {l.action}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-700 dark:text-slate-300 font-medium">
                        {l.target_username ? `@${l.target_username}` : `User #${l.target_user_id || 'N/A'}`}
                      </td>
                      <td className="py-3 px-4 text-slate-600 dark:text-slate-400 text-[11px]">
                        {l.details}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* USER DETAIL SLIDE-OVER DRAWER */}
      {selectedUserDetail && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/60 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-2xl bg-white dark:bg-slate-950 h-full border-l border-slate-200 dark:border-slate-800 shadow-2xl overflow-y-auto p-6 sm:p-8 space-y-6">
            
            <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-black text-lg flex items-center justify-center">
                  {selectedUserDetail.user.username.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h3 className="text-xl font-black text-slate-900 dark:text-white">
                    {selectedUserDetail.user.username}
                  </h3>
                  <p className="text-xs text-slate-500 flex items-center gap-2">
                    <span>{selectedUserDetail.user.email}</span>
                    <span>•</span>
                    <span className="font-bold text-emerald-600 capitalize">{selectedUserDetail.user.role}</span>
                  </p>
                </div>
              </div>

              <button
                onClick={() => setSelectedUserDetail(null)}
                className="p-2 rounded-xl bg-slate-100 dark:bg-slate-900 hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Quick Metadata */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <span className="text-slate-500 block text-[10px] font-bold uppercase">Account Status</span>
                <span className={`font-bold ${selectedUserDetail.user.is_active ? 'text-emerald-600' : 'text-rose-600'}`}>
                  {selectedUserDetail.user.is_active ? 'Active' : 'Suspended'}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <span className="text-slate-500 block text-[10px] font-bold uppercase">Phone Number</span>
                <span className="font-semibold text-slate-900 dark:text-white">
                  {selectedUserDetail.user.phone_number || 'None'}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <span className="text-slate-500 block text-[10px] font-bold uppercase">Total Lifetime Scans</span>
                <span className="font-black text-slate-900 dark:text-white font-mono">
                  {selectedUserDetail.scans.length}
                </span>
              </div>
            </div>

            {/* Scans List */}
            <div className="space-y-4">
              <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center justify-between">
                <span>Scan History & Inferences ({selectedUserDetail.scans.length})</span>
              </h4>

              {selectedUserDetail.scans.length === 0 ? (
                <div className="py-8 text-center text-slate-500 text-xs border border-dashed rounded-2xl">
                  This user has not scanned any food items yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {selectedUserDetail.scans.map((scan) => (
                    <div
                      key={scan.id}
                      className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 flex items-center space-x-4 shadow-sm"
                    >
                      <img
                        src={getImageUrl(scan.image_url)}
                        alt=""
                        className="w-16 h-16 rounded-xl object-cover bg-black shrink-0 border border-slate-300 dark:border-slate-800"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-black ${
                            scan.freshness_status === 'Fresh'
                              ? 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-300'
                              : scan.freshness_status === 'Nearly Spoiled'
                              ? 'bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300'
                              : 'bg-rose-100 dark:bg-rose-500/20 text-rose-800 dark:text-rose-300'
                          }`}>
                            {scan.freshness_status}
                          </span>
                          <span className="text-[10px] font-bold text-slate-500 font-mono">
                            {Math.round(scan.confidence_score * 100)}% Confident
                          </span>
                        </div>
                        <h5 className="text-xs font-bold text-slate-900 dark:text-white truncate">
                          {scan.original_filename}
                        </h5>
                        <p className="text-[11px] text-slate-500 flex items-center gap-2 mt-0.5">
                          <span className="capitalize">{scan.food_type} ({scan.food_category})</span>
                          <span>•</span>
                          <span>{new Date(scan.created_at).toLocaleString()}</span>
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>
        </div>
      )}

      {/* SUSPENSION / ACTIVATION CONFIRMATION MODAL */}
      {statusModalUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fade-in">
          <div className="max-w-md w-full glass-panel rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-2xl space-y-4">
            <div className="flex items-center space-x-3 text-amber-600 dark:text-amber-400">
              <AlertTriangle className="w-6 h-6" />
              <h3 className="text-lg font-black text-slate-900 dark:text-white">
                {statusModalUser.is_active ? 'Suspend User Account' : 'Re-activate User Account'}
              </h3>
            </div>

            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed font-medium">
              Are you sure you want to {statusModalUser.is_active ? 'suspend' : 're-activate'} the account for <strong>{statusModalUser.username}</strong> ({statusModalUser.email})? 
              {statusModalUser.is_active && ' Suspended users are immediately blocked from logging in and accessing endpoints.'}
            </p>

            <div>
              <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1">
                Reason for Audit Trail (Optional):
              </label>
              <textarea
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                placeholder="e.g. Terms violation, requested deactivation..."
                rows="2"
                className="w-full p-2.5 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-800 text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={() => setStatusModalUser(null)}
                disabled={actionLoading}
                className="px-4 py-2 rounded-xl bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-300 text-xs font-bold transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleToggleStatus}
                disabled={actionLoading}
                className={`px-5 py-2 rounded-xl text-white text-xs font-extrabold shadow-md transition-all flex items-center space-x-2 ${
                  statusModalUser.is_active
                    ? 'bg-rose-600 hover:bg-rose-700'
                    : 'bg-emerald-600 hover:bg-emerald-700'
                }`}
              >
                {actionLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                <span>{statusModalUser.is_active ? 'Confirm Suspension' : 'Confirm Activation'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default AdminDashboard;
