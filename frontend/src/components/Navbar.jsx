import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Briefcase, User, Layers, Activity, BookOpen, Users } from 'lucide-react';

const NAV_ITEMS = [
  { path: '/',           label: 'Job Feed',   icon: Briefcase, id: 'nav-job-feed'   },
  { path: '/tracker',   label: 'Tracker',    icon: Layers,    id: 'nav-tracker'    },
  { path: '/resources', label: 'Resources',  icon: BookOpen,  id: 'nav-resources'  },
  { path: '/community', label: 'Community',  icon: Users,     id: 'nav-community'  },
  { path: '/profile',   label: 'Profile',    icon: User,      id: 'nav-profile'    },
  { path: '/admin',     label: 'Admin',      icon: Activity,  id: 'nav-admin'      },
];

const Navbar = () => {
  const location = useLocation();

  return (
    <nav style={styles.nav}>
      {/* Logo */}
      <div style={styles.logoWrap}>
        <span style={styles.logoText}>
          InternIQ<span style={styles.logoDot}>.</span>
        </span>
      </div>

      {/* Nav links */}
      <div style={styles.navSection}>
        {NAV_ITEMS.map(({ path, label, icon: Icon, id }) => {
          const active = location.pathname === path;
          return (
            <Link
              key={path}
              to={path}
              id={id}
              style={{
                ...styles.navItem,
                ...(active ? styles.navItemActive : {}),
              }}
            >
              <Icon
                size={16}
                strokeWidth={1.8}
                style={{ color: active ? 'var(--accent)' : 'inherit', flexShrink: 0 }}
              />
              {label}
            </Link>
          );
        })}
      </div>

      {/* Bottom spacer */}
      <div style={styles.navBottom}>
      </div>
    </nav>
  );
};

const styles = {
  nav: {
    position: 'fixed',
    left: 0,
    top: 0,
    height: '100%',
    width: '240px',
    background: '#ffffff',
    display: 'flex',
    flexDirection: 'column',
    padding: '28px 0',
    borderRight: '1px solid var(--border)',
    zIndex: 100,
    transition: 'var(--transition)',
  },
  logoWrap: {
    padding: '0 24px 28px',
    borderBottom: '1px solid var(--border)',
  },
  logoText: {
    fontSize: '22px',
    fontWeight: 700,
    color: 'var(--text-primary)',
    letterSpacing: '-0.5px',
  },
  logoDot: {
    color: 'var(--gold)',
  },
  navSection: {
    flex: 1,
    padding: '24px 0 0',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 24px',
    fontSize: '14px',
    fontWeight: 500,
    color: 'var(--text-secondary)',
    textDecoration: 'none',
    transition: 'var(--transition)',
    borderLeft: '3px solid transparent',
  },
  navItemActive: {
    color: 'var(--accent)',
    background: 'var(--accent-subtle)',
    borderLeft: '3px solid var(--accent)',
  },
  navBottom: {
    padding: '16px 12px 0',
    borderTop: '1px solid var(--border)',
    marginTop: 'auto',
  },
  signOutBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    borderRadius: '8px',
    fontSize: '14px',
    color: 'var(--text-muted)',
    cursor: 'pointer',
    background: 'none',
    border: 'none',
    width: '100%',
    textAlign: 'left',
    transition: 'var(--transition)',
  },
};

export default Navbar;
