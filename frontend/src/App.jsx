import React, { useState, useEffect } from 'react';
import { Calendar, Users, Plus, Clock } from 'lucide-react';
import AuthBar from "./AuthBar";
import LoginPage from "./LoginPage";

export default function App() {
  const [meetings, setMeetings] = useState([]);
  const [formData, setFormData] = useState({
    title: '',
    starts_at: '',
    ends_at: '',
    attendee_count: 1,
  });

  if (window.location.pathname.startsWith("/login")) {
    return <LoginPage />;
  }

  const fetchMeetings = async () => {
    try {
      const res = await fetch('/api/meetings');
      if (res.ok) {
        const data = await res.json();
        setMeetings(data);
      }
    } catch (err) {
      console.error('Failed to fetch meetings:', err);
    }
  };

  useEffect(() => {
    fetchMeetings();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        starts_at: new Date(formData.starts_at).toISOString(),
        ends_at: new Date(formData.ends_at).toISOString(),
        attendee_count: parseInt(formData.attendee_count, 10),
      };

      const res = await fetch('/api/meetings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setFormData({ title: '', starts_at: '', ends_at: '', attendee_count: 1 });
        fetchMeetings();
      }
    } catch (err) {
      console.error('Failed to create meeting:', err);
    }
  };

  return (
    <div className="min-h-screen p-8 max-w-5xl mx-auto space-y-8">
      <AuthBar />
      <header className="border-b pb-4">
        <h1 className="text-3xl font-bold tracking-tight text-slate-800">Spry Meetings</h1>
        <p className="text-slate-500 text-sm mt-1">Manage and schedule team sessions</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Creation Form */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 h-fit">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Plus className="w-5 h-5 text-indigo-600" />
            New Meeting
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Title</label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Architecture Review"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Starts At</label>
              <input
                type="datetime-local"
                required
                value={formData.starts_at}
                onChange={(e) => setFormData({ ...formData, starts_at: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Ends At</label>
              <input
                type="datetime-local"
                required
                value={formData.ends_at}
                onChange={(e) => setFormData({ ...formData, ends_at: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Attendees</label>
              <input
                type="number"
                min="1"
                required
                value={formData.attendee_count}
                onChange={(e) => setFormData({ ...formData, attendee_count: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <button
              type="submit"
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 rounded-lg text-sm transition-colors"
            >
              Create Meeting
            </button>
          </form>
        </div>

        {/* Meetings List */}
        <div className="md:col-span-2 space-y-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Calendar className="w-5 h-5 text-indigo-600" />
            Scheduled Sessions ({meetings.length})
          </h2>
          {meetings.length === 0 ? (
            <div className="bg-white p-8 text-center rounded-xl border border-slate-200 text-slate-400 text-sm">
              No meetings scheduled yet. Create one on the left.
            </div>
          ) : (
            <div className="space-y-3">
              {meetings.map((m) => (
                <div key={m.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-2">
                  <div className="flex justify-between items-start">
                    <h3 className="font-semibold text-slate-800 text-base">{m.title}</h3>
                    <span className="inline-flex items-center gap-1 bg-slate-100 text-slate-600 text-xs px-2.5 py-1 rounded-full font-medium">
                      <Users className="w-3.5 h-3.5" />
                      {m.attendee_count}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {new Date(m.starts_at).toLocaleString()} - {new Date(m.ends_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
