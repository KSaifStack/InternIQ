import React from 'react';

const RESOURCES = [
  {
    icon: '📄',
    title: 'Resume Templates',
    description: 'Battle-tested LaTeX + Word templates used by CS students at top schools.',
    url: 'https://www.overleaf.com/latex/templates?q=software+engineer+resume',
    label: 'Browse Templates →',
  },
  {
    icon: '✉️',
    title: 'Cover Letter Guide',
    description: 'How to write cover letters that actually get read by engineers, not just HR.',
    url: 'https://www.themuse.com/advice/cover-letter-template-and-tips',
    label: 'Read Guide →',
  },
  {
    icon: '🎤',
    title: 'Interview Prep',
    description: 'Curated LeetCode patterns, system design resources, and behavioral question banks.',
    url: 'https://www.techinterviewhandbook.org/',
    label: 'Start Prepping →',
  },
  {
    icon: '💰',
    title: 'Salary & Comp Data',
    description: 'Real compensation data from interns and new grads at hundreds of tech companies.',
    url: 'https://levels.fyi/internships/',
    label: 'View Salaries →',
  },
  {
    icon: '🐙',
    title: 'GitHub Portfolio Guide',
    description: 'Step-by-step guide to building a GitHub profile that makes recruiters stop scrolling.',
    url: 'https://www.freecodecamp.org/news/how-to-build-a-developer-portfolio-website/',
    label: 'Build Portfolio →',
  },
  {
    icon: '🤝',
    title: 'Networking Tips',
    description: 'Cold outreach scripts, LinkedIn optimization, and coffee chat strategies for students.',
    url: 'https://www.linkedin.com/pulse/networking-guide-college-students/',
    label: 'Learn Networking →',
  },
];

const Resources = () => {
  return (
    <div style={styles.page}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>Career Resources</h1>
        <p style={styles.subtitle}>
          Curated guides and tools to maximize your internship search success.
        </p>
      </div>

      {/* Resource Grid */}
      <div style={styles.grid}>
        {RESOURCES.map((r) => (
          <a
            key={r.title}
            href={r.url}
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
            <div style={styles.cardIcon}>{r.icon}</div>
            <div style={styles.cardBody}>
              <div style={styles.cardTitle}>{r.title}</div>
              <div style={styles.cardDesc}>{r.description}</div>
              <div style={styles.cardLink}>{r.label}</div>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
};

const styles = {
  page: {
    padding: '32px 40px',
    maxWidth: '960px',
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
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '16px',
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
  cardIcon: {
    fontSize: '28px',
    lineHeight: 1,
  },
  cardBody: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    flex: 1,
  },
  cardTitle: {
    fontSize: '15px',
    fontWeight: 600,
    color: 'var(--text-primary)',
  },
  cardDesc: {
    fontSize: '13px',
    color: 'var(--text-secondary)',
    lineHeight: 1.55,
    flex: 1,
  },
  cardLink: {
    fontSize: '12px',
    fontWeight: 600,
    color: 'var(--accent)',
    marginTop: '8px',
  },
};

export default Resources;
