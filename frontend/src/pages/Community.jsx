import React from 'react';

const COMMUNITIES = [
  {
    icon: '🔴',
    name: 'r/csMajors',
    platform: 'Reddit',
    description: 'The most active CS internship community. Real timelines, offer comparisons, and recruitment season updates.',
    url: 'https://reddit.com/r/csmajors',
    members: '250k+ members',
  },
  {
    icon: '🟠',
    name: 'r/cscareerquestions',
    platform: 'Reddit',
    description: 'Career advice, resume reviews, salary negotiations, and the tech job market pulse.',
    url: 'https://reddit.com/r/cscareerquestions',
    members: '700k+ members',
  },
  {
    icon: '💬',
    name: 'CS Internships',
    platform: 'Discord',
    description: 'Real-time chat about open roles, referral trades, interview debriefs, and offer deadlines.',
    url: 'https://discord.gg/csinternships',
    members: 'Active daily',
  },
  {
    icon: '👁️',
    name: 'Blind',
    platform: 'Blind',
    description: 'Anonymous tech talk — verified employees share insider compensation data, team culture, and hiring signals.',
    url: 'https://www.teamblind.com',
    members: 'Verified employees',
  },
];

const Community = () => {
  return (
    <div style={styles.page}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>Community</h1>
        <p style={styles.subtitle}>
          Connect with thousands of other internship seekers. Join these active communities for
          real-time advice, resume reviews, and networking.
        </p>
      </div>

      {/* Communities Grid */}
      <div style={styles.grid}>
        {COMMUNITIES.map((c) => (
          <a
            key={c.name}
            href={c.url}
            target="_blank"
            rel="noopener noreferrer"
            style={styles.card}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-hover)';
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.07)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border)';
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            <div style={styles.cardTop}>
              <span style={styles.cardIcon}>{c.icon}</span>
              <div>
                <div style={styles.cardName}>{c.name}</div>
                <div style={styles.cardPlatform}>{c.platform}</div>
              </div>
              <span style={styles.externalArrow}>↗</span>
            </div>
            <p style={styles.cardDesc}>{c.description}</p>
            <div style={styles.cardFooter}>
              <span style={styles.memberCount}>{c.members}</span>
            </div>
          </a>
        ))}
      </div>

      {/* Footer note */}
      <p style={styles.footerNote}>
        💡 Tip: Turn on post notifications for r/csMajors during September–November for the best
        early application opportunities.
      </p>
    </div>
  );
};

const styles = {
  page: {
    padding: '32px 40px',
    maxWidth: '900px',
  },
  header: {
    marginBottom: '32px',
  },
  title: {
    fontSize: '28px',
    fontWeight: 700,
    color: 'var(--text-primary)',
    letterSpacing: '-0.5px',
    marginBottom: '8px',
  },
  subtitle: {
    fontSize: '14px',
    color: 'var(--text-secondary)',
    lineHeight: 1.6,
    maxWidth: '580px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))',
    gap: '16px',
    marginBottom: '32px',
  },
  card: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    background: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: '14px',
    padding: '24px',
    textDecoration: 'none',
    transition: 'border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease',
    cursor: 'pointer',
  },
  cardTop: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  cardIcon: {
    fontSize: '28px',
    lineHeight: 1,
    flexShrink: 0,
  },
  cardName: {
    fontSize: '15px',
    fontWeight: 600,
    color: 'var(--text-primary)',
    lineHeight: 1.3,
  },
  cardPlatform: {
    fontSize: '11px',
    fontWeight: 500,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    marginTop: '1px',
  },
  externalArrow: {
    marginLeft: 'auto',
    fontSize: '16px',
    color: 'var(--text-muted)',
    flexShrink: 0,
  },
  cardDesc: {
    fontSize: '13px',
    color: 'var(--text-secondary)',
    lineHeight: 1.55,
    margin: 0,
  },
  cardFooter: {
    paddingTop: '8px',
    borderTop: '1px solid var(--border)',
    marginTop: '4px',
  },
  memberCount: {
    fontSize: '11px',
    fontWeight: 600,
    color: 'var(--accent)',
  },
  footerNote: {
    fontSize: '13px',
    color: 'var(--text-muted)',
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: '10px',
    padding: '14px 18px',
    lineHeight: 1.55,
  },
};

export default Community;
