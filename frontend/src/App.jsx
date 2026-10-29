import { useState, useEffect } from 'react';
import { Calendar, Users, Plus, Clock, FileText } from 'lucide-react';
import AuthBar from "./AuthBar";
import LoginPage from "./LoginPage";
import AgendaManager from "./components/AgendaManager";

export default function App() {
  const [meetings, setMeetings] = useState([]);
  const [agendas, setAgendas] = useState([]);
  const [selectedMeetingId, setSelectedMeetingId] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    starts_at: '',
    ends_at: '',
    attendee_count: 1,
  });

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

  const fetchAgendas = async () => {
    try {
      const res = await fetch('/api/agendas');
      if (res.ok) {
        const data = await res.json();
        setAgendas(data);
      }
    } catch (err) {
      console.error('Failed to fetch agendas:', err);
    }
  };

  useEffect(() => {
    fetchMeetings();
    fetchAgendas();
  }, []);

  if (window.location.pathname.startsWith("/login")) {
    return <LoginPage />;
  }

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
    <div className="min-h-screen p-8 max-w-6xl mx-auto space-y-8">
      <AuthBar />
      <header className="border-b pb-4">
        <h1 className="text-3xl font-bold tracking-tight text-slate-800">Spry Meetings & Agendas</h1>
        <p className="text-slate-500 text-sm mt-1">Manage team sessions and parse structured agendas with Claude on Bedrock</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* Left Column: Meeting Form and Paste Agenda */}
        <div className="space-y-8">
          {/* Creation Form */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
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
              <div className="grid grid-cols-2 gap-3">
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

          {/* Paste an Agenda Component */}
          <AgendaManager
            selectedMeetingId={selectedMeetingId}
            onAgendaSaved={() => fetchAgendas()}
          />
        </div>

        {/* Right Column: Scheduled Meetings and Agendas List */}
        <div className="space-y-8">
          {/* Meetings List */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold flex items-center justify-between text-slate-800">
              <span className="flex items-center gap-2">
                <Calendar className="w-5 h-5 text-indigo-600" />
                Scheduled Sessions ({meetings.length})
              </span>
            </h2>
            {meetings.length === 0 ? (
              <div className="bg-white p-8 text-center rounded-xl border border-slate-200 text-slate-400 text-sm">
                No meetings scheduled yet. Create one on the left.
              </div>
            ) : (
              <div className="space-y-3">
                {meetings.map((m) => (
                  <div
                    key={m.id}
                    onClick={() => setSelectedMeetingId(selectedMeetingId === m.id ? null : m.id)}
                    className={`bg-white p-4 rounded-xl border transition-all cursor-pointer shadow-sm ${
                      selectedMeetingId === m.id ? 'border-indigo-500 ring-2 ring-indigo-200' : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <h3 className="font-semibold text-slate-800 text-base">{m.title}</h3>
                      <span className="inline-flex items-center gap-1 bg-slate-100 text-slate-600 text-xs px-2.5 py-1 rounded-full font-medium">
                        <Users className="w-3.5 h-3.5" />
                        {m.attendee_count}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate-500 mt-2">
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

          {/* Agendas List */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2 text-slate-800">
              <FileText className="w-5 h-5 text-indigo-600" />
              Saved Agendas ({agendas.length})
            </h2>
            {agendas.length === 0 ? (
              <div className="bg-white p-8 text-center rounded-xl border border-slate-200 text-slate-400 text-sm">
                No agendas saved yet. Paste and parse one above!
              </div>
            ) : (
              <div className="space-y-4">
                {agendas.map((a) => (
                  <div key={a.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold text-slate-800 text-base">{a.title || 'Untitled Agenda'}</h3>
                        <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                          {a.duration_minutes && <span>{a.duration_minutes} mins</span>}
                          {a.language && <span className="uppercase text-[10px] bg-slate-100 px-1.5 py-0.5 rounded font-mono">{a.language}</span>}
                          {a.model && <span className="text-[10px] bg-indigo-50 text-indigo-700 px-1.5 py-0.5 rounded">{a.model}</span>}
                        </div>
                      </div>
                    </div>

                    {/* Topics */}
                    {a.items && a.items.length > 0 && (
                      <div className="space-y-1.5 pt-2 border-t border-slate-100">
                        <h4 className="text-xs font-semibold text-slate-600">Topics</h4>
                        <ul className="space-y-1">
                          {a.items.map((it, idx) => (
                            <li key={idx} className="text-xs text-slate-700 flex justify-between bg-slate-50 px-2 py-1 rounded">
                              <span>• {it.topic}</span>
                              <span className="text-slate-400 font-mono">
                                {it.owner && <span className="mr-2 text-indigo-600">{it.owner}</span>}
                                {it.minutes ? `${it.minutes}m` : ''}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Action Items */}
                    {a.action_items && a.action_items.length > 0 && (
                      <div className="space-y-1.5 pt-2 border-t border-slate-100">
                        <h4 className="text-xs font-semibold text-slate-600">Action Items</h4>
                        <ul className="space-y-1">
                          {a.action_items.map((act, idx) => (
                            <li key={idx} className="text-xs text-slate-700 flex justify-between bg-amber-50/50 px-2 py-1 rounded border border-amber-100">
                              <span>☐ {act.task}</span>
                              <span className="text-slate-400 font-mono text-[11px]">
                                {act.owner && <span className="mr-2 text-amber-700 font-medium">{act.owner}</span>}
                                {act.due && <span className="text-slate-500">due {act.due}</span>}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
