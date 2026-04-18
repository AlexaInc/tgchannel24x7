import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Play, SkipForward, Search, Music, LogIn, LogOut, Loader2, ListMusic } from 'lucide-react';

const API_BASE = window.location.origin;

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Auto-refresh bot state
  useEffect(() => {
    if (token) {
      const interval = setInterval(fetchState, 3000);
      fetchState();
      return () => clearInterval(interval);
    }
  }, [token]);

  const fetchState = async () => {
    try {
      const res = await axios.get(`${API_BASE}/state`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStatus(res.data);
    } catch (err) {
      if (err.response?.status === 401) handleLogout();
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('username', 'admin');
      formData.append('password', password);
      const res = await axios.post(`${API_BASE}/token`, formData);
      localStorage.setItem('token', res.data.access_token);
      setToken(res.data.access_token);
    } catch (err) {
      setError('Invalid password');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setStatus(null);
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery) return;
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/search?q=${encodeURIComponent(searchQuery)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSearchResults(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const playSong = async (query, playNow = false) => {
    try {
      await axios.post(`${API_BASE}/play?query=${encodeURIComponent(query)}&play_now=${playNow}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (playNow) {
        setSearchResults([]);
        setSearchQuery('');
      } else {
        // Show a brief success toast/indicator
        fetchState();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const skipSong = async () => {
    try {
      await axios.post(`${API_BASE}/skip`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchState();
    } catch (err) {
      console.error(err);
    }
  };

  if (!token) {
    return (
      <div className="flex-center" style={{ height: '100vh' }}>
        <div className="glass-card animate-fade" style={{ padding: '3rem', width: '100%', maxWidth: '400px' }}>
          <div className="flex-center" style={{ marginBottom: '2rem', gap: '1rem' }}>
            <Music size={40} color="#4f46e5" />
            <h1 style={{ fontSize: '2rem' }}>Echoflow</h1>
          </div>
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Admin Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                style={{ width: '100%' }}
                required
              />
            </div>
            {error && <p style={{ color: 'var(--error)', fontSize: '0.9rem' }}>{error}</p>}
            <button className="flex-center" style={{
              background: 'var(--primary)',
              color: 'white',
              padding: '12px',
              gap: '0.5rem'
            }} disabled={loading}>
              {loading ? <Loader2 className="animate-spin" /> : <LogIn size={20} />}
              Login
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="container animate-fade">
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            background: 'var(--primary)',
            padding: '10px',
            borderRadius: '12px',
            boxShadow: '0 0 20px rgba(79, 70, 229, 0.4)'
          }}>
            <Music size={24} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.5rem' }}>Echoflow Music</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>24/7 Channel Bot</p>
          </div>
        </div>
        <button onClick={handleLogout} style={{ background: 'var(--glass)', color: 'white', padding: '10px 20px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <LogOut size={18} /> Logout
        </button>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '2rem' }}>
        {/* Main Content */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Now Playing Card */}
          <div className="glass-card" style={{ padding: '2rem', position: 'relative', overflow: 'hidden' }}>
            <div style={{
              position: 'absolute',
              top: '-50px',
              right: '-50px',
              width: '200px',
              height: '200px',
              background: 'var(--primary)',
              filter: 'blur(100px)',
              opacity: 0.2,
              zIndex: 0
            }} />

            <div style={{ position: 'relative', zIndex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                <span style={{
                  background: status?.is_playing ? 'var(--success)' : 'var(--text-muted)',
                  color: 'white',
                  padding: '4px 12px',
                  borderRadius: '20px',
                  fontSize: '0.7rem',
                  textTransform: 'uppercase',
                  fontWeight: 'bold',
                  letterSpacing: '1px'
                }}>
                  {status?.is_playing ? 'Live & Speaking' : 'Waiting for song'}
                </span>
              </div>

              <h2 style={{ fontSize: '1.8rem', marginBottom: '0.5rem' }}>
                {status?.current_video_id ? 'Streaming Video @ 240p' : 'Ready to start'}
              </h2>
              <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
                {status?.current_video_id ? `Video ID: ${status.current_video_id}` : 'Queue up some music to begin'}
              </p>

              <div style={{ display: 'flex', gap: '1rem' }}>
                <button
                  onClick={skipSong}
                  className="flex-center"
                  style={{
                    background: 'var(--glass)',
                    color: 'white',
                    padding: '12px 24px',
                    gap: '0.5rem'
                  }}>
                  <SkipForward size={20} /> Skip Song
                </button>
              </div>
            </div>
          </div>

          {/* Search Section */}
          <div className="glass-card" style={{ padding: '2rem' }}>
            <form onSubmit={handleSearch} style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
              <div style={{ position: 'relative', flex: 1 }}>
                <Search size={20} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search for songs or videos..."
                  style={{ width: '100%', paddingLeft: '40px' }}
                />
              </div>
              <button style={{ background: 'var(--primary)', color: 'white', padding: '0 24px' }}>
                {loading ? <Loader2 className="animate-spin" /> : 'Search'}
              </button>
            </form>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {searchResults.map(video => (
                <div key={video.id} className="flex-center" style={{
                  justifyContent: 'space-between',
                  padding: '12px',
                  background: 'var(--glass)',
                  borderRadius: '16px',
                  border: '1px solid transparent',
                  transition: '0.2s'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1, minWidth: 0 }}>
                    <img src={video.thumbnail} alt="" style={{ width: '100px', height: '56px', objectFit: 'cover', borderRadius: '8px' }} />
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <p style={{ fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{video.title}</p>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {video.duration ? `${Math.floor(video.duration / 60)}:${String(video.duration % 60).padStart(2, '0')}` : 'Live/Unknown'}
                      </p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      onClick={() => playSong(video.id, false)}
                      className="flex-center"
                      title="Add to Queue"
                      style={{ background: 'var(--glass)', color: 'white', padding: '8px 12px', fontSize: '0.8rem', gap: '0.4rem' }}>
                      <ListMusic size={16} /> + Queue
                    </button>
                    <button
                      onClick={() => playSong(video.id, true)}
                      className="flex-center"
                      title="Play Now"
                      style={{ background: 'white', color: 'black', padding: '8px 12px', fontSize: '0.8rem', gap: '0.4rem', fontWeight: 'bold' }}>
                      <Play size={16} fill="black" /> Play Now
                    </button>
                  </div>
                </div>
              ))}
              {searchResults.length === 0 && !loading && (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                  No results yet. Try searching for a song!
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar / Queue */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div className="glass-card" style={{ padding: '2rem', height: 'fit-content' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
              <ListMusic size={20} color="var(--primary)" />
              <h3 style={{ fontSize: '1.2rem' }}>Up Next</h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {status?.queue?.map((item, i) => (
                <div key={i} style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>#{i + 1}</span>
                  <p style={{ fontSize: '0.9rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item}</p>
                </div>
              ))}
              {status?.queue?.length === 0 && (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center' }}>Queue is empty. Autoplay enabled.</p>
              )}
            </div>
          </div>

          <div className="glass-card" style={{ padding: '1.5rem', background: 'rgba(244, 114, 182, 0.05)' }}>
            <h4 style={{ color: 'var(--accent)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>Tip</h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              The bot automatically plays related songs from YouTube if the queue is empty.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
