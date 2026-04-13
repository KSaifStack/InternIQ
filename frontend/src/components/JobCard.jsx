import React from 'react';
import { MapPin, Bookmark } from 'lucide-react';
import { logActivity, createApplication } from '../api';
import DOMPurify from 'dompurify';

const ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'span'];
const ALLOWED_ATTR = [];

const sanitizeDescription = (raw) => {
  if (!raw) return null;
  const clean = DOMPurify.sanitize(raw, { ALLOWED_TAGS, ALLOWED_ATTR });
  return clean || null;
};

const JobCard = ({ job, onSave }) => {
  const getRelativeTime = (dateStr) => {
    if (!dateStr) return 'New';
    const posted = new Date(dateStr);
    const now = new Date();
    const diffMs = now - posted;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 30) return `${Math.floor(diffDays / 30)}mo ago`;
    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    if (diffMins > 0) return `${diffMins}m ago`;
    return 'Just now';
  };

  const handleApplyClick = () => {
    logActivity('apply', job.id).catch(() => {});
  };

  const initials = (name = '') =>
    name.split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase();

  const avatarColors = [
    '#2d7a4f', '#c9952a', '#1a7a3c', '#7c3aed', '#b45309', '#0369a1',
  ];
  const avatarBg = avatarColors[(job.company?.name || '').charCodeAt(0) % avatarColors.length];

  return (
    <div style={styles.card}>
      {/* Header */}
      <div style={styles.cardTop}>
        <div style={styles.companyRow}>
          <div style={{ ...styles.avatar, background: avatarBg }}>
            {initials(job.company?.name || 'UK')}
          </div>
          <div>
            <div style={styles.companyName}>{job.company?.name || 'Unknown Company'}</div>
            <div style={styles.jobTitle}>{job.title}</div>
          </div>
        </div>
      </div>

      {/* Meta */}
      <div style={styles.metaRow}>
        <div style={styles.metaChip}>
          <MapPin size={12} strokeWidth={2} />
          <span>{job.is_remote ? 'Remote' : job.location}</span>
          {job.state && !job.is_remote && (
            <span style={styles.stateTag}>{job.state}</span>
          )}
        </div>
        <span style={styles.postedTime}>{getRelativeTime(job.posted_at)}</span>
      </div>

      {/* Skills */}
      {job.required_skills && (
          <div style={styles.skillsRow}>
            {(job.required_skills || '').split(',').filter(s => s.trim()).map(skill => (
              <span key={skill} style={styles.skillTag}>{skill.trim()}</span>
            ))}
          </div>
      )}

      {/* Description — sanitized HTML render */}
      {sanitizeDescription(job.description) && (
        <p
          style={styles.description}
          dangerouslySetInnerHTML={{ __html: sanitizeDescription(job.description) }}
        />
      )}

      {/* Footer */}
      <div style={styles.footer}>
        <button onClick={() => onSave(job.id)} style={styles.trackBtn}>
          <Bookmark size={13} strokeWidth={2} />
          Track
        </button>
        {job.application_url ? (
          <a
            href={job.application_url}
            target="_blank"
            rel="noreferrer"
            onClick={handleApplyClick}
            style={styles.applyBtn}
          >
            Apply Now
          </a>
        ) : (
          <span style={styles.disabledBtn}>Closed</span>
        )}
      </div>
    </div>
  );
};

const styles = {
  card: {
    background: 'var(--bg-secondary)',
    borderRadius: '14px',
    border: '1px solid var(--border)',
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    transition: 'var(--transition)',
    cursor: 'default',
  },
  cardTop: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '16px',
    gap: '12px',
  },
  companyRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  avatar: {
    width: '38px',
    height: '38px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '12px',
    fontWeight: 600,
    color: '#fff',
    flexShrink: 0,
    fontFamily: "'DM Mono', monospace",
  },
  companyName: {
    fontSize: '12px',
    color: 'var(--text-secondary)',
    fontWeight: 500,
    lineHeight: 1.2,
  },
  jobTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: 'var(--text-primary)',
    marginTop: '2px',
    letterSpacing: '-0.2px',
    lineHeight: 1.4,
  },

  metaRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    marginBottom: '12px',
    flexWrap: 'wrap',
  },
  metaChip: {
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
    fontSize: '12px',
    color: 'var(--text-muted)',
  },
  stateTag: {
    background: 'var(--bg-elevated)',
    color: 'var(--text-muted)',
    fontSize: '10px',
    fontWeight: 600,
    padding: '2px 6px',
    borderRadius: '6px',
    marginLeft: '4px',
    textTransform: 'uppercase',
  },
  postedTime: {
    fontSize: '11px',
    color: 'var(--text-muted)',
    fontFamily: "'DM Mono', monospace",
    marginLeft: 'auto',
  },
  skillsRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
    marginBottom: '16px',
  },
  skillTag: {
    background: 'var(--bg-elevated)',
    color: 'var(--text-secondary)',
    fontSize: '11px',
    fontWeight: 500,
    padding: '4px 10px',
    borderRadius: '6px',
    border: '1px solid var(--border)',
  },
  description: {
    fontSize: '13px',
    color: 'var(--text-secondary)',
    lineHeight: 1.6,
    marginBottom: '12px',
    display: '-webkit-box',
    WebkitLineClamp: 2,
    WebkitBoxOrient: 'vertical',
    overflow: 'hidden',
    flex: 1,
  },
  footer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 'auto',
    paddingTop: '18px',
    borderTop: '1px solid var(--border)',
  },
  trackBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '13px',
    color: 'var(--text-secondary)',
    cursor: 'pointer',
    fontWeight: 500,
    background: 'transparent',
    border: '1px solid var(--border)',
    padding: '6px 12px',
    borderRadius: '8px',
    transition: 'var(--transition)',
  },

  applyBtn: {
    background: 'var(--accent)',
    color: '#fff',
    fontSize: '13px',
    fontWeight: 600,
    padding: '8px 20px',
    borderRadius: '8px',
    textDecoration: 'none',
    cursor: 'pointer',
    transition: 'var(--transition)',
    border: 'none',
  },
  disabledBtn: {
    background: 'var(--bg-elevated)',
    color: 'var(--text-muted)',
    fontSize: '13px',
    fontWeight: 600,
    padding: '8px 20px',
    borderRadius: '8px',
    textDecoration: 'none',
    cursor: 'not-allowed',
  },
};

export default JobCard;
