import React, { useState, useEffect } from 'react';
import { getApplications, updateApplication } from '../api';
import { Loader2, ExternalLink } from 'lucide-react';

const statuses = ['saved', 'applied', 'interviewing', 'offered', 'rejected'];
const statusColors = {
  saved: 'rgba(136, 136, 136, 0.1) text-[#888888] border-[#88888833]',
  applied: 'var(--accent-subtle) text-[var(--accent)] border-[rgba(59,130,246,0.2)]',
  interviewing: 'rgba(245, 158, 11, 0.1) text-[#f59e0b] border-[#f59e0b33]',
  offered: 'rgba(34, 197, 94, 0.1) text-[#22c55e] border-[#22c55e33]',
  rejected: 'rgba(239, 68, 68, 0.1) text-[#ef4444] border-[#ef444433]'
};

const ApplicationTracker = () => {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    try {
      const data = await getApplications(1); // Hardcoded user 1 for MVP
      setApplications(data);
    } catch (error) {
      console.error("Failed to fetch applications", error);
    }
    setLoading(false);
  };

  const handleStatusChange = async (appId, newStatus) => {
    try {
      await updateApplication(appId, newStatus);
      setApplications(applications.map(app => 
        app.id === appId ? { ...app, status: newStatus } : app
      ));
    } catch (e) {
      console.error("Failed to update status", e);
    }
  };

  return (
    <div className="w-full max-w-full space-y-8 p-6 box-border">
      {/* Header Stat Panel */}
      <div className="w-full box-border flex flex-col md:flex-row justify-between items-start md:items-center bg-[var(--bg-secondary)] p-8 rounded-[var(--radius-card)] border border-[var(--border)] shadow-2xl overflow-hidden">
        <div className="mb-6 md:mb-0">
          <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight">Application Tracker</h1>
          <p className="text-[var(--text-secondary)] mt-1">Real-time status tracking for your candidate pipeline.</p>
        </div>
        <div className="flex gap-8 flex-shrink-0">
          <div className="text-center">
            <span className="block text-4xl font-black text-[var(--accent)]">{applications.length}</span>
            <span className="text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-[0.2em]">Total</span>
          </div>
          <div className="text-center pl-8 border-l border-[var(--border)]">
            <span className="block text-4xl font-black text-[var(--accent)]">
              {applications.filter(a => a.status === 'interviewing').length}
            </span>
            <span className="text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-[0.2em]">Interviews</span>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="w-10 h-10 animate-spin text-[var(--accent)]" /></div>
      ) : (
        <div className="bg-[var(--bg-secondary)] rounded-[var(--radius-card)] border border-[var(--border)] overflow-hidden shadow-xl">
          <table className="w-full text-left">
            <thead className="bg-[var(--bg-elevated)] text-[var(--text-secondary)] text-[11px] uppercase tracking-widest">
              <tr>
                <th className="py-5 px-8 font-bold">Company</th>
                <th className="py-5 px-8 font-bold">Role</th>
                <th className="py-5 px-8 font-bold">Saved</th>
                <th className="py-5 px-8 font-bold">Current Status</th>
                <th className="py-5 px-8 font-bold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {applications.map(app => (
                <tr key={app.id} className="hover:bg-[var(--bg-elevated)] transition-colors group">
                  <td className="py-5 px-8 font-bold text-[var(--text-primary)]">{app.job.company.name}</td>
                  <td className="py-5 px-8 text-[var(--text-secondary)]">{app.job.title}</td>
                  <td className="py-5 px-8 text-[var(--text-muted)] text-xs font-mono">
                    {new Date(app.job.posted_at).toLocaleDateString()}
                  </td>
                  <td className="py-5 px-8">
                    <div className="relative inline-block">
                      <select 
                        id={`status-select-${app.id}`}
                        value={app.status} 
                        onChange={(e) => handleStatusChange(app.id, e.target.value)}
                        className={`text-[11px] font-black uppercase tracking-tighter rounded-[var(--radius-badge)] px-3 py-1.5 border border-transparent focus:ring-0 cursor-pointer appearance-none ${statusColors[app.status]}`}
                      >
                        {statuses.map(s => (
                          <option key={s} value={s} className="bg-[var(--bg-secondary)] text-[var(--text-primary)]">
                            {s.toUpperCase()}
                          </option>
                        ))}
                      </select>
                    </div>
                  </td>
                  <td className="py-5 px-8 text-right">
                    <a 
                      id={`view-job-${app.id}`}
                      href={app.job.application_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center text-[var(--accent)] hover:text-[var(--accent-hover)] text-xs font-bold transition-all transform hover:translate-x-1"
                    >
                      VIEW LISTING <ExternalLink className="w-3 h-3 ml-2" />
                    </a>
                  </td>
                </tr>
              ))}
              {applications.length === 0 && (
                <tr>
                  <td colSpan="5" className="py-24 text-center text-[var(--text-muted)] italic text-sm">
                    Your pipeline is empty. Start saving jobs from the feed!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ApplicationTracker;
