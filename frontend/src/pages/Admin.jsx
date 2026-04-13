import React, { useState, useEffect } from 'react';
import {
  FiRefreshCw,
  FiDatabase,
  FiCheckCircle,
  FiAlertCircle,
  FiClock,
  FiBarChart2,
  FiTerminal,
  FiGitBranch,
  FiZap,
} from 'react-icons/fi';
import { getSyncLogs, triggerSync, getPipelineStatus, getSystemHealth } from '../api';

const Admin = () => {
  const [logs, setLogs] = useState([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState(null);
  const [health, setHealth] = useState(null);
  const [stats, setStats] = useState({ active_jobs: 0, jobs_2026: 0, last_sync: null });

  const fetchAll = async () => {
    try {
      const [logData, statusData, healthData] = await Promise.allSettled([
        getSyncLogs(30),
        getPipelineStatus(),
        getSystemHealth(),
      ]);
      if (logData.status === 'fulfilled') setLogs(logData.value);
      if (statusData.status === 'fulfilled') setStats(statusData.value);
      if (healthData.status === 'fulfilled') setHealth(healthData.value);
    } catch (err) {
      console.error('Failed to fetch admin data:', err);
    }
  };

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 15000);
    return () => clearInterval(interval);
  }, []);

  const runSync = async () => {
    setIsSyncing(true);
    setSyncMsg(null);
    try {
      const data = await triggerSync();
      setSyncMsg(data.message || 'Sync started');
      setTimeout(fetchAll, 3000);
    } catch (err) {
      setSyncMsg('Sync request failed');
    } finally {
      setIsSyncing(false);
    }
  };

  const sourceItems = health ? [
    {
      label: 'GitHub (5 repos)',
      icon: FiGitBranch,
      status: 'active',
      detail: `Last sync: ${health.sources?.github?.last_sync ? new Date(health.sources.github.last_sync).toLocaleString() : 'Never'}`,
      color: 'var(--success)',
    },
    {
      label: 'RemoteOK',
      icon: FiZap,
      status: health.sources?.remoteok?.status || 'unknown',
      detail: `Free · Last sync: ${health.sources?.remoteok?.last_sync ? new Date(health.sources.remoteok.last_sync).toLocaleString() : 'Never'}`,
      color: 'var(--success)',
    },
    {
      label: 'JSearch API',
      icon: FiDatabase,
      status: health.sources?.jsearch?.status || 'unknown',
      detail: `${health.sources?.jsearch?.requests_used ?? 0} / ${health.sources?.jsearch?.monthly_limit ?? 200} requests used`,
      color: health.sources?.jsearch?.quota_ok ? 'var(--success)' : 'var(--danger)',
    },
  ] : [];

  return (
    <div style={s.page}>
      {/* Header */}
      <div style={s.header}>
        <div>
          <h1 style={s.title}>Control Center</h1>
          <p style={s.subtitle}>2026 internship discovery — system health &amp; sync status</p>
        </div>
        <button
          id="sync-all-btn"
          onClick={runSync}
          disabled={isSyncing}
          style={{ ...s.syncBtn, opacity: isSyncing ? 0.6 : 1 }}
        >
          <FiRefreshCw style={{ animation: isSyncing ? 'spin 1s linear infinite' : 'none' }} />
          {isSyncing ? 'Syncing...' : 'Sync All Sources'}
        </button>
      </div>

      {syncMsg && <div style={s.syncMsg}>{syncMsg}</div>}

      {/* Stats row */}
      <div style={s.statsGrid}>
        <StatCard
          icon={<FiBarChart2 />}
          label="Active 2026 Jobs"
          value={(stats.jobs_2026 ?? 0).toLocaleString()}
          color="#3b82f6"
        />
        <StatCard
          icon={<FiCheckCircle />}
          label="Total Active Listings"
          value={(stats.active_jobs ?? 0).toLocaleString()}
          color="var(--success)"
        />
        <StatCard
          icon={<FiClock />}
          label="Last Full Sync"
          value={health?.last_full_sync ? new Date(health.last_full_sync).toLocaleTimeString() : '—'}
          color="var(--gold)"
        />
      </div>

      <div style={s.twoCol}>
        {/* Sync Log */}
        <div style={s.card}>
          <div style={s.cardHeader}>
            <FiTerminal style={{ color: '#3b82f6' }} />
            <span>Sync Activity Log</span>
            <button onClick={fetchAll} style={s.refreshBtn}><FiRefreshCw size={14} /></button>
          </div>
          <table style={s.table}>
            <thead>
              <tr style={s.thead}>
                <th style={s.th}>Source</th>
                <th style={s.th}>Time</th>
                <th style={s.th}>New Jobs</th>
                <th style={{ ...s.th, textAlign: 'right' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={4} style={s.empty}>No sync history. Trigger a sync to get started.</td>
                </tr>
              ) : logs.map((log) => (
                <tr key={log.id} style={s.row}>
                  <td style={s.td}>
                    <span style={s.sourceLabel}>{log.source}</span>
                  </td>
                  <td style={s.td}>
                    <div style={s.timeCell}>
                      <FiClock size={12} />
                      {log.ran_at ? new Date(log.ran_at).toLocaleTimeString() : '—'}
                    </div>
                  </td>
                  <td style={s.td}>
                    <span style={s.newCount}>+{log.jobs_added ?? 0}</span>
                  </td>
                  <td style={{ ...s.td, textAlign: 'right' }}>
                    {log.errors ? (
                      <span style={s.badgeError}><FiAlertCircle size={11} /> Error</span>
                    ) : (
                      <span style={s.badgeOk}><FiCheckCircle size={11} /> OK</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Source Health */}
        <div>
          <div style={s.cardHeader}>
            <FiDatabase style={{ color: '#3b82f6' }} />
            <span>Data Sources</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '8px' }}>
            {sourceItems.map((item) => (
              <div key={item.label} style={s.sourceCard}>
                <div style={s.sourceLeft}>
                  <item.icon style={{ color: item.color, flexShrink: 0 }} size={16} />
                  <div>
                    <div style={s.sourceTitle}>{item.label}</div>
                    <div style={s.sourceDetail}>{item.detail}</div>
                  </div>
                </div>
                <span style={{
                  ...s.dot,
                  background: item.status === 'active' || item.status === 'healthy' ? 'var(--success)' :
                              item.status === 'no_key' ? 'var(--gold)' : 'var(--danger)',
                }} />
              </div>
            ))}
            {!health && (
              <div style={s.sourceDetail}>Loading health data…</div>
            )}
          </div>

          {/* DB Stats */}
          {health?.database && (
            <div style={{ ...s.card, marginTop: '20px' }}>
              <div style={s.cardHeader}>
                <FiBarChart2 style={{ color: '#3b82f6' }} />
                <span>Database</span>
              </div>
              <div style={s.dbGrid}>
                {Object.entries(health.database.jobs_by_source || {}).map(([src, cnt]) => (
                  <div key={src} style={s.dbRow}>
                    <span style={s.sourceDetail}>{src}</span>
                    <span style={s.newCount}>{cnt}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
};

const StatCard = ({ icon, label, value, color }) => (
  <div style={s.statCard}>
    <div style={{ ...s.statIcon, color }}>{icon}</div>
    <div style={s.statLabel}>{label}</div>
    <div style={s.statValue}>{value}</div>
  </div>
);

const s = {
  page: {
    maxWidth: '1100px',
    margin: '0 auto',
    padding: '32px 24px 64px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '28px',
    flexWrap: 'wrap',
    gap: '16px',
  },
  title: {
    fontSize: '22px',
    fontWeight: 700,
    color: 'var(--text-primary)',
    letterSpacing: '-0.4px',
    marginBottom: '4px',
  },
  subtitle: {
    fontSize: '13px',
    color: 'var(--text-secondary)',
  },
  syncBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 22px',
    background: 'var(--accent)',
    color: '#fff',
    border: 'none',
    borderRadius: '10px',
    fontSize: '13px',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'var(--transition)',
  },
  syncMsg: {
    padding: '10px 16px',
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: '8px',
    fontSize: '13px',
    color: 'var(--text-secondary)',
    marginBottom: '24px',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginBottom: '28px',
  },
  statCard: {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: '14px',
    padding: '22px',
  },
  statIcon: {
    fontSize: '20px',
    marginBottom: '10px',
  },
  statLabel: {
    fontSize: '11px',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    color: 'var(--text-muted)',
    marginBottom: '6px',
  },
  statValue: {
    fontSize: '28px',
    fontWeight: 700,
    color: 'var(--text-primary)',
    fontVariantNumeric: 'tabular-nums',
  },
  twoCol: {
    display: 'grid',
    gridTemplateColumns: '1.5fr 1fr',
    gap: '24px',
    alignItems: 'start',
  },
  card: {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: '14px',
    overflow: 'hidden',
  },
  cardHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '16px 20px',
    fontSize: '12px',
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    color: 'var(--text-secondary)',
    borderBottom: '1px solid var(--border)',
  },
  refreshBtn: {
    marginLeft: 'auto',
    background: 'none',
    border: 'none',
    color: 'var(--text-muted)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  thead: {
    background: 'var(--bg-elevated)',
  },
  th: {
    padding: '10px 20px',
    fontSize: '10px',
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    color: 'var(--text-muted)',
    textAlign: 'left',
  },
  row: {
    borderTop: '1px solid var(--border)',
  },
  td: {
    padding: '12px 20px',
    fontSize: '13px',
    color: 'var(--text-secondary)',
  },
  empty: {
    padding: '40px',
    textAlign: 'center',
    color: 'var(--text-muted)',
    fontSize: '13px',
    fontStyle: 'italic',
  },
  sourceLabel: {
    fontWeight: 600,
    color: 'var(--text-primary)',
    fontSize: '12px',
  },
  timeCell: {
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
    fontSize: '12px',
  },
  newCount: {
    color: 'var(--success)',
    fontWeight: 700,
    fontSize: '12px',
    fontVariantNumeric: 'tabular-nums',
  },
  badgeOk: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    color: 'var(--success)',
    fontSize: '11px',
    fontWeight: 700,
  },
  badgeError: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    color: 'var(--danger)',
    fontSize: '11px',
    fontWeight: 700,
  },
  sourceCard: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '14px 16px',
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: '10px',
  },
  sourceLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  sourceTitle: {
    fontSize: '13px',
    fontWeight: 600,
    color: 'var(--text-primary)',
  },
  sourceDetail: {
    fontSize: '11px',
    color: 'var(--text-muted)',
    marginTop: '2px',
  },
  dot: {
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    flexShrink: 0,
  },
  dbGrid: {
    padding: '12px 0',
  },
  dbRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '6px 20px',
    fontSize: '12px',
    borderBottom: '1px solid var(--border)',
  },
};

export default Admin;
