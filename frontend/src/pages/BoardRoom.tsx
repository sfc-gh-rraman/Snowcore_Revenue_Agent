import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import {
  Swords, Brain, Eye, Flame, ChevronDown, ChevronUp, Database,
  AlertTriangle, CheckCircle, TrendingDown, TrendingUp, Minus,
  Search, Zap, FileText, MessageSquare, Target, Quote, Shield, Crosshair
} from 'lucide-react';

interface Decomposition {
  original_question: string;
  sub_questions: string[];
  time_horizon: string;
  key_metrics: string[];
}

interface Position {
  agent: string;
  round: number;
  text: string;
}

interface Challenge {
  agent: string;
  round: number;
  text: string;
}

interface Response {
  agent: string;
  round: number;
  action: string;
  text: string;
}

interface DataRequest {
  agent: string;
  request: string;
  sql: string;
  result: string;
}

interface DisagreementEntry {
  topic: string;
  fox: string;
  hedgehog: string;
  devil: string;
  magnitude: string;
  trend: string;
}

interface DisagreementRound {
  round: number;
  estimates?: Record<string, { range: number[]; confidence: number }>;
  disagreements: DisagreementEntry[];
  convergence_score: number;
}

interface FinalPosition {
  agent: string;
  initial_estimate?: { range: number[]; confidence: number };
  final_estimate?: { range: number[]; confidence: number };
  what_changed?: string;
  remaining_uncertainty?: string;
  key_insight?: string;
}

type Phase = 'idle' | 'decomposing' | 'researching' | 'analyzing' | 'debating' | 'debating_round3' | 'synthesizing' | 'complete';

const AGENTS: Record<string, {
  name: string; style: string; description: string;
  color: string; textColor: string; bg: string; border: string;
  gradient: string; glowClass: string; icon: React.ElementType;
}> = {
  fox: {
    name: 'The Fox', style: 'Triangulator',
    description: 'Triangulates multiple weak signals across macro, micro, and sentiment data',
    color: '#3b82f6', textColor: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30',
    gradient: 'from-blue-600 to-cyan-500', glowClass: 'animate-glow-pulse-blue', icon: Eye,
  },
  hedgehog: {
    name: 'The Hedgehog', style: 'Deep Thesis',
    description: 'Follows the deep thesis — one big idea driven by fundamentals and simulation',
    color: '#f59e0b', textColor: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30',
    gradient: 'from-amber-500 to-orange-500', glowClass: 'animate-glow-pulse-amber', icon: Brain,
  },
  devil: {
    name: "Devil's Advocate", style: 'Stress Tester',
    description: 'Stress-tests every assumption with tail risks, black swans, and inversion',
    color: '#8b5cf6', textColor: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/30',
    gradient: 'from-purple-600 to-pink-500', glowClass: 'animate-glow-pulse-purple', icon: Flame,
  },
};

const PHASE_LABELS: Record<Phase, string> = {
  idle: 'Ready',
  decomposing: 'Decomposing Question',
  researching: 'Gathering Intelligence',
  analyzing: 'Independent Analysis',
  debating: 'Cross-Examination',
  debating_round3: 'Round 3 — Final Exchange',
  synthesizing: 'Synthesizing Board Brief',
  complete: 'Debate Complete',
};

const PHASE_ORDER: Phase[] = ['decomposing', 'researching', 'analyzing', 'debating', 'debating_round3', 'synthesizing', 'complete'];
const PHASE_ICONS: Record<Phase, React.ElementType> = {
  idle: Target,
  decomposing: Crosshair,
  researching: Search,
  analyzing: Brain,
  debating: Swords,
  debating_round3: Swords,
  synthesizing: FileText,
  complete: CheckCircle,
};

function parseBrief(text: string) {
  const sections: Record<string, string> = {};
  const keys = ['CONSENSUS RANGE', 'AGREEMENT', 'DISAGREEMENT', 'WHAT WOULD CHANGE', 'THE ONE QUESTION', 'PROBABILITY-WEIGHTED SCENARIOS'];
  let current = 'title';
  const lines = text.split('\n');
  for (const line of lines) {
    const upper = line.trim().toUpperCase();
    const matched = keys.find(k => upper.startsWith(k));
    if (matched) { current = matched; sections[current] = ''; continue; }
    if (upper.startsWith('BOARD BRIEF:')) { sections['title'] = line.replace(/^BOARD BRIEF:\s*/i, '').trim(); continue; }
    sections[current] = (sections[current] || '') + line + '\n';
  }
  return sections;
}

function TypingText({ text, speed = 8 }: { text: string; speed?: number }) {
  const [displayed, setDisplayed] = useState('');
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!text) return;
    let i = 0;
    setDisplayed('');
    setDone(false);
    const iv = setInterval(() => {
      i += 3;
      if (i >= text.length) {
        setDisplayed(text);
        setDone(true);
        clearInterval(iv);
      } else {
        setDisplayed(text.slice(0, i));
      }
    }, speed);
    return () => clearInterval(iv);
  }, [text, speed]);

  return (
    <span className={done ? '' : 'typing-cursor'}>{displayed}</span>
  );
}

function ConvergenceGauge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const circumference = 283;
  const offset = circumference - (score * circumference);
  const color = score > 0.7 ? '#22c55e' : score > 0.4 ? '#f59e0b' : '#ef4444';
  const bgColor = score > 0.7 ? 'text-green-400' : score > 0.4 ? 'text-amber-400' : 'text-red-400';

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-32 h-16 overflow-hidden">
        <svg className="w-32 h-32 -mt-0" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="45" fill="none" stroke="rgb(51,65,85)" strokeWidth="8"
            strokeDasharray={circumference} strokeDashoffset={circumference / 2}
            transform="rotate(180 50 50)" strokeLinecap="round" />
          <circle cx="50" cy="50" r="45" fill="none" stroke={color} strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={offset + (circumference / 2)}
            transform="rotate(180 50 50)" strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1s ease-out, stroke 0.5s ease' }} />
        </svg>
      </div>
      <span className={`text-2xl font-bold ${bgColor} -mt-4`}>{pct}%</span>
      <span className="text-xs text-slate-500 mt-0.5">Convergence</span>
    </div>
  );
}

function RangeBar({ agentId, range, confidence, min, max }: {
  agentId: string; range: number[]; confidence: number; min: number; max: number;
}) {
  const a = AGENTS[agentId];
  const span = max - min || 1;
  const left = ((range[0] - min) / span) * 100;
  const width = ((range[1] - range[0]) / span) * 100;

  return (
    <div className="flex items-center gap-3">
      <div className="w-20 flex items-center gap-1.5">
        <a.icon className={`w-3.5 h-3.5 ${a.textColor}`} />
        <span className={`text-xs font-medium ${a.textColor}`}>{a.name.replace("The ", "")}</span>
      </div>
      <div className="flex-1 h-6 bg-slate-700/50 rounded-full relative overflow-hidden">
        <div
          className="absolute h-full rounded-full transition-all duration-1000 ease-out flex items-center justify-center"
          style={{
            left: `${left}%`, width: `${Math.max(width, 3)}%`,
            background: `linear-gradient(90deg, ${a.color}88, ${a.color}cc)`,
          }}
        >
          <span className="text-[10px] font-bold text-white drop-shadow whitespace-nowrap">
            ${range[0].toFixed(1)}B – ${range[1].toFixed(1)}B
          </span>
        </div>
      </div>
      <span className="text-xs text-slate-500 w-10 text-right">{confidence}%</span>
    </div>
  );
}

export default function BoardRoom() {
  const [question, setQuestion] = useState('');
  const [phase, setPhase] = useState<Phase>('idle');
  const [decomposition, setDecomposition] = useState<Decomposition | null>(null);
  const [positions, setPositions] = useState<Record<string, Position>>({});
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [responses, setResponses] = useState<Response[]>([]);
  const [dataRequests, setDataRequests] = useState<DataRequest[]>([]);
  const [disagreements, setDisagreements] = useState<DisagreementRound[]>([]);
  const [finalPositions, setFinalPositions] = useState<Record<string, FinalPosition>>({});
  const [briefText, setBriefText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [expandedPositions, setExpandedPositions] = useState<Record<string, boolean>>({ fox: true, hedgehog: true, devil: true });
  const [speakingAgent, setSpeakingAgent] = useState<string | null>(null);
  const [visibleSections, setVisibleSections] = useState<Set<string>>(new Set());
  const debateRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const showSection = useCallback((id: string) => {
    setVisibleSections(prev => new Set([...prev, id]));
  }, []);

  const scrollToBottom = useCallback(() => {
    if (debateRef.current) {
      debateRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, []);

  useEffect(() => { scrollToBottom(); }, [challenges, responses, briefText, scrollToBottom]);

  useEffect(() => {
    if (decomposition) showSection('decomposition');
  }, [decomposition, showSection]);

  useEffect(() => {
    if (Object.keys(positions).length > 0) showSection('positions');
  }, [positions, showSection]);

  useEffect(() => {
    if (challenges.length > 0) showSection('challenges');
  }, [challenges, showSection]);

  useEffect(() => {
    if (responses.length > 0) showSection('responses');
  }, [responses, showSection]);

  useEffect(() => {
    if (disagreements.length > 0) showSection('disagreements');
  }, [disagreements, showSection]);

  useEffect(() => {
    if (Object.keys(finalPositions).length > 0) showSection('finals');
  }, [finalPositions, showSection]);

  useEffect(() => {
    if (briefText) showSection('brief');
  }, [briefText, showSection]);

  const startDebate = async () => {
    if (!question.trim()) return;

    setPhase('decomposing');
    setDecomposition(null);
    setPositions({});
    setChallenges([]);
    setResponses([]);
    setDataRequests([]);
    setDisagreements([]);
    setFinalPositions({});
    setBriefText('');
    setError(null);
    setSpeakingAgent(null);
    setVisibleSections(new Set());

    abortRef.current = new AbortController();

    try {
      const resp = await fetch('/api/boardroom/debate/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim() }),
        signal: abortRef.current.signal,
      });

      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      if (!resp.body) throw new Error('No response body');

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const event = JSON.parse(line.slice(6));
            handleEvent(event);
          } catch {
          }
        }
      }
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        setError(e.message);
        setPhase('idle');
      }
    }
  };

  const handleEvent = (event: any) => {
    switch (event.type) {
      case 'phase':
        setPhase(event.phase as Phase);
        setSpeakingAgent(null);
        break;
      case 'decomposition':
        setDecomposition(event.data);
        break;
      case 'position':
        setSpeakingAgent(event.agent);
        setPositions(prev => ({ ...prev, [event.agent]: { agent: event.agent, round: event.round, text: event.text } }));
        break;
      case 'challenge':
        setSpeakingAgent(event.agent);
        setChallenges(prev => [...prev, { agent: event.agent, round: event.round, text: event.text }]);
        break;
      case 'response':
        setSpeakingAgent(event.agent);
        setResponses(prev => [...prev, { agent: event.agent, round: event.round, action: event.action, text: event.text }]);
        break;
      case 'data_request':
        setDataRequests(prev => [...prev, { agent: event.agent, request: event.request, sql: event.sql, result: event.result }]);
        break;
      case 'disagreement':
        setDisagreements(prev => [...prev, { round: event.round, ...event.data }]);
        break;
      case 'final':
        setFinalPositions(prev => ({ ...prev, [event.agent]: event.data }));
        break;
      case 'brief':
        setBriefText(event.text);
        setSpeakingAgent(null);
        break;
      case 'error':
        setError(event.message);
        break;
    }
  };

  const togglePosition = (agent: string) => {
    setExpandedPositions(prev => ({ ...prev, [agent]: !prev[agent] }));
  };

  const phaseIdx = PHASE_ORDER.indexOf(phase);

  const allEstimates = useMemo(() => {
    const fp = Object.entries(finalPositions);
    if (fp.length === 0) return null;
    let min = Infinity, max = -Infinity;
    fp.forEach(([, v]) => {
      const r = v.final_estimate?.range;
      if (r) { min = Math.min(min, r[0]); max = Math.max(max, r[1]); }
    });
    const pad = (max - min) * 0.15 || 0.5;
    return { min: min - pad, max: max + pad };
  }, [finalPositions]);

  return (
    <div className="space-y-6" ref={debateRef}>

      {phase === 'idle' && !briefText && (
        <div className="relative overflow-hidden rounded-2xl border border-slate-700/50">
          <div className="absolute inset-0">
            <div className="absolute -top-32 -right-32 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl animate-orbit-pulse" />
            <div className="absolute -bottom-32 -left-32 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl animate-orbit-pulse" style={{ animationDelay: '1.5s' }} />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />
          </div>
          <div className="absolute inset-0 bg-gradient-to-b from-slate-900/80 via-slate-900/60 to-slate-900/90" />

          <div className="relative px-8 pt-12 pb-8">
            <div className="text-center mb-10 animate-fade-in-up">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 shadow-2xl shadow-purple-500/30 mb-5">
                <Swords size={32} className="text-white" />
              </div>
              <h1 className="text-3xl font-bold mb-2">
                <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent animate-gradient-shift" style={{ backgroundSize: '200% auto' }}>
                  The Board Room
                </span>
              </h1>
              <p className="text-slate-400 text-sm max-w-lg mx-auto">
                Three AI analysts engage in adversarial debate — Superforecasting methodology.
                Challenge assumptions, stress-test scenarios, converge on truth.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-8">
              {(['fox', 'hedgehog', 'devil'] as const).map((id, i) => {
                const a = AGENTS[id];
                const Icon = a.icon;
                return (
                  <div key={id} className={`animate-fade-in-up-delay-${i + 1} glass rounded-xl p-5 border ${a.border} hover:scale-[1.02] transition-transform`}>
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${a.gradient} flex items-center justify-center mb-3 shadow-lg`}>
                      <Icon size={24} className="text-white" />
                    </div>
                    <h3 className={`font-bold ${a.textColor} mb-0.5`}>{a.name}</h3>
                    <p className="text-xs text-slate-500 font-medium mb-2">{a.style}</p>
                    <p className="text-xs text-slate-400 leading-relaxed">{a.description}</p>
                  </div>
                );
              })}
            </div>

            <div className="max-w-2xl mx-auto animate-fade-in-up-delay-4">
              <label className="block text-sm font-medium text-slate-300 mb-2.5 text-center">
                What question should the board deliberate?
              </label>
              <div className="glass-strong rounded-xl p-1 border border-slate-600/50 focus-within:border-purple-500/50 transition-colors">
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="e.g., What will SnowCore's revenue be in the next 12 months given current market conditions?"
                  className="w-full h-28 bg-transparent rounded-lg p-4 text-white placeholder-slate-600 focus:outline-none resize-none text-sm"
                />
              </div>
              <div className="flex justify-center mt-5">
                <button
                  onClick={startDebate}
                  disabled={!question.trim()}
                  className="group flex items-center gap-3 px-8 py-3.5 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl text-white font-semibold text-base shadow-xl shadow-purple-500/25 hover:shadow-purple-500/40 hover:scale-105 disabled:opacity-40 disabled:hover:scale-100 disabled:shadow-none transition-all"
                >
                  <Zap size={18} />
                  Begin Debate
                  <Swords size={16} className="group-hover:rotate-12 transition-transform" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="glass rounded-xl p-4 flex items-center gap-3 border border-red-500/30 animate-scale-in">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <span className="text-red-300 text-sm">{error}</span>
        </div>
      )}

      {phase !== 'idle' && (
        <div className="glass-strong rounded-xl p-5 border border-slate-700/50 animate-fade-in-up">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Swords className="w-6 h-6 text-purple-400" />
              <div>
                <h1 className="text-lg font-bold text-white">Board Room</h1>
                <p className="text-xs text-slate-500">{PHASE_LABELS[phase]}</p>
              </div>
            </div>
            {phase !== 'complete' && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/30">
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" />
                <span className="text-xs font-medium text-purple-400">Live</span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {PHASE_ORDER.map((p, i) => {
              const Icon = PHASE_ICONS[p];
              const isActive = p === phase;
              const isDone = i < phaseIdx;
              const isFuture = i > phaseIdx;
              return (
                <div key={p} className="flex items-center flex-1">
                  <div className={`
                    flex items-center justify-center w-9 h-9 rounded-full transition-all duration-500
                    ${isDone ? 'bg-purple-500 shadow-lg shadow-purple-500/30' : ''}
                    ${isActive ? 'bg-purple-500/20 border-2 border-purple-400 shadow-lg shadow-purple-500/20' : ''}
                    ${isFuture ? 'bg-slate-700/50 border border-slate-600/50' : ''}
                  `}>
                    {isDone ? (
                      <CheckCircle className="w-4 h-4 text-white" />
                    ) : (
                      <Icon className={`w-4 h-4 ${isActive ? 'text-purple-400 animate-pulse' : 'text-slate-500'}`} />
                    )}
                  </div>
                  {i < PHASE_ORDER.length - 1 && (
                    <div className={`flex-1 h-0.5 mx-1 rounded-full transition-all duration-500 ${
                      isDone ? 'bg-purple-500' : 'bg-slate-700/50'
                    }`} />
                  )}
                </div>
              );
            })}
          </div>
          <div className="flex justify-between mt-2 px-1">
            {PHASE_ORDER.map((p, i) => (
              <span key={p} className={`text-[10px] ${i <= phaseIdx ? 'text-slate-400' : 'text-slate-600'}`}>
                {p === 'debating_round3' ? 'R3' : PHASE_LABELS[p].split(' ')[0]}
              </span>
            ))}
          </div>
        </div>
      )}

      {decomposition && (
        <div className={`transition-all duration-700 ${visibleSections.has('decomposition') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
          <div className="glass rounded-xl p-5 border border-slate-700/50">
            <div className="flex items-center gap-2 mb-3">
              <Crosshair className="w-4 h-4 text-purple-400" />
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Decomposition</h3>
            </div>
            <p className="text-xs text-slate-500 mb-3">
              Time horizon: <span className="text-slate-400">{decomposition.time_horizon}</span>
              {' | '}Metrics: <span className="text-slate-400">{decomposition.key_metrics?.join(', ')}</span>
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {decomposition.sub_questions?.map((q, i) => (
                <div key={i} className={`glass rounded-lg p-3.5 border border-slate-700/50 animate-fade-in-up-delay-${i + 1}`}>
                  <span className="text-xs text-purple-400 font-mono font-bold">Q{i + 1}</span>
                  <p className="text-sm text-slate-200 mt-1.5 leading-relaxed">{q}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {Object.keys(positions).length > 0 && (
        <div className={`transition-all duration-700 ${visibleSections.has('positions') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
          <div className="flex items-center gap-2 mb-3">
            <FileText className="w-4 h-4 text-slate-400" />
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Position Papers</h3>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {(['fox', 'hedgehog', 'devil'] as const).map(id => {
              const pos = positions[id];
              const a = AGENTS[id];
              const Icon = a.icon;
              const expanded = expandedPositions[id];
              const isSpeaking = speakingAgent === id && phase === 'analyzing';

              if (!pos) return (
                <div key={id} className={`glass rounded-xl border ${a.border} h-48 animate-pulse`}>
                  <div className={`h-1 bg-gradient-to-r ${a.gradient} rounded-t-xl`} />
                </div>
              );

              return (
                <div key={id} className={`glass rounded-xl border ${a.border} overflow-hidden transition-all duration-500 ${isSpeaking ? a.glowClass : ''}`}>
                  <div className={`h-1 bg-gradient-to-r ${a.gradient}`} />
                  <div className={`flex items-center justify-between p-4 cursor-pointer hover:bg-white/5 transition-colors`} onClick={() => togglePosition(id)}>
                    <div className="flex items-center gap-3">
                      <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${a.gradient} flex items-center justify-center shadow-lg`}>
                        <Icon className="w-4.5 h-4.5 text-white" />
                      </div>
                      <div>
                        <span className={`text-sm font-bold ${a.textColor}`}>{a.name}</span>
                        <p className="text-[10px] text-slate-500">{a.style}</p>
                      </div>
                    </div>
                    {expanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                  </div>
                  {expanded && (
                    <div className="px-4 pb-4 text-sm text-slate-300 max-h-96 overflow-y-auto leading-relaxed">
                      <TypingText text={pos.text} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {challenges.length > 0 && (
        <div className={`transition-all duration-700 ${visibleSections.has('challenges') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
          <div className="flex items-center gap-2 mb-3">
            <MessageSquare className="w-4 h-4 text-slate-400" />
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Cross-Examination</h3>
          </div>
          <div className="space-y-3">
            {challenges.map((c, i) => {
              const a = AGENTS[c.agent];
              const Icon = a.icon;
              const isSpeaking = speakingAgent === c.agent && i === challenges.length - 1;
              return (
                <div key={i} className={`glass rounded-xl p-4 border-l-4 transition-all duration-500 ${isSpeaking ? a.glowClass : ''}`}
                  style={{ borderLeftColor: a.color }}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-7 h-7 rounded-lg bg-gradient-to-br ${a.gradient} flex items-center justify-center`}>
                      <Icon className="w-3.5 h-3.5 text-white" />
                    </div>
                    <span className={`text-sm font-bold ${a.textColor}`}>{a.name}</span>
                    <span className="text-xs text-slate-600">Round {c.round} — Challenge</span>
                  </div>
                  <div className="text-sm text-slate-300 leading-relaxed pl-9">
                    <TypingText text={c.text} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {dataRequests.length > 0 && (
        <div className="space-y-2 animate-fade-in-up">
          {dataRequests.map((dr, i) => (
            <div key={i} className="glass rounded-lg p-3 border border-cyan-500/20 flex items-start gap-3">
              <Database className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
              <div className="min-w-0">
                <p className="text-xs text-cyan-400 font-medium">{AGENTS[dr.agent]?.name} requested data</p>
                <p className="text-xs text-slate-400 mt-1">{dr.request}</p>
                {dr.sql && <p className="text-xs font-mono text-slate-600 mt-1 truncate">{dr.sql}</p>}
              </div>
            </div>
          ))}
        </div>
      )}

      {responses.length > 0 && (
        <div className={`transition-all duration-700 ${visibleSections.has('responses') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-4 h-4 text-slate-400" />
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Responses</h3>
          </div>
          <div className="space-y-3">
            {responses.map((r, i) => {
              const a = AGENTS[r.agent];
              const Icon = a.icon;
              const isSpeaking = speakingAgent === r.agent && i === responses.length - 1;
              const actionColor = r.action === 'CONCEDE' ? 'bg-green-500/20 text-green-400 border-green-500/30' :
                r.action === 'REBUT' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                'bg-amber-500/20 text-amber-400 border-amber-500/30';
              return (
                <div key={i} className={`glass rounded-xl p-4 border-l-4 transition-all duration-500 ${isSpeaking ? a.glowClass : ''}`}
                  style={{ borderLeftColor: a.color }}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-7 h-7 rounded-lg bg-gradient-to-br ${a.gradient} flex items-center justify-center`}>
                      <Icon className="w-3.5 h-3.5 text-white" />
                    </div>
                    <span className={`text-sm font-bold ${a.textColor}`}>{a.name}</span>
                    <span className={`text-xs px-2.5 py-0.5 rounded-full border font-semibold ${actionColor}`}>{r.action}</span>
                  </div>
                  <div className="text-sm text-slate-300 leading-relaxed pl-9">
                    <TypingText text={r.text} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {disagreements.length > 0 && (
        <div className={`transition-all duration-700 ${visibleSections.has('disagreements') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
          <div className="glass rounded-xl p-5 border border-slate-700/50">
            <div className="flex items-center gap-2 mb-4">
              <Target className="w-4 h-4 text-slate-400" />
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Disagreement Tracker</h3>
            </div>
            <div className="space-y-6">
              {disagreements.map((dr, ri) => (
                <div key={ri}>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold text-slate-400">After Round {dr.round}</span>
                    <ConvergenceGauge score={dr.convergence_score || 0} />
                  </div>

                  {dr.estimates && Object.keys(dr.estimates).length > 0 && (() => {
                    let eMin = Infinity, eMax = -Infinity;
                    Object.values(dr.estimates!).forEach(e => { eMin = Math.min(eMin, e.range[0]); eMax = Math.max(eMax, e.range[1]); });
                    const pad = (eMax - eMin) * 0.15 || 0.5;
                    return (
                      <div className="mb-4 space-y-2 p-3 bg-slate-900/30 rounded-lg">
                        {Object.entries(dr.estimates!).map(([agentId, est]) => (
                          <RangeBar key={agentId} agentId={agentId} range={est.range} confidence={est.confidence} min={eMin - pad} max={eMax + pad} />
                        ))}
                      </div>
                    );
                  })()}

                  <div className="space-y-2">
                    {dr.disagreements?.map((d, di) => {
                      const magColor = d.magnitude === 'HIGH' ? 'bg-red-500/20 text-red-400' : d.magnitude === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400' : 'bg-green-500/20 text-green-400';
                      const TrendIcon = d.trend === 'NARROWING' ? TrendingDown : d.trend === 'WIDENING' ? TrendingUp : Minus;
                      const trendColor = d.trend === 'NARROWING' ? 'text-green-400' : d.trend === 'WIDENING' ? 'text-red-400' : 'text-slate-400';
                      return (
                        <div key={di} className="glass rounded-lg p-3">
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${magColor}`}>{d.magnitude}</span>
                            <span className="text-sm font-medium text-slate-200">{d.topic}</span>
                            <TrendIcon className={`w-3.5 h-3.5 ${trendColor} ml-auto`} />
                            <span className={`text-xs ${trendColor}`}>{d.trend}</span>
                          </div>
                          <div className="grid grid-cols-3 gap-2 text-xs">
                            <div><span className="text-blue-400 font-semibold">Fox:</span> <span className="text-slate-400">{d.fox}</span></div>
                            <div><span className="text-amber-400 font-semibold">Hedgehog:</span> <span className="text-slate-400">{d.hedgehog}</span></div>
                            <div><span className="text-purple-400 font-semibold">Devil:</span> <span className="text-slate-400">{d.devil}</span></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {Object.keys(finalPositions).length > 0 && (
        <div className={`transition-all duration-700 ${visibleSections.has('finals') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-4 h-4 text-slate-400" />
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Final Positions</h3>
          </div>

          {allEstimates && (
            <div className="glass rounded-xl p-4 border border-slate-700/50 mb-4">
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Estimate Range Comparison</h4>
              <div className="space-y-2">
                {(['fox', 'hedgehog', 'devil'] as const).map(id => {
                  const fp = finalPositions[id];
                  if (!fp?.final_estimate) return null;
                  return <RangeBar key={id} agentId={id} range={fp.final_estimate.range} confidence={fp.final_estimate.confidence} min={allEstimates.min} max={allEstimates.max} />;
                })}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {(['fox', 'hedgehog', 'devil'] as const).map(id => {
              const fp = finalPositions[id];
              if (!fp) return null;
              const a = AGENTS[id];
              const Icon = a.icon;
              const init = fp.initial_estimate;
              const fin = fp.final_estimate;
              return (
                <div key={id} className={`glass rounded-xl border ${a.border} overflow-hidden`}>
                  <div className={`h-1 bg-gradient-to-r ${a.gradient}`} />
                  <div className="p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${a.gradient} flex items-center justify-center shadow-lg`}>
                        <Icon className="w-4.5 h-4.5 text-white" />
                      </div>
                      <div>
                        <span className={`text-sm font-bold ${a.textColor}`}>{a.name}</span>
                        <p className="text-[10px] text-slate-500">{a.style}</p>
                      </div>
                    </div>
                    {init && fin && (
                      <div className="space-y-2 mb-3 p-3 bg-slate-900/30 rounded-lg">
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-500">Initial</span>
                          <span className="text-slate-400 line-through opacity-60">${init.range?.[0]}B - ${init.range?.[1]}B ({init.confidence}%)</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-500">Final</span>
                          <span className={`font-bold ${a.textColor}`}>${fin.range?.[0]}B - ${fin.range?.[1]}B ({fin.confidence}%)</span>
                        </div>
                      </div>
                    )}
                    {fp.what_changed && (
                      <p className="text-xs text-slate-400 mb-2">
                        <span className="text-slate-500 font-semibold">Changed:</span> {fp.what_changed}
                      </p>
                    )}
                    {fp.key_insight && (
                      <p className="text-xs text-slate-300">
                        <span className="text-slate-500 font-semibold">Insight:</span> {fp.key_insight}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {briefText && (() => {
        const b = parseBrief(briefText);
        return (
          <div className={`transition-all duration-700 ${visibleSections.has('brief') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
            <div className="relative overflow-hidden rounded-2xl border border-purple-500/30 shadow-2xl shadow-purple-500/10">
              <div className="absolute inset-0 bg-gradient-to-b from-purple-500/5 via-slate-900/95 to-slate-900" />
              <div className="absolute -top-20 -right-20 w-60 h-60 bg-purple-500/10 rounded-full blur-3xl" />

              <div className="relative">
                <div className="px-8 py-6 border-b border-purple-500/20">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-xl shadow-purple-500/30">
                      <CheckCircle className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white">Board Brief</h3>
                      <p className="text-xs text-slate-400">Synthesized from three-agent adversarial debate</p>
                    </div>
                  </div>
                  {b.title && (
                    <p className="text-sm text-slate-300 mt-3 pl-16">{b.title}</p>
                  )}
                </div>

                {b['CONSENSUS RANGE'] && (
                  <div className="px-8 py-6 border-b border-slate-700/30">
                    <h4 className="text-xs font-semibold text-purple-300 uppercase tracking-widest mb-3">Consensus Range</h4>
                    <div className="text-lg font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent leading-relaxed">
                      {b['CONSENSUS RANGE'].trim().split('\n')[0]}
                    </div>
                    {b['CONSENSUS RANGE'].trim().split('\n').length > 1 && (
                      <div className="text-sm text-slate-300 mt-2 whitespace-pre-wrap leading-relaxed">
                        {b['CONSENSUS RANGE'].trim().split('\n').slice(1).join('\n')}
                      </div>
                    )}
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-0 border-b border-slate-700/30">
                  {b['AGREEMENT'] && (
                    <div className="px-8 py-5 border-r border-slate-700/30">
                      <h4 className="text-xs font-semibold text-green-400 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                        <CheckCircle className="w-3.5 h-3.5" /> Where They Agree
                      </h4>
                      <div className="space-y-2">
                        {b['AGREEMENT'].trim().split('\n').filter(l => l.trim()).map((line, i) => (
                          <div key={i} className="flex items-start gap-2 text-sm text-slate-300">
                            <div className="w-1 h-1 rounded-full bg-green-400 mt-2 shrink-0" />
                            <span className="leading-relaxed">{line.replace(/^[-•*]\s*/, '')}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {b['DISAGREEMENT'] && (
                    <div className="px-8 py-5">
                      <h4 className="text-xs font-semibold text-amber-400 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5" /> Where They Disagree
                      </h4>
                      <div className="space-y-2">
                        {b['DISAGREEMENT'].trim().split('\n').filter(l => l.trim()).map((line, i) => (
                          <div key={i} className="flex items-start gap-2 text-sm text-slate-300">
                            <div className="w-1 h-1 rounded-full bg-amber-400 mt-2 shrink-0" />
                            <span className="leading-relaxed">{line.replace(/^[-•*]\s*/, '')}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {b['PROBABILITY-WEIGHTED SCENARIOS'] && (
                  <div className="px-8 py-5 border-b border-slate-700/30">
                    <h4 className="text-xs font-semibold text-blue-300 uppercase tracking-widest mb-3">Probability-Weighted Scenarios</h4>
                    <div className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{b['PROBABILITY-WEIGHTED SCENARIOS'].trim()}</div>
                  </div>
                )}

                {b['WHAT WOULD CHANGE'] && (
                  <div className="px-8 py-5 border-b border-slate-700/30">
                    <h4 className="text-xs font-semibold text-red-300 uppercase tracking-widest mb-3">What Would Change This Forecast</h4>
                    <div className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{b['WHAT WOULD CHANGE'].trim()}</div>
                  </div>
                )}

                {b['THE ONE QUESTION'] && (
                  <div className="px-8 py-6 bg-purple-500/5">
                    <h4 className="text-xs font-semibold text-purple-300 uppercase tracking-widest mb-3">The One Question</h4>
                    <div className="relative pl-6">
                      <Quote className="absolute left-0 top-0 w-4 h-4 text-purple-500/50" />
                      <p className="text-lg text-white font-medium italic leading-relaxed">
                        {b['THE ONE QUESTION'].trim()}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })()}

      {phase === 'complete' && (
        <div className="flex justify-center pt-4 animate-fade-in-up">
          <button
            onClick={() => { setPhase('idle'); setQuestion(''); setVisibleSections(new Set()); }}
            className="group flex items-center gap-3 px-8 py-3 bg-slate-700/50 hover:bg-slate-600/50 border border-slate-600/50 rounded-xl font-medium transition-all hover:scale-105"
          >
            <Swords className="w-4 h-4 text-purple-400" />
            New Debate
          </button>
        </div>
      )}
    </div>
  );
}
