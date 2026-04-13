import React, { useState, useEffect } from 'react';
import JobCard from '../components/JobCard';
import { getJobs, getStates, createApplication, getTrendingSearches, getTrendingSkills, logActivity } from '../api';
import { Search, Loader2, TrendingUp, Zap, MapPin, RefreshCw } from 'lucide-react';

const PAGE_SIZE = 100;
const INITIAL_LIMIT = 200;

const STATE_NAMES = {
  CA: 'California', NY: 'New York', TX: 'Texas', WA: 'Washington',
  MA: 'Massachusetts', IL: 'Illinois', GA: 'Georgia', CO: 'Colorado',
  NC: 'North Carolina', FL: 'Florida', PA: 'Pennsylvania', OH: 'Ohio',
  VA: 'Virginia', OR: 'Oregon', MI: 'Michigan', AZ: 'Arizona',
  MN: 'Minnesota', MD: 'Maryland', CT: 'Connecticut', NJ: 'New Jersey',
};

const JobFeed = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [search, setSearch] = useState('');
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [selectedState, setSelectedState] = useState('');
  const [states, setStates] = useState([]);
  const [trending, setTrending] = useState([]);
  const [trendingSkills, setTrendingSkills] = useState([]);
  const [toast, setToast] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStates();
    fetchTrending();
    fetchJobs();
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [remoteOnly, selectedState]);

  const fetchStates = async () => {
    try {
      const data = await getStates();
      setStates(data);
    } catch (e) {
      console.error('Failed to fetch states', e);
    }
  };

  const fetchTrending = async () => {
    try {
      const [searches, skills] = await Promise.all([
        getTrendingSearches(8),
        getTrendingSkills(8),
      ]);
      setTrending(searches);
      setTrendingSkills(skills);
    } catch (e) {
      console.error('Failed to fetch trending data', e);
    }
  };

  const fetchJobs = async () => {
    setLoading(true);
    setHasMore(true);
    setError(null);
    try {
      const data = await getJobs(0, INITIAL_LIMIT, search, remoteOnly, selectedState);
      setJobs(data);
      setHasMore(data.length >= INITIAL_LIMIT);
    } catch (error) {
      console.error('Failed to fetch jobs', error);
      setError('Failed to load jobs. Please try again.');
    }
    setLoading(false);
  };

  const loadMore = async () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    try {
      const data = await getJobs(jobs.length, PAGE_SIZE, search, remoteOnly, selectedState);
      setJobs(prev => [...prev, ...data]);
      setHasMore(data.length >= PAGE_SIZE);
    } catch (error) {
      console.error('Failed to load more jobs', error);
    }
    setLoadingMore(false);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchJobs();
    setTimeout(fetchTrending, 500);
  };

  const handleTrendingClick = (query) => {
    setSearch(query);
    setTimeout(fetchJobs, 100);
  };

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleTrackApplication = async (jobId) => {
    try {
      await createApplication(1, jobId);
      await logActivity('save', jobId);
      showToast('Application saved to tracker!');
      fetchTrending();
    } catch (e) {
      showToast('Application might already be tracked.', 'error');
    }
  };


  return (
    <div style={s.page}>
      {/* Page header */}
      <div style={s.pageHeader}>
        <h1 style={s.pageTitle}>Job Feed</h1>
      </div>

      <div style={{ marginBottom: '24px' }}>
        {/* Search bar */}
        <form onSubmit={handleSearch} style={s.searchRow}>
          <div style={s.searchWrap}>
            <Search size={16} strokeWidth={2} style={s.searchIcon} />
            <input
              id="job-search-input"
              type="text"
              placeholder="Search skills, titles, companies..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={s.searchInput}
            />
          </div>
          <button type="submit" id="job-search-btn" style={s.searchBtn}>
            Search
          </button>
          <button
            type="button"
            onClick={fetchJobs}
            disabled={loading}
            title="Refresh job listings"
            style={{ ...s.iconBtn, opacity: loading ? 0.5 : 1 }}
          >
            <RefreshCw size={15} strokeWidth={2} style={{ display: 'block', animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          </button>
        </form>

        {/* Filters row */}
        <div style={s.filtersRow}>
          <div style={s.filterItem}>
            <MapPin size={13} strokeWidth={2} style={{ color: '#999' }} />
            <select
              id="state-filter"
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
              style={s.select}
            >
              <option value="">All States</option>
              {states.map(st => (
                <option key={st} value={st}>{STATE_NAMES[st] || st}</option>
              ))}
            </select>
          </div>

          <label style={s.checkboxLabel}>
            <input
              id="remote-only-checkbox"
              type="checkbox"
              checked={remoteOnly}
              onChange={(e) => setRemoteOnly(e.target.checked)}
              style={s.checkbox}
            />
            Remote only
          </label>

          <span style={s.resultCount}>
            {loading ? '—' : `${jobs.length} job${jobs.length !== 1 ? 's' : ''} found`}
          </span>
        </div>
      </div>

      {/* Trending sections */}
      {(trending.length > 0 || trendingSkills.length > 0) && (
        <div style={s.trendingGrid}>
          {trending.length > 0 && (
            <div style={s.trendingBlock}>
              <div style={s.trendingLabel}>
                <TrendingUp size={13} strokeWidth={2} style={{ color: '#3b82f6' }} />
                <span>Trending searches</span>
              </div>
              <div style={s.pillRow}>
                {trending.map((t, i) => (
                  <button key={i} onClick={() => handleTrendingClick(t.query)} style={s.pill}>
                    {t.query}
                    <span style={s.pillCount}>{t.count}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {trendingSkills.length > 0 && (
            <div style={s.trendingBlock}>
              <div style={s.trendingLabel}>
                <Zap size={13} strokeWidth={2} style={{ color: '#1a7a3c' }} />
                <span>In-demand skills</span>
              </div>
              <div style={s.pillRow}>
                {trendingSkills.map((sk, i) => (
                  <button key={i} onClick={() => handleTrendingClick(sk.skill)} style={{ ...s.pill, ...s.pillGreen }}>
                    {sk.skill}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Job grid */}
      {loading ? (
        <div style={s.loadingWrap}>
          <Loader2 size={24} strokeWidth={2} style={{ animation: 'spin 1s linear infinite', color: '#3b82f6' }} />
        </div>
      ) : error ? (
        <div style={{ ...s.empty, color: '#c0392b' }}>{error}</div>
      ) : jobs.length === 0 ? (
        <div style={s.empty}>No jobs found matching your criteria.</div>
      ) : (
        <>
          <div style={s.grid}>
            {jobs.map(job => (
              <JobCard key={job.id} job={job} onSave={handleTrackApplication} />
            ))}
          </div>

          {hasMore && (
            <div style={s.loadMoreWrap}>
              <button
                type="button"
                onClick={loadMore}
                disabled={loadingMore}
                style={{ ...s.loadMoreBtn, opacity: loadingMore ? 0.6 : 1 }}
              >
                {loadingMore
                  ? <><Loader2 size={15} strokeWidth={2} style={{ animation: 'spin 1s linear infinite' }} /> Loading…</>
                  : 'Load more jobs'}
              </button>
            </div>
          )}
        </>
      )}

      {/* Toast */}
      {toast && (
        <div style={{
          ...s.toast,
          background: toast.type === 'success' ? '#1a7a3c' : '#b91c1c',
        }}>
          {toast.message}
        </div>
      )}

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
};

const s = {
  page: {
    maxWidth: '960px',
    margin: '0 auto',
    padding: '32px 24px 64px',
    background: 'var(--bg-primary)',
  },
  pageHeader: {
    marginBottom: '24px',
  },
  pageTitle: {
    fontSize: '22px',
    fontWeight: 600,
    color: 'var(--text-primary)',
    letterSpacing: '-0.4px',
    marginBottom: '16px',
  },

  /* Search */
  searchRow: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
    marginBottom: '14px',
  },
  searchWrap: {
    flex: 1,
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  },
  searchIcon: {
    position: 'absolute',
    left: '12px',
    color: 'var(--text-muted)',
    pointerEvents: 'none',
  },
  searchInput: {
    width: '100%',
    paddingLeft: '36px',
    paddingRight: '14px',
    height: '38px',
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-button)',
    fontSize: '13.5px',
    color: 'var(--text-primary)',
    outline: 'none',
    transition: 'var(--transition)',
  },
  searchBtn: {
    height: '38px',
    padding: '0 18px',
    background: 'var(--accent)',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    fontSize: '13px',
    fontWeight: 500,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    transition: 'var(--transition)',
  },
  iconBtn: {
    width: '38px',
    height: '38px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-button)',
    cursor: 'pointer',
    color: 'var(--text-secondary)',
    flexShrink: 0,
    transition: 'var(--transition)',
  },

  /* Filters */
  filtersRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    flexWrap: 'wrap',
  },
  filterItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  select: {
    height: '32px',
    padding: '0 10px',
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: '8px',
    fontSize: '13px',
    color: 'var(--text-primary)',
    outline: 'none',
    cursor: 'pointer',
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '7px',
    fontSize: '12.5px',
    color: 'var(--text-secondary)',
    cursor: 'pointer',
    userSelect: 'none',
  },
  checkbox: {
    width: '14px',
    height: '14px',
    accentColor: 'var(--accent)',
    cursor: 'pointer',
  },
  resultCount: {
    fontSize: '12px',
    color: 'var(--text-muted)',
    fontFamily: "'DM Mono', monospace",
    marginLeft: 'auto',
  },

  /* Trending */
  trendingGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '12px',
    marginBottom: '24px',
  },
  trendingBlock: {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-card)',
    padding: '14px 16px',
  },
  trendingLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '12px',
    fontWeight: 500,
    color: 'var(--text-secondary)',
    marginBottom: '10px',
  },
  pillRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
  },
  pill: {
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
    height: '28px',
    padding: '0 10px',
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: '20px',
    fontSize: '12px',
    color: 'var(--text-secondary)',
    cursor: 'pointer',
    transition: 'var(--transition)',
  },
  pillGreen: {
    color: 'var(--success)',
    background: 'rgba(34, 197, 94, 0.1)',
    borderColor: 'transparent',
  },
  pillCount: {
    fontSize: '10.5px',
    color: 'var(--text-muted)',
    fontFamily: "'DM Mono', monospace",
  },

  /* Grid */
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '14px',
  },
  loadingWrap: {
    display: 'flex',
    justifyContent: 'center',
    padding: '64px 0',
  },
  empty: {
    textAlign: 'center',
    padding: '64px 0',
    fontSize: '14px',
    color: 'var(--text-muted)',
  },
  loadMoreWrap: {
    display: 'flex',
    justifyContent: 'center',
    paddingTop: '28px',
  },
  loadMoreBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    height: '38px',
    padding: '0 24px',
    background: 'var(--bg-secondary)',
    color: 'var(--text-primary)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-button)',
    fontSize: '13px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'var(--transition)',
  },

  /* Toast */
  toast: {
    position: 'fixed',
    bottom: '24px',
    right: '24px',
    padding: '10px 18px',
    borderRadius: 'var(--radius-button)',
    fontSize: '13px',
    fontWeight: 500,
    color: '#fff',
    zIndex: 50,
    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
  },
};

const sh = {
  cloudBox: {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-card)',
    padding: '14px',
    marginBottom: '16px',
    boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
  },
  cloudTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '11px',
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.6px',
    color: 'var(--text-muted)',
  },
  pillGrid: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
  },
  cloudPill: {
    padding: '6px 14px',
    background: 'var(--bg-elevated)',
    borderRadius: 'var(--radius-badge)',
    fontSize: '12px',
    fontWeight: 500,
    cursor: 'pointer',
    textDecoration: 'none',
    transition: 'var(--transition)',
    display: 'inline-block',
    border: '1px solid var(--border)',
    color: 'var(--text-primary)',
  },
  closeCloud: {
    border: 'none',
    background: 'none',
    fontSize: '18px',
    color: 'var(--text-muted)',
    cursor: 'pointer',
    padding: '0 5px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  progressContainer: {
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-card)',
    padding: '16px',
    marginBottom: '20px',
    boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
  },
  progressBarBg: {
    width: '100%',
    height: '8px',
    background: 'var(--bg-elevated)',
    borderRadius: '10px',
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    transition: 'width 0.4s ease-out',
  },
  dismissProgress: {
    marginTop: '12px',
    fontSize: '11px',
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: 0,
    textDecoration: 'underline',
  }
};

export default JobFeed;