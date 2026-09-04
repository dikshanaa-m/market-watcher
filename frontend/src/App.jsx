import React, { useState, useEffect } from 'react';
import axios from 'axios'

axios.defaults.baseURL = import.meta.env.VITE_API_URL || ''
import { 
  Activity, 
  ShieldCheck, 
  AlertTriangle, 
  RefreshCw, 
  GitCommit, 
  CheckCircle2, 
  Server, 
  Radio,
  Play,
  RotateCcw,
  TrendingDown,
  TrendingUp,
  Newspaper,
  Layers,
  Database,
  ChevronRight,
  Flame,
  ArrowUpDown,
  X,
  Zap,
  BarChart3,
  Clock,
  CheckCheck,
  Eye,
  AlertOctagon,
  VolumeX,
  Sparkles,
  ShieldAlert,
  Sliders,
  ThumbsUp,
  Volume2,
  SlidersHorizontal,
  Bookmark
} from 'lucide-react';

export default function App() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [catchupDigest, setCatchupDigest] = useState(null);
  const [trustSummary, setTrustSummary] = useState(null);
  const [userWeights, setUserWeights] = useState(null);
  const [stocks, setStocks] = useState([]);
  const [surpriseScores, setSurpriseScores] = useState({});
  const [events, setEvents] = useState([]);
  const [news, setNews] = useState([]);
  const [aiExplanations, setAiExplanations] = useState({});
  const [aiLoading, setAiLoading] = useState(false);
  
  const [viewMode, setViewMode] = useState('CATCHUP'); // 'CATCHUP' (Hero) or 'WATCHLIST'
  const [selectedTicker, setSelectedTicker] = useState('ALL');
  const [activeAuditStock, setActiveAuditStock] = useState(null);
  const [showWeightsDrawer, setShowWeightsDrawer] = useState(false);
  const [sortBy, setSortBy] = useState('ABNORMAL');
  
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  const fetchAiExplanation = async (ticker) => {
    if (!ticker || ticker === 'ALL' || aiExplanations[ticker]) return;
    setAiLoading(true);
    try {
      const res = await axios.get(`/api/ai/explain/${ticker}`);
      if (res.data && res.data.status === 'success') {
        setAiExplanations(prev => ({ ...prev, [ticker]: res.data }));
      }
    } catch (err) {
      console.error("AI explanation fetch error:", err);
    } finally {
      setAiLoading(false);
    }
  };

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // 1. Fetch Health
      const healthRes = await axios.get('/api/health');
      setHealthStatus(healthRes.data);

      // 2. Fetch User Preference Weights
      const weightsRes = await axios.get('/api/personalization/weights');
      setUserWeights(weightsRes.data);

      // 3. Fetch Data Trust Summary
      const trustRes = await axios.get('/api/data-trust/status');
      setTrustSummary(trustRes.data);

      // 4. Fetch Catch-Up Digest
      const catchupRes = await axios.get('/api/catchup/digest');
      setCatchupDigest(catchupRes.data);

      // 5. Fetch Surprise Scores
      const scoresRes = await axios.get('/api/surprise-scores');
      const scoreMap = {};
      (scoresRes.data.data || []).forEach(s => {
        scoreMap[s.ticker] = s;
      });
      setSurpriseScores(scoreMap);

      // 6. Fetch Watchlist Stocks
      const stocksRes = await axios.get('/api/watchlists/1/stocks');
      const fetchedStocks = stocksRes.data.stocks || [];
      setStocks(fetchedStocks);

      // 7. Fetch Market Events
      const tickerParam = selectedTicker === 'ALL' ? '' : `?ticker=${selectedTicker}`;
      const eventsRes = await axios.get(`/api/market-events${tickerParam}`);
      setEvents(eventsRes.data.data || []);

      // 8. Fetch News Events
      const newsRes = await axios.get(`/api/news`);
      setNews(newsRes.data.data || []);

      // 9. Fetch Batch AI Explanations for Digest Cards
      if (catchupRes.data.story_cards) {
        const digestTickers = catchupRes.data.story_cards.map(c => c.ticker);
        try {
          const aiRes = await axios.post('/api/ai/explain-digest', { tickers: digestTickers });
          if (aiRes.data && aiRes.data.explanations) {
            setAiExplanations(prev => ({ ...prev, ...aiRes.data.explanations }));
          }
        } catch (err) {
          console.error("Batch AI explanations error:", err);
        }
      }

    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [selectedTicker]);

  useEffect(() => {
    if (activeAuditStock?.ticker) {
      fetchAiExplanation(activeAuditStock.ticker);
    }
  }, [activeAuditStock]);


  const handleResetDemo = async () => {
    setActionLoading(true);
    try {
      await axios.get('/api/demo/reset');
      await axios.post('/api/demo/run');
      setNotification({ type: 'success', message: 'Demo database reset & scenario events replayed.' });
      await fetchDashboardData();
    } catch (err) {
      setNotification({ type: 'error', message: 'Failed to reset demo database' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleMarkSeen = async () => {
    setActionLoading(true);
    try {
      await axios.post('/api/catchup/mark-seen');
      setNotification({ type: 'success', message: 'Marked all as seen. Updated last-seen timestamp.' });
      await fetchDashboardData();
    } catch (err) {
      setNotification({ type: 'error', message: 'Failed to mark watchlist as seen' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleUserFeedback = async (ticker, interactionType) => {
    setActionLoading(true);
    try {
      const res = await axios.post('/api/interactions', {
        ticker: ticker,
        interaction_type: interactionType
      });
      setNotification({ type: 'success', message: res.data.message });
      await fetchDashboardData();
    } catch (err) {
      setNotification({ type: 'error', message: 'Failed to record feedback signal' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleResetWeights = async () => {
    setActionLoading(true);
    try {
      const res = await axios.post('/api/personalization/reset-weights');
      setNotification({ type: 'success', message: res.data.message });
      await fetchDashboardData();
    } catch (err) {
      setNotification({ type: 'error', message: 'Failed to reset preference weights' });
    } finally {
      setActionLoading(false);
    }
  };

  // Helper for sorting watchlist stocks
  const sortedStocks = [...stocks].sort((a, b) => {
    const scoreA = surpriseScores[a.ticker]?.surprise_score || 0;
    const scoreB = surpriseScores[b.ticker]?.surprise_score || 0;
    const changeA = Math.abs(a.latest_event?.price_change_percent || 0);
    const changeB = Math.abs(b.latest_event?.price_change_percent || 0);

    if (sortBy === 'ABNORMAL') {
      return scoreB - scoreA;
    } else if (sortBy === 'CHANGE') {
      return changeB - changeA;
    } else if (sortBy === 'TICKER') {
      return a.ticker.localeCompare(b.ticker);
    }
    return 0;
  });

  const getScoreBadgeClass = (category) => {
    switch (category) {
      case 'VERY UNUSUAL':
        return 'bg-rose-950/80 text-rose-300 border-rose-800/80 glow-rose';
      case 'UNUSUAL':
        return 'bg-amber-950/80 text-amber-300 border-amber-800/80 glow-amber';
      case 'MODERATE':
        return 'bg-cyan-950/80 text-cyan-300 border-cyan-800/80';
      default:
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80';
    }
  };

  const trustMap = {};
  (trustSummary?.stock_trust || []).forEach(t => {
    trustMap[t.ticker] = t;
  });

  const w = userWeights?.weights || { volatility_weight: 0.40, volume_weight: 0.30, news_weight: 0.20, extreme_weight: 0.10 };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-gray-100 flex flex-col font-sans">
      {/* Header Bar */}
      <header className="border-b border-gray-800 bg-[#111827]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 p-0.5 shadow-lg shadow-emerald-500/20">
              <div className="w-full h-full bg-gray-950 rounded-[10px] flex items-center justify-center">
                <GitCommit className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
            <div>
              <h1 className="font-bold text-xl tracking-tight text-white flex items-center space-x-2">
                <span>MarketPulse</span>
                <span className="px-2 py-0.5 text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full font-mono">
                  Watchlist Intelligence
                </span>
              </h1>
              <p className="text-xs text-gray-400 font-medium mt-0.5">Smart Stock Watchlist &amp; Anomaly Engine</p>
            </div>


          </div>

          {/* Navigation & Controls */}
          <div className="flex items-center space-x-4">
            <div className="inline-flex rounded-xl bg-gray-950 p-1 border border-gray-800">
              <button
                onClick={() => setViewMode('CATCHUP')}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  viewMode === 'CATCHUP'
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-black shadow-md'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Catch-Up Mode (Hero)</span>
              </button>

              <button
                onClick={() => setViewMode('WATCHLIST')}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  viewMode === 'WATCHLIST'
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-black shadow-md'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Watchlist Grid</span>
              </button>
            </div>

            {/* Weights Drawer Toggle */}
            <button
              onClick={() => setShowWeightsDrawer(!showWeightsDrawer)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-gray-900 hover:bg-gray-800 text-emerald-400 text-xs font-mono border border-gray-800"
              title="View and adjust your feedback weights"
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Personalized Weights</span>
            </button>

            <button
              onClick={handleResetDemo}
              disabled={actionLoading || loading}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-medium border border-gray-700 transition disabled:opacity-50"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${actionLoading ? 'animate-spin' : ''}`} />
              <span>Reset Demo</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        
        {/* Notification Toast */}
        {notification && (
          <div className={`p-4 rounded-xl border flex items-center justify-between text-xs font-medium transition-all ${
            notification.type === 'success' 
              ? 'bg-emerald-950/60 border-emerald-800 text-emerald-300' 
              : 'bg-rose-950/60 border-rose-800 text-rose-300'
          }`}>
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>{notification.message}</span>
            </div>
            <button onClick={() => setNotification(null)} className="text-gray-400 hover:text-white">Dismiss</button>
          </div>
        )}

        {/* Personalized Preference Weights Drawer (Surfaced when toggled) */}
        {showWeightsDrawer && (
          <div className="p-6 rounded-2xl bg-gray-900/90 border border-emerald-500/30 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-gray-800 pb-3">
              <div className="flex items-center space-x-2">
                <Sliders className="w-5 h-5 text-emerald-400" />
                <h3 className="font-bold text-base text-white">Your Personalized Materiality Profile</h3>
              </div>
              
              <button 
                onClick={handleResetWeights}
                disabled={actionLoading}
                className="text-xs text-gray-400 hover:text-emerald-400 font-mono underline"
              >
                Reset to default weights (40/30/20/10)
              </button>
            </div>

            <p className="text-xs text-gray-300">
              {userWeights?.explanation || "Meaningful is personal. Your factor weights dynamically adapt as you interact with alerts and news."}
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
              <div className="p-3 bg-gray-950 rounded-xl border border-gray-800 space-y-1">
                <div className="text-[11px] text-gray-400">Price Volatility Weight</div>
                <div className="text-lg font-bold font-mono text-emerald-400">{(w.volatility_weight * 100).toFixed(1)}%</div>
              </div>
              <div className="p-3 bg-gray-950 rounded-xl border border-gray-800 space-y-1">
                <div className="text-[11px] text-gray-400">Volume Spike Weight</div>
                <div className="text-lg font-bold font-mono text-teal-400">{(w.volume_weight * 100).toFixed(1)}%</div>
              </div>
              <div className="p-3 bg-gray-950 rounded-xl border border-gray-800 space-y-1">
                <div className="text-[11px] text-gray-400">News Impact Weight</div>
                <div className="text-lg font-bold font-mono text-amber-400">{(w.news_weight * 100).toFixed(1)}%</div>
              </div>
              <div className="p-3 bg-gray-950 rounded-xl border border-gray-800 space-y-1">
                <div className="text-[11px] text-gray-400">Historical Extreme Weight</div>
                <div className="text-lg font-bold font-mono text-cyan-400">{(w.extreme_weight * 100).toFixed(1)}%</div>
              </div>
            </div>
          </div>
        )}

        {/* Data Trust Conflict Banner */}
        {trustSummary?.active_conflicts?.length > 0 && (
          <div className="p-5 rounded-2xl bg-amber-950/40 border border-amber-700/60 glow-amber space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <ShieldAlert className="w-6 h-6 text-amber-400 flex-shrink-0" />
                <div>
                  <h4 className="font-bold text-sm text-amber-200 flex items-center space-x-2">
                    <span>⚠ Data Provenance &amp; Conflict Warning</span>
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      {trustSummary.active_conflicts.length} Active Conflict Detected
                    </span>
                  </h4>
                  <p className="text-xs text-amber-300/80 mt-0.5">
                    MarketPulse transparently surfaces data source mismatches instead of selecting one silently.
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
              {trustSummary.active_conflicts.map(conf => (
                <div key={conf.ticker} className="p-3.5 rounded-xl bg-gray-950/80 border border-amber-800/40 text-xs space-y-2 font-mono">
                  <div className="flex items-center justify-between font-bold text-white">
                    <span>{conf.ticker} Data Disagreement</span>
                    <span className="text-amber-400">Differ by {conf.conflict_percent}%</span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 border-t border-gray-800">
                    <div className="bg-gray-900 p-2 rounded border border-gray-800">
                      <div className="text-gray-400">{conf.source}</div>
                      <div className="text-emerald-400 font-bold text-sm">${conf.primary_price?.toFixed(2)}</div>
                    </div>
                    <div className="bg-gray-900 p-2 rounded border border-gray-800">
                      <div className="text-gray-400">{conf.secondary_source}</div>
                      <div className="text-amber-400 font-bold text-sm">${conf.secondary_price?.toFixed(2)}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* HERO VIEW: CATCH-UP MODE */}
        {viewMode === 'CATCHUP' && catchupDigest && (
          <div className="space-y-8">
            {/* Catch-Up Hero Header Banner */}
            <div className="p-8 rounded-3xl glass-panel relative overflow-hidden border border-emerald-500/20 shadow-2xl">
              <div className="absolute -top-32 -right-32 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>

              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
                <div className="space-y-3">
                  <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-950/80 border border-emerald-800/60 text-emerald-400 text-xs font-mono">
                    <Clock className="w-3.5 h-3.5" />
                    <span>While You Were Away • {catchupDigest.time_away_hours}h elapsed</span>
                  </div>

                  <h2 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
                    Good evening 👋 <br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
                      Here&apos;s what changed since you were last here.
                    </span>
                  </h2>

                  <p className="text-gray-300 text-sm leading-relaxed max-w-2xl">
                    MarketPulse analyzed your watchlist events and prioritized the most meaningful changes and abnormal silence.
                  </p>
                </div>


                <div className="flex flex-col items-start md:items-end space-y-3">
                  <button
                    onClick={handleMarkSeen}
                    disabled={actionLoading}
                    className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 text-black font-bold text-xs shadow-lg shadow-emerald-500/20 hover:opacity-90 transition disabled:opacity-50"
                  >
                    <CheckCheck className="w-4 h-4" />
                    <span>Mark All as Seen</span>
                  </button>
                  <span className="text-[11px] text-gray-500 font-mono">Resets digest baseline to current time</span>
                </div>
              </div>
            </div>

            {/* Catch-Up Story Cards Stream */}
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-xl text-white flex items-center space-x-2">
                  <span>Prioritized Events Digest</span>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-gray-800 text-gray-300 border border-gray-700">
                    {catchupDigest.digest_cards_count} story cards
                  </span>
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {catchupDigest.story_cards?.map((card) => {
                  const isAbnormalMove = card.card_type === 'ABNORMAL_MOVEMENT';
                  const isAbnormalSilence = card.card_type === 'ABNORMAL_SILENCE';
                  const isPos = card.price_change_percent >= 0;
                  const trustInfo = trustMap[card.ticker];

                  return (
                    <div
                      key={card.ticker}
                      className={`p-6 rounded-2xl border transition-all flex flex-col justify-between space-y-4 relative overflow-hidden ${
                        isAbnormalMove
                          ? 'bg-rose-950/20 border-rose-800/60 shadow-xl shadow-rose-950/20 glow-rose'
                          : isAbnormalSilence
                          ? 'bg-amber-950/20 border-amber-800/60 shadow-xl shadow-amber-950/20 glow-amber'
                          : 'bg-gray-900/80 border-gray-800 hover:border-gray-700'
                      }`}
                    >
                      {/* Card Header */}
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3">
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm font-mono ${
                            isAbnormalMove
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              : isAbnormalSilence
                              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                              : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          }`}>
                            {card.ticker}
                          </div>
                          <div>
                            <h4 className="font-bold text-base text-white">{card.company_name}</h4>
                            <div className="text-xs text-gray-400 font-mono">${card.price?.toFixed(2)}</div>
                          </div>
                        </div>

                        {/* Badge */}
                        <div className="flex flex-col items-end space-y-1">
                          <span className={`px-2.5 py-1 rounded-lg text-xs font-bold font-mono border ${
                            isAbnormalMove
                              ? 'bg-rose-950 text-rose-300 border-rose-800'
                              : isAbnormalSilence
                              ? 'bg-amber-950 text-amber-300 border-amber-800'
                              : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                          }`}>
                            {card.badge_text}
                          </span>

                          {trustInfo && (
                            <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
                              trustInfo.has_conflict
                                ? 'bg-amber-950/90 text-amber-300 border-amber-800'
                                : 'bg-gray-950/80 text-gray-400 border-gray-800'
                            }`}>
                              {trustInfo.badge_text}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Story Card Bullet Points */}
                      <div className="space-y-2 py-2 border-y border-gray-800/60 flex-1">
                        {card.highlights?.map((bullet, bIdx) => (
                          <div key={bIdx} className="flex items-start space-x-2 text-xs leading-relaxed">
                            <span className={`font-bold mt-0.5 ${
                              isAbnormalMove ? 'text-rose-400' : isAbnormalSilence ? 'text-amber-400' : 'text-emerald-400'
                            }`}>•</span>
                            <span className={bIdx === 0 ? 'font-semibold text-white' : 'text-gray-300'}>{bullet}</span>
                          </div>
                        ))}
                      </div>

                      {/* AI Fact Summary Banner */}
                      {aiExplanations[card.ticker] && (
                        <div className="p-3 rounded-xl bg-gray-950/80 border border-emerald-500/30 text-xs space-y-1.5 shadow-inner">
                          <div className="flex items-center justify-between text-[10px] font-mono font-bold">
                            <span className="flex items-center space-x-1 text-emerald-400">
                              <Sparkles className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                              <span>AI Fact Summary</span>
                            </span>
                            <span className="px-2 py-0.5 bg-emerald-950 text-emerald-300 rounded border border-emerald-800/80 text-[9px]">
                              {aiExplanations[card.ticker].provider_label}
                            </span>
                          </div>
                          <p className="text-gray-300 text-[11px] leading-snug">
                            {aiExplanations[card.ticker].explanation}
                          </p>
                        </div>
                      )}


                      {/* Interactive Feedback Buttons */}
                      <div className="pt-2 flex items-center space-x-2 border-t border-gray-800/40">
                        <button
                          onClick={() => handleUserFeedback(card.ticker, 'news_clicked')}
                          disabled={actionLoading}
                          className="flex-1 py-1.5 px-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-[11px] font-medium text-amber-300 flex items-center justify-center space-x-1 border border-gray-700 transition"
                          title="Increase news weighting for your scores"
                        >
                          <Newspaper className="w-3 h-3" />
                          <span>+ News Weight</span>
                        </button>

                        <button
                          onClick={() => handleUserFeedback(card.ticker, 'volume_ignored')}
                          disabled={actionLoading}
                          className="flex-1 py-1.5 px-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-[11px] font-medium text-gray-300 flex items-center justify-center space-x-1 border border-gray-700 transition"
                          title="Decrease volume weighting for your scores"
                        >
                          <VolumeX className="w-3 h-3 text-gray-400" />
                          <span>- Vol Weight</span>
                        </button>
                      </div>

                      {/* Card Footer */}
                      <div className="flex items-center justify-between text-xs pt-1">
                        <div className={`font-mono font-bold flex items-center space-x-1 ${isPos ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {isPos ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                          <span>{isPos ? '+' : ''}{card.price_change_percent}%</span>
                        </div>

                        <button
                          onClick={() => {
                            const sc = surpriseScores[card.ticker];
                            if (sc) setActiveAuditStock(sc);
                            setViewMode('WATCHLIST');
                          }}
                          className="text-[11px] text-emerald-400 hover:underline font-mono flex items-center"
                        >
                          <span>Inspect details</span>
                          <ChevronRight className="w-3 h-3 ml-0.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          </div>
        )}

        {/* WATCHLIST GRID VIEW (UNDERNEATH OR SWITCHED) */}
        {viewMode === 'WATCHLIST' && (
          <div className="space-y-8">
            {/* Watchlist Section with Sort Controls */}
            <section className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center space-x-2">
                  <Flame className="w-5 h-5 text-amber-400" />
                  <h3 className="font-bold text-lg text-white">Watchlist Abnormality Ranking</h3>
                  <span className="text-xs text-gray-400 font-mono">({stocks.length} stocks)</span>
                </div>

                {/* Sort Control */}
                <div className="flex items-center space-x-2 text-xs">
                  <span className="text-gray-400 flex items-center space-x-1 font-mono">
                    <ArrowUpDown className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Sort by:</span>
                  </span>
                  <div className="inline-flex rounded-lg bg-gray-900 p-0.5 border border-gray-800">
                    <button
                      onClick={() => setSortBy('ABNORMAL')}
                      className={`px-3 py-1 rounded-md font-medium transition-all ${
                        sortBy === 'ABNORMAL' 
                          ? 'bg-emerald-500 text-black font-semibold shadow-md' 
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Most Abnormal (Surprise)
                    </button>
                    <button
                      onClick={() => setSortBy('CHANGE')}
                      className={`px-3 py-1 rounded-md font-medium transition-all ${
                        sortBy === 'CHANGE' 
                          ? 'bg-emerald-500 text-black font-semibold shadow-md' 
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Gain / Loss %
                    </button>
                    <button
                      onClick={() => setSortBy('TICKER')}
                      className={`px-3 py-1 rounded-md font-medium transition-all ${
                        sortBy === 'TICKER' 
                          ? 'bg-emerald-500 text-black font-semibold shadow-md' 
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Ticker (A-Z)
                    </button>
                  </div>
                </div>
              </div>

              {/* Watchlist Stock Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                {sortedStocks.map((stock) => {
                  const latest = stock.latest_event;
                  const surprise = surpriseScores[stock.ticker];
                  const trustInfo = trustMap[stock.ticker];
                  const isPos = latest?.price_change_percent >= 0;

                  return (
                    <div 
                      key={stock.ticker}
                      onClick={() => setActiveAuditStock(surprise)}
                      className={`p-4 rounded-xl transition-all cursor-pointer border relative overflow-hidden group ${
                        activeAuditStock?.ticker === stock.ticker
                          ? 'bg-gray-800/90 border-emerald-500 shadow-xl shadow-emerald-500/10'
                          : 'bg-gray-900/90 hover:bg-gray-800/60 border-gray-800'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold font-mono text-base text-white">{stock.ticker}</span>
                        {surprise && (
                          <div className={`px-2 py-0.5 rounded-md border text-[11px] font-bold font-mono flex items-center space-x-1 ${getScoreBadgeClass(surprise.category)}`}>
                            <span>{surprise.surprise_score}</span>
                            <span className="text-[9px] uppercase opacity-80">{surprise.category}</span>
                          </div>
                        )}
                      </div>

                      <div className="flex items-center justify-between mb-3">
                        <p className="text-[11px] text-gray-400 truncate">{stock.company_name}</p>
                        {trustInfo && (
                          <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono border ${
                            trustInfo.has_conflict
                              ? 'bg-amber-950 text-amber-400 border-amber-800'
                              : 'bg-gray-950 text-gray-400 border-gray-800'
                          }`}>
                            {trustInfo.badge_text}
                          </span>
                        )}
                      </div>

                      {latest ? (
                        <div>
                          <div className="text-xl font-bold font-mono text-white mb-1">
                            ${latest.price?.toFixed(2)}
                          </div>
                          <div className="flex items-center justify-between">
                            <div className={`flex items-center space-x-1 text-xs font-semibold font-mono ${isPos ? 'text-emerald-400' : 'text-rose-400'}`}>
                              {isPos ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                              <span>{isPos ? '+' : ''}{latest.price_change_percent}%</span>
                            </div>
                            
                            <div className="text-[10px] text-emerald-400 group-hover:underline flex items-center font-mono">
                              <span>Why score?</span>
                              <ChevronRight className="w-3 h-3 ml-0.5" />
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-xs text-gray-500 italic">No event state</div>
                      )}
                    </div>
                  );
                })}
              </div>
            </section>

            {/* Audit Breakdown Drawer / Modal */}
            {activeAuditStock && (
              <div className="p-6 rounded-2xl bg-gray-900 border border-gray-800 shadow-2xl space-y-6 relative overflow-hidden">
                <div className="flex items-start justify-between border-b border-gray-800 pb-4">
                  <div className="flex items-center space-x-3">
                    <div className={`px-3 py-1.5 rounded-xl border text-sm font-bold font-mono ${getScoreBadgeClass(activeAuditStock.category)}`}>
                      SURPRISE SCORE: {activeAuditStock.surprise_score}/100 — {activeAuditStock.category}
                    </div>
                    <div>
                      <h4 className="text-lg font-bold text-white flex items-center space-x-2">
                        <span>Audit Breakdown for {activeAuditStock.ticker}</span>
                      </h4>
                      <p className="text-xs text-gray-400">Auditable factor contribution &amp; personalized baseline formula explanation</p>
                    </div>
                  </div>

                  <button 
                    onClick={() => setActiveAuditStock(null)}
                    className="p-1 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-xl bg-gray-950/60 border border-gray-800 space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-gray-400">Price Volatility ({(w.volatility_weight*100).toFixed(0)}%)</span>
                      <span className="font-bold text-white">{activeAuditStock.volatility_score}/100</span>
                    </div>
                    <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
                      <div className="bg-emerald-400 h-full rounded-full transition-all" style={{ width: `${Math.min(100, activeAuditStock.volatility_score)}%` }}></div>
                    </div>
                    <p className="text-[10px] text-gray-400 font-mono">Z-score: {activeAuditStock.volatility_z_score}σ (60d StdDev: {activeAuditStock.historical_std_dev}%)</p>
                  </div>

                  <div className="p-4 rounded-xl bg-gray-950/60 border border-gray-800 space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-gray-400">Volume Spike ({(w.volume_weight*100).toFixed(0)}%)</span>
                      <span className="font-bold text-white">{activeAuditStock.volume_score}/100</span>
                    </div>
                    <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
                      <div className="bg-teal-400 h-full rounded-full transition-all" style={{ width: `${Math.min(100, activeAuditStock.volume_score)}%` }}></div>
                    </div>
                    <p className="text-[10px] text-gray-400 font-mono">Ratio: {activeAuditStock.volume_ratio}× 60-day avg volume</p>
                  </div>

                  <div className="p-4 rounded-xl bg-gray-950/60 border border-gray-800 space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-gray-400">News Impact ({(w.news_weight*100).toFixed(0)}%)</span>
                      <span className="font-bold text-white">{activeAuditStock.news_score}/100</span>
                    </div>
                    <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
                      <div className="bg-amber-400 h-full rounded-full transition-all" style={{ width: `${Math.min(100, activeAuditStock.news_score)}%` }}></div>
                    </div>
                    <p className="text-[10px] text-gray-400 font-mono">Structured sentiment signal</p>
                  </div>

                  <div className="p-4 rounded-xl bg-gray-950/60 border border-gray-800 space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-gray-400">Historical Extreme ({(w.extreme_weight*100).toFixed(0)}%)</span>
                      <span className="font-bold text-white">{activeAuditStock.extreme_score}/100</span>
                    </div>
                    <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
                      <div className="bg-cyan-400 h-full rounded-full transition-all" style={{ width: `${Math.min(100, activeAuditStock.extreme_score)}%` }}></div>
                    </div>
                    <p className="text-[10px] text-gray-400 font-mono">Percentile: {activeAuditStock.historical_extreme_percentile}%</p>
                  </div>
                </div>

                {/* AI Modular Fact Summary Section */}
                {aiExplanations[activeAuditStock.ticker] && (
                  <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-950/40 via-gray-950 to-teal-950/40 border border-emerald-500/40 shadow-xl space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Sparkles className="w-4 h-4 text-emerald-400 animate-pulse" />
                        <h5 className="font-bold text-xs text-white uppercase tracking-wider font-mono">
                          Modular AI Fact Summary
                        </h5>
                      </div>
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-700/60">
                        {aiExplanations[activeAuditStock.ticker].provider_label}
                      </span>
                    </div>

                    <p className="text-xs text-gray-200 leading-relaxed font-sans">
                      {aiExplanations[activeAuditStock.ticker].explanation}
                    </p>

                    <div className="text-[10px] text-gray-500 font-mono pt-1">
                      Zero macro hallucination rule active • Built strictly from auditable baseline metrics
                    </div>
                  </div>
                )}

                <div className="p-4 rounded-xl bg-gray-950/80 border border-gray-800 space-y-3">
                  <h5 className="font-semibold text-xs text-white uppercase tracking-wider font-mono flex items-center space-x-2">
                    <BarChart3 className="w-4 h-4 text-emerald-400" />
                    <span>Human-Readable Audit Explanations</span>
                  </h5>
                  <ul className="space-y-2">
                    {activeAuditStock.explanation_factors?.map((bullet, idx) => (
                      <li key={idx} className="flex items-start space-x-2 text-xs text-gray-200">
                        <span className="text-emerald-400 font-bold">•</span>
                        <span>{bullet}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-6 text-center text-xs text-gray-500">
        <p>MarketPulse — Smart Stock Watchlist &amp; Anomaly Intelligence</p>
      </footer>



    </div>
  );
}
