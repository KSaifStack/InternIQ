import React, { useState, useEffect } from 'react';
import { Save, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { getUser, updateUser, getStates } from '../api';

const US_STATES = {
  '': 'No Preference',
  CA: 'California', NY: 'New York', TX: 'Texas', WA: 'Washington',
  MA: 'Massachusetts', IL: 'Illinois', GA: 'Georgia', CO: 'Colorado',
  NC: 'North Carolina', FL: 'Florida', PA: 'Pennsylvania', OH: 'Ohio',
  VA: 'Virginia', OR: 'Oregon', MI: 'Michigan', AZ: 'Arizona',
  MN: 'Minnesota', MD: 'Maryland', CT: 'Connecticut', NJ: 'New Jersey',
};

const GRAD_YEARS = [2024, 2025, 2026, 2027, 2028, 2029];

const Profile = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);

  // Form state
  const [fullName, setFullName] = useState('');
  const [gradYear, setGradYear] = useState(2026);
  const [skills, setSkills] = useState('');
  const [location, setLocation] = useState('');

  useEffect(() => {
    fetchUser();
  }, []);

  const fetchUser = async () => {
    try {
      const data = await getUser(1); // Hardcoded user 1 for MVP
      setUser(data);
      setFullName(data.full_name || '');
      setGradYear(data.graduation_year || 2026);
      setSkills(data.skills || '');
      setLocation(data.location || '');
    } catch (error) {
      console.error("Failed to fetch user", error);
    }
    setLoading(false);
  };

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await updateUser(1, {
        full_name: fullName,
        graduation_year: parseInt(gradYear),
        skills: skills,
        location: location || null,
      });
      setUser(updated);
      showToast('Profile saved successfully!');
    } catch (error) {
      console.error("Failed to update user", error);
      showToast('Failed to save profile.', 'error');
    }
    setSaving(false);
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto flex justify-center py-24">
        <Loader2 className="w-10 h-10 animate-spin text-[var(--accent)]" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 p-4">
      <div className="bg-[var(--bg-secondary)] p-10 rounded-[var(--radius-card)] border border-[var(--border)] shadow-2xl">
        <h1 className="text-3xl font-extrabold text-[var(--text-primary)] mb-8 tracking-tight">Student Profile</h1>
        
        {/* Profile Form */}
        <div className="space-y-8">
          <div className="grid grid-cols-2 gap-8">
            <div>
              <label className="block text-xs font-bold text-[var(--text-secondary)] mb-2">Full Name</label>
              <input
                id="profile-name-input"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full bg-[var(--bg-elevated)] border border-[var(--border)] rounded-[var(--radius-button)] px-4 py-3 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)] transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-[var(--text-secondary)] mb-2">Graduation Year</label>
              <select
                id="profile-grad-year-select"
                value={gradYear}
                onChange={(e) => setGradYear(e.target.value)}
                className="w-full bg-[var(--bg-elevated)] border border-[var(--border)] rounded-[var(--radius-button)] px-4 py-3 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)] transition-all"
              >
                {GRAD_YEARS.map(y => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Preferred Location */}
          <div>
            <label className="block text-xs font-bold text-[var(--text-secondary)] mb-2">Preferred Location</label>
            <select
              id="profile-location-select"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full bg-[var(--bg-elevated)] border border-[var(--border)] rounded-[var(--radius-button)] px-4 py-3 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)] transition-all"
            >
              {Object.entries(US_STATES).map(([code, name]) => (
                <option key={code} value={code} className="bg-[var(--bg-secondary)]">{name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-[var(--text-secondary)] mb-2">Skills (Comma separated)</label>
            <textarea 
              id="profile-skills-textarea"
              rows="4" 
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
              className="w-full bg-[var(--bg-elevated)] border border-[var(--border)] rounded-[var(--radius-button)] px-4 py-3 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)] transition-all resize-none"
              placeholder="React, Python, Machine Learning..."
            ></textarea>
          </div>

          <div className="flex justify-end pt-8 border-t border-[var(--border)]">
            <button
              id="profile-save-btn"
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:bg-[var(--text-muted)] text-white font-black uppercase tracking-tighter py-3 px-8 rounded-[var(--radius-button)] transition-all flex items-center gap-3 transform hover:scale-105 active:scale-95 shadow-lg shadow-blue-500/20"
            >
              {saving ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Save className="w-5 h-5" />
              )}
              {saving ? 'UPDATING...' : 'SAVE CHANGES'}
            </button>
          </div>
        </div>
      </div>

      {/* Toast Notification */}
      {toast && (
        <div className={`fixed bottom-8 right-8 px-6 py-4 rounded-[var(--radius-card)] shadow-2xl text-white font-bold transition-all z-50 flex items-center gap-3 animate-in slide-in-from-bottom-4 duration-300 ${
          toast.type === 'success' ? 'bg-[var(--success)]' : 'bg-[var(--danger)]'
        }`}>
          {toast.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
          {toast.message}
        </div>
      )}
    </div>
  );
};

export default Profile;
