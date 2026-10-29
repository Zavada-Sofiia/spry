import { useState, useRef } from 'react';
import { useAuth } from 'react-oidc-context';
import { Sparkles, X, Check, AlertCircle, Loader2, Plus, Trash2 } from 'lucide-react';

export default function AgendaManager({ selectedMeetingId = null, onAgendaSaved = () => {} }) {
  const auth = useAuth();
  const [pasteText, setPasteText] = useState('');
  const [parsing, setParsing] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [statusMessage, setStatusMessage] = useState(null);
  const abortControllerRef = useRef(null);

  // Suggested badges state
  const [suggestedFields, setSuggestedFields] = useState({});

  // Original AI output preservation
  const [originalSuggestion, setOriginalSuggestion] = useState(null);
  const [modelUsed, setModelUsed] = useState(null);
  const [promptVersion, setPromptVersion] = useState(null);

  // Form State
  const [formData, setFormData] = useState({
    title: '',
    starts_at: '',
    duration_minutes: '',
    language: 'en',
    items: [],
    action_items: [],
  });

  const clearBadge = (fieldName) => {
    setSuggestedFields((prev) => {
      const next = { ...prev };
      delete next[fieldName];
      return next;
    });
  };

  const handleCancelParse = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setParsing(false);
    setStatusMessage(null);
    setErrorMessage('Parsing was cancelled.');
  };

  const handleParse = async () => {
    setErrorMessage(null);
    setStatusMessage(null);

    if (!pasteText.trim()) {
      setErrorMessage('Please paste some text first.');
      return;
    }

    if (pasteText.length > 10000) {
      setErrorMessage('Text exceeds maximum limit of 10,000 characters.');
      return;
    }

    const token = auth.user?.id_token || auth.user?.access_token;
    if (!token) {
      setErrorMessage('Unauthorized. Please sign in to parse agendas.');
      return;
    }

    const parserUrl = import.meta.env.VITE_PARSER_FUNCTION_URL;
    if (!parserUrl) {
      setErrorMessage('Parser Function URL is not configured. (VITE_PARSER_FUNCTION_URL)');
      return;
    }

    const today = new Date().toISOString().split('T')[0];
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';

    const controller = new AbortController();
    abortControllerRef.current = controller;
    setParsing(true);
    setStatusMessage('Parsing agenda with Claude on Amazon Bedrock... (2–8 s)');

    try {
      const response = await fetch(parserUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          text: pasteText,
          today,
          tz,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        let errData = {};
        try {
          errData = await response.json();
        } catch {
          // ignore json parse error
        }

        let errMsg = errData.error || errData.message;
        if (typeof errMsg === 'object' && errMsg !== null) {
          errMsg = errMsg.message || JSON.stringify(errMsg);
        }
        if (!errMsg && Array.isArray(errData.detail)) {
          errMsg = errData.detail.map((d) => `${d.loc ? d.loc.join('.') + ': ' : ''}${d.msg}`).join('; ');
        }
        errMsg = errMsg || `Error ${response.status}: Failed to parse agenda.`;

        if (response.status === 401) {
          throw new Error('Unauthorized. Please check your credentials or sign in again.');
        } else if (response.status === 413) {
          throw new Error('Text exceeds maximum limit of 10,000 characters.');
        } else if (response.status === 422) {
          throw new Error(errMsg || 'No agenda found in pasted text. You can still type the agenda manually below.');
        } else if (response.status === 429) {
          throw new Error('Service busy (throttling). Please wait a moment and try again.');
        } else {
          throw new Error(errMsg);
        }
      }

      const data = await response.json();
      const agenda = data.agenda || {};

      // Store original suggestion metadata
      setOriginalSuggestion(agenda);
      setModelUsed(data.model || null);
      setPromptVersion(data.prompt_version || null);

      // Pre-fill form
      const newItems = (agenda.items || []).map((it) => ({
        topic: it.topic || '',
        owner: it.owner || '',
        minutes: it.minutes !== null && it.minutes !== undefined ? it.minutes : '',
      }));

      const newActionItems = (agenda.action_items || []).map((act) => ({
        task: act.task || '',
        owner: act.owner || '',
        due: act.due || '',
      }));

      setFormData({
        title: agenda.title || '',
        starts_at: agenda.starts_at || '',
        duration_minutes: agenda.duration_minutes !== null && agenda.duration_minutes !== undefined ? agenda.duration_minutes : '',
        language: agenda.language || 'en',
        items: newItems,
        action_items: newActionItems,
      });

      // Mark suggested fields
      const suggestions = {};
      if (agenda.title) suggestions['title'] = true;
      if (agenda.starts_at) suggestions['starts_at'] = true;
      if (agenda.duration_minutes) suggestions['duration_minutes'] = true;
      if (agenda.language) suggestions['language'] = true;
      newItems.forEach((_, idx) => {
        suggestions[`item_${idx}_topic`] = true;
        if (newItems[idx].owner) suggestions[`item_${idx}_owner`] = true;
        if (newItems[idx].minutes) suggestions[`item_${idx}_minutes`] = true;
      });
      newActionItems.forEach((_, idx) => {
        suggestions[`action_${idx}_task`] = true;
        if (newActionItems[idx].owner) suggestions[`action_${idx}_owner`] = true;
        if (newActionItems[idx].due) suggestions[`action_${idx}_due`] = true;
      });
      setSuggestedFields(suggestions);

      setStatusMessage('Agenda successfully parsed! Review and edit the fields below.');
    } catch (err) {
      if (err.name === 'AbortError') {
        setErrorMessage('Parsing was cancelled.');
      } else {
        setErrorMessage(err.message || 'Network failure connecting to agenda parser.');
      }
    } finally {
      setParsing(false);
      abortControllerRef.current = null;
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setErrorMessage(null);
    setStatusMessage(null);

    const formattedItems = formData.items
      .filter((it) => it.topic.trim().length > 0)
      .map((it) => ({
        topic: it.topic.trim(),
        owner: it.owner.trim() || null,
        minutes: it.minutes !== '' ? parseInt(it.minutes, 10) : null,
      }));

    const formattedActionItems = formData.action_items
      .filter((act) => act.task.trim().length > 0)
      .map((act) => {
        let dueVal = act.due ? act.due.trim() : null;
        if (dueVal && /^\d{1,2}\.\d{1,2}\.\d{4}$/.test(dueVal)) {
          const [d, m, y] = dueVal.split('.');
          dueVal = `${y}-${m.padStart(2, '0')}-${d.padStart(2, '0')}`;
        }
        return {
          task: act.task.trim(),
          owner: act.owner.trim() || null,
          due: dueVal,
        };
      });

    let startsAtIso = null;
    if (formData.starts_at) {
      try {
        startsAtIso = new Date(formData.starts_at).toISOString();
      } catch {
        startsAtIso = formData.starts_at;
      }
    }

    const payload = {
      meeting_id: selectedMeetingId || null,
      title: formData.title.trim() || null,
      starts_at: startsAtIso,
      duration_minutes: formData.duration_minutes !== '' ? parseInt(formData.duration_minutes, 10) : null,
      language: formData.language || 'en',
      items: formattedItems,
      action_items: formattedActionItems,
      ai_suggestion: originalSuggestion,
      model: modelUsed,
      prompt_version: promptVersion,
    };

    try {
      const res = await fetch('/api/agendas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        let msg = 'Failed to save agenda';
        if (typeof errData.detail === 'string') {
          msg = errData.detail;
        } else if (Array.isArray(errData.detail)) {
          msg = errData.detail.map((d) => `${d.loc ? d.loc.join('.') + ': ' : ''}${d.msg}`).join('; ');
        } else if (errData.detail && typeof errData.detail === 'object') {
          msg = JSON.stringify(errData.detail);
        } else if (errData.error) {
          msg = typeof errData.error === 'object' ? (errData.error.message || JSON.stringify(errData.error)) : errData.error;
        }
        throw new Error(msg);
      }

      const saved = await res.json();
      setStatusMessage('Agenda saved successfully!');
      setSuggestedFields({});
      setOriginalSuggestion(null);
      setPasteText('');
      setFormData({
        title: '',
        starts_at: '',
        duration_minutes: '',
        language: 'en',
        items: [],
        action_items: [],
      });
      onAgendaSaved(saved);
    } catch (err) {
      setErrorMessage(err.message || 'Error saving agenda to server.');
    }
  };

  const addItem = () => {
    setFormData((prev) => ({
      ...prev,
      items: [...prev.items, { topic: '', owner: '', minutes: '' }],
    }));
  };

  const removeItem = (index) => {
    setFormData((prev) => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index),
    }));
  };

  const addActionItem = () => {
    setFormData((prev) => ({
      ...prev,
      action_items: [...prev.action_items, { task: '', owner: '', due: '' }],
    }));
  };

  const removeActionItem = (index) => {
    setFormData((prev) => ({
      ...prev,
      action_items: prev.action_items.filter((_, i) => i !== index),
    }));
  };

  const SuggestedBadge = () => (
    <span className="ml-1.5 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800 border border-amber-200">
      suggested
    </span>
  );

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 space-y-6">
      <div className="flex items-center justify-between border-b pb-3">
        <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-600" />
          Paste an Agenda
        </h2>
        <span className="text-xs text-slate-500">The model suggests, you decide</span>
      </div>

      {/* Paste Area */}
      <div className="space-y-3">
        <label className="block text-xs font-medium text-slate-700">
          Paste free text (emails, Slack messages, meeting notes)
        </label>
        <textarea
          rows={4}
          value={pasteText}
          onChange={(e) => setPasteText(e.target.value)}
          disabled={parsing}
          placeholder="e.g. Monday 10:00, pricing sync, 45m. 1) Pro tier update - Olena (15m) 2) Customer feedback - Taras. Taras to collect competitor matrix by Friday."
          className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-xs"
        />

        <div className="flex items-center gap-3">
          {!parsing ? (
            <button
              type="button"
              onClick={handleParse}
              className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              <Sparkles className="w-4 h-4" />
              Parse with AI
            </button>
          ) : (
            <button
              type="button"
              onClick={handleCancelParse}
              className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              <X className="w-4 h-4" />
              Cancel
            </button>
          )}

          {parsing && (
            <span className="text-xs text-slate-500 flex items-center gap-1.5">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-600" />
              {statusMessage || 'Processing...'}
            </span>
          )}
        </div>
      </div>

      {/* Messages */}
      {errorMessage && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {statusMessage && !parsing && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-xs text-green-700 flex items-start gap-2">
          <Check className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Pre-filled / Editable Agenda Form */}
      <form onSubmit={handleSave} className="space-y-4 pt-4 border-t border-slate-100">
        <h3 className="text-sm font-semibold text-slate-800">Agenda Details & Review</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Title
              {suggestedFields['title'] && <SuggestedBadge />}
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => {
                clearBadge('title');
                setFormData({ ...formData, title: e.target.value });
              }}
              placeholder="e.g. Pricing Sync"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Duration (minutes)
              {suggestedFields['duration_minutes'] && <SuggestedBadge />}
            </label>
            <input
              type="number"
              min="1"
              max="600"
              value={formData.duration_minutes}
              onChange={(e) => {
                clearBadge('duration_minutes');
                setFormData({ ...formData, duration_minutes: e.target.value });
              }}
              placeholder="45"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Starts At (ISO / Date string)
              {suggestedFields['starts_at'] && <SuggestedBadge />}
            </label>
            <input
              type="text"
              value={formData.starts_at}
              onChange={(e) => {
                clearBadge('starts_at');
                setFormData({ ...formData, starts_at: e.target.value });
              }}
              placeholder="2026-10-19T10:00:00+03:00"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Language
              {suggestedFields['language'] && <SuggestedBadge />}
            </label>
            <input
              type="text"
              value={formData.language}
              onChange={(e) => {
                clearBadge('language');
                setFormData({ ...formData, language: e.target.value });
              }}
              placeholder="uk or en"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Agenda Topics */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Agenda Topics ({formData.items.length})
            </h4>
            <button
              type="button"
              onClick={addItem}
              className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 font-medium"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Topic
            </button>
          </div>

          {formData.items.map((item, idx) => (
            <div key={idx} className="flex items-center gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
              <div className="flex-1">
                <div className="flex items-center">
                  <span className="text-[10px] text-slate-500 font-medium mr-1">{idx + 1}. Topic</span>
                  {suggestedFields[`item_${idx}_topic`] && <SuggestedBadge />}
                </div>
                <input
                  type="text"
                  required
                  value={item.topic}
                  onChange={(e) => {
                    clearBadge(`item_${idx}_topic`);
                    const next = [...formData.items];
                    next[idx].topic = e.target.value;
                    setFormData({ ...formData, items: next });
                  }}
                  placeholder="Discussion topic"
                  className="w-full mt-1 px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="w-32">
                <div className="flex items-center">
                  <span className="text-[10px] text-slate-500 font-medium mr-1">Owner</span>
                  {suggestedFields[`item_${idx}_owner`] && <SuggestedBadge />}
                </div>
                <input
                  type="text"
                  value={item.owner}
                  onChange={(e) => {
                    clearBadge(`item_${idx}_owner`);
                    const next = [...formData.items];
                    next[idx].owner = e.target.value;
                    setFormData({ ...formData, items: next });
                  }}
                  placeholder="Name"
                  className="w-full mt-1 px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="w-20">
                <div className="flex items-center">
                  <span className="text-[10px] text-slate-500 font-medium mr-1">Mins</span>
                  {suggestedFields[`item_${idx}_minutes`] && <SuggestedBadge />}
                </div>
                <input
                  type="number"
                  min="1"
                  max="480"
                  value={item.minutes}
                  onChange={(e) => {
                    clearBadge(`item_${idx}_minutes`);
                    const next = [...formData.items];
                    next[idx].minutes = e.target.value;
                    setFormData({ ...formData, items: next });
                  }}
                  placeholder="15"
                  className="w-full mt-1 px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <button
                type="button"
                onClick={() => removeItem(idx)}
                className="p-1 text-slate-400 hover:text-red-500 mt-4 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>

        {/* Action Items */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Action Items ({formData.action_items.length})
            </h4>
            <button
              type="button"
              onClick={addActionItem}
              className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 font-medium"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Action Item
            </button>
          </div>

          {formData.action_items.map((act, idx) => (
            <div key={idx} className="flex items-center gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
              <div className="flex-1">
                <div className="flex items-center">
                  <span className="text-[10px] text-slate-500 font-medium mr-1">{idx + 1}. Task</span>
                  {suggestedFields[`action_${idx}_task`] && <SuggestedBadge />}
                </div>
                <input
                  type="text"
                  required
                  value={act.task}
                  onChange={(e) => {
                    clearBadge(`action_${idx}_task`);
                    const next = [...formData.action_items];
                    next[idx].task = e.target.value;
                    setFormData({ ...formData, action_items: next });
                  }}
                  placeholder="Task description"
                  className="w-full mt-1 px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="w-32">
                <div className="flex items-center">
                  <span className="text-[10px] text-slate-500 font-medium mr-1">Owner</span>
                  {suggestedFields[`action_${idx}_owner`] && <SuggestedBadge />}
                </div>
                <input
                  type="text"
                  value={act.owner}
                  onChange={(e) => {
                    clearBadge(`action_${idx}_owner`);
                    const next = [...formData.action_items];
                    next[idx].owner = e.target.value;
                    setFormData({ ...formData, action_items: next });
                  }}
                  placeholder="Name"
                  className="w-full mt-1 px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="w-32">
                <div className="flex items-center">
                  <span className="text-[10px] text-slate-500 font-medium mr-1">Due Date</span>
                  {suggestedFields[`action_${idx}_due`] && <SuggestedBadge />}
                </div>
                <input
                  type="date"
                  value={act.due}
                  onChange={(e) => {
                    clearBadge(`action_${idx}_due`);
                    const next = [...formData.action_items];
                    next[idx].due = e.target.value;
                    setFormData({ ...formData, action_items: next });
                  }}
                  className="w-full mt-1 px-2 py-1 bg-white border border-slate-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <button
                type="button"
                onClick={() => removeActionItem(idx)}
                className="p-1 text-slate-400 hover:text-red-500 mt-4 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>

        <div className="pt-3">
          <button
            type="submit"
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
          >
            <Check className="w-4 h-4" />
            Save Agenda
          </button>
        </div>
      </form>
    </div>
  );
}
