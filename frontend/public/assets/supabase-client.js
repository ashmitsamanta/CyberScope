/**
 * CYBERSCOPE — Supabase Authentication Client
 * Provides unified authentication, session persistence, token synchronization,
 * and seamless fallback for local demonstration/evaluation.
 */
(function(window) {
  'use strict';

  var SUPABASE_CDN = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';
  var STORAGE_USER_KEY = 'cyberscopeUser';
  var STORAGE_SESSION_KEY = 'cyberscopeSession';
  var STORAGE_TOKEN_KEY = 'cyberscopeAccessToken';
  var STORAGE_CUSTOM_URL = 'cyberscope_supabase_url';
  var STORAGE_CUSTOM_KEY = 'cyberscope_supabase_anon_key';

  var DEMO_ACCOUNT = {
    id: 'demo-investigator-001',
    email: 'investigator@cyberscope.io',
    password: 'password123',
    name: 'Investigator Demo',
    role: 'Investigator',
    phone: '9876543210',
    organization: 'TetraByte Cyber Defense',
    is_demo: true
  };

  var state = {
    client: null,
    configured: false,
    url: '',
    anonKey: '',
    initialized: false,
    initPromise: null
  };

  function loadScript(src) {
    return new Promise(function(resolve, reject) {
      if (window.supabase) return resolve(window.supabase);
      var existing = document.querySelector('script[src*="@supabase/supabase-js"]');
      if (existing) {
        existing.addEventListener('load', function() { resolve(window.supabase); });
        existing.addEventListener('error', reject);
        return;
      }
      var s = document.createElement('script');
      s.src = src;
      s.async = true;
      s.onload = function() { resolve(window.supabase); };
      s.onerror = function() { reject(new Error('Failed to load Supabase SDK from CDN')); };
      document.head.appendChild(s);
    });
  }

  // Clear any legacy custom config stored in localStorage from earlier in-page settings
  try {
    localStorage.removeItem(STORAGE_CUSTOM_URL);
    localStorage.removeItem(STORAGE_CUSTOM_KEY);
  } catch(e) {}

  var PROJECT_ENV_CONFIG = {
    url: 'https://ivyzighppyaiizunvqkb.supabase.co',
    anonKey: 'sb_publishable_r0f7WBvARHXEnK2E1IqfKQ_T-t5SGrY'
  };

  async function fetchServerConfig() {
    try {
      var res = await fetch('/api/auth/config');
      if (res.ok) {
        var data = await res.json();
        if (data.supabase_url && data.supabase_anon_key) {
          return { url: data.supabase_url, anonKey: data.supabase_anon_key };
        }
      }
    } catch (e) {
      // Backend not running or offline
    }
    return null;
  }

  async function init() {
    if (state.initPromise) return state.initPromise;

    state.initPromise = (async function() {
      // 1. Determine Supabase config: window override -> server endpoint (/api/auth/config) -> project .env credentials
      var config = null;

      if (window.CYBERSCOPE_SUPABASE_CONFIG) {
        config = window.CYBERSCOPE_SUPABASE_CONFIG;
      }

      if (!config) {
        config = await fetchServerConfig();
      }

      if (!config || !config.url || !config.anonKey) {
        config = PROJECT_ENV_CONFIG;
      }

      if (config && config.url && config.anonKey && config.url.indexOf('your-project') === -1) {
        state.url = config.url;
        state.anonKey = config.anonKey;
        state.configured = true;
      } else {
        state.configured = false;
      }

      // 2. Load Supabase library if configured
      if (state.configured) {
        try {
          await loadScript(SUPABASE_CDN);
          if (window.supabase && typeof window.supabase.createClient === 'function') {
            state.client = window.supabase.createClient(state.url, state.anonKey, {
              auth: {
                persistSession: true,
                autoRefreshToken: true,
                detectSessionInUrl: true
              }
            });

            // Listen to auth state changes
            state.client.auth.onAuthStateChange(function(event, session) {
              if (session && session.user) {
                var meta = session.user.user_metadata || {};
                var u = {
                  id: session.user.id,
                  email: session.user.email,
                  name: meta.name || meta.full_name || (session.user.email ? session.user.email.split('@')[0] : 'Investigator'),
                  role: meta.role || 'Investigator',
                  phone: meta.phone || '',
                  organization: meta.organization || '',
                  is_demo: false
                };
                localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(u));
                localStorage.setItem(STORAGE_SESSION_KEY, 'active');
                localStorage.setItem(STORAGE_TOKEN_KEY, session.access_token);
              } else if (event === 'SIGNED_OUT') {
                localStorage.removeItem(STORAGE_USER_KEY);
                localStorage.removeItem(STORAGE_SESSION_KEY);
                localStorage.removeItem(STORAGE_TOKEN_KEY);
              }
            });
          }
        } catch (err) {
          console.warn('Supabase initialization warning:', err);
          state.configured = false;
        }
      }

      // Fallback demo account setup if no local user is stored
      if (!localStorage.getItem(STORAGE_USER_KEY)) {
        localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(DEMO_ACCOUNT));
      }

      state.initialized = true;
      return state;
    })();

    return state.initPromise;
  }

  function getUser() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_USER_KEY) || 'null');
    } catch(e) {
      return null;
    }
  }

  function isAuthenticated() {
    return localStorage.getItem(STORAGE_SESSION_KEY) === 'active' && Boolean(getUser());
  }

  function getAuthHeaders() {
    var token = localStorage.getItem(STORAGE_TOKEN_KEY);
    if (token) {
      return { 'Authorization': 'Bearer ' + token };
    }
    return {};
  }

  async function signIn(credentials) {
    await init();
    var email = (credentials.email || '').trim().toLowerCase();
    var password = credentials.password || '';

    if (!email || !password) {
      return { success: false, error: { message: 'Please enter both email and password.' } };
    }

    // A. Use real Supabase client if configured
    if (state.configured && state.client) {
      try {
        var res = await state.client.auth.signInWithPassword({
          email: email,
          password: password
        });

        if (res.error) {
          return { success: false, error: res.error };
        }

        var session = res.data.session;
        var user = res.data.user;
        var meta = (user && user.user_metadata) || {};
        var userObj = {
          id: user.id,
          email: user.email,
          name: meta.name || meta.full_name || email.split('@')[0],
          role: meta.role || 'Investigator',
          phone: meta.phone || '',
          organization: meta.organization || '',
          is_demo: false
        };

        localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(userObj));
        localStorage.setItem(STORAGE_SESSION_KEY, 'active');
        if (session) {
          localStorage.setItem(STORAGE_TOKEN_KEY, session.access_token);
        }

        return { success: true, user: userObj, session: session };
      } catch (err) {
        return { success: false, error: { message: err.message || 'Supabase authentication failed.' } };
      }
    }

    // B. Demo mode authentication
    var savedUser = getUser() || DEMO_ACCOUNT;
    var demoMatch = (email === String(DEMO_ACCOUNT.email).toLowerCase() && password === DEMO_ACCOUNT.password);
    var savedMatch = (savedUser && email === String(savedUser.email).toLowerCase() && (password === savedUser.password || password === 'password123'));

    if (demoMatch || savedMatch) {
      var activeUser = demoMatch ? DEMO_ACCOUNT : savedUser;
      localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(activeUser));
      localStorage.setItem(STORAGE_SESSION_KEY, 'active');
      localStorage.setItem(STORAGE_TOKEN_KEY, 'demo-token');
      return {
        success: true,
        user: activeUser,
        session: { access_token: 'demo-token' }
      };
    }

    return {
      success: false,
      error: { message: 'Invalid email or password. (For demo login, use investigator@cyberscope.io / password123)' }
    };
  }

  async function signUp(data) {
    await init();
    var email = (data.email || '').trim().toLowerCase();
    var password = data.password || '';
    var name = (data.name || '').trim();
    var phone = (data.phone || '').trim();
    var role = data.role || 'Investigator';
    var organization = (data.organization || '').trim();

    if (!email || !password || !name) {
      return { success: false, error: { message: 'Please provide name, email, and password.' } };
    }

    // A. Use real Supabase client if configured
    if (state.configured && state.client) {
      try {
        var res = await state.client.auth.signUp({
          email: email,
          password: password,
          options: {
            data: {
              name: name,
              phone: phone,
              role: role,
              organization: organization
            }
          }
        });

        if (res.error) {
          return { success: false, error: res.error };
        }

        var user = res.data.user;
        var session = res.data.session;
        var userObj = {
          id: user ? user.id : 'sb-user',
          email: email,
          name: name,
          phone: phone,
          role: role,
          organization: organization,
          is_demo: false
        };

        // Cache details
        localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(userObj));
        if (session) {
          localStorage.setItem(STORAGE_SESSION_KEY, 'active');
          localStorage.setItem(STORAGE_TOKEN_KEY, session.access_token);
        }

        return {
          success: true,
          user: userObj,
          session: session,
          needsEmailConfirmation: user && !session
        };
      } catch (err) {
        return { success: false, error: { message: err.message || 'Supabase signup failed.' } };
      }
    }

    // B. Demo mode signup
    var newUser = {
      id: 'demo-' + Date.now(),
      email: email,
      password: password,
      name: name,
      phone: phone,
      role: role,
      organization: organization,
      is_demo: true
    };
    localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(newUser));
    localStorage.removeItem(STORAGE_SESSION_KEY);
    return {
      success: true,
      user: newUser,
      session: null,
      needsEmailConfirmation: false
    };
  }

  async function signOut() {
    try {
      if (state.configured && state.client) {
        await state.client.auth.signOut();
      }
    } catch(e) {}
    localStorage.removeItem(STORAGE_SESSION_KEY);
    localStorage.removeItem(STORAGE_TOKEN_KEY);
    return true;
  }

  async function resetPassword(email) {
    await init();
    if (!email) return { success: false, error: { message: 'Please enter your email address.' } };

    if (state.configured && state.client) {
      try {
        var res = await state.client.auth.resetPasswordForEmail(email, {
          redirectTo: window.location.origin + '/signin.html'
        });
        if (res.error) return { success: false, error: res.error };
        return { success: true, message: 'Password reset instructions have been sent to ' + email };
      } catch(err) {
        return { success: false, error: { message: err.message } };
      }
    }

    return {
      success: true,
      message: 'Demo mode: In live mode, Supabase will dispatch an email recovery link. For demo testing, use password123.'
    };
  }

  async function verifySession() {
    await init();
    if (state.configured && state.client) {
      var res = await state.client.auth.getSession();
      if (res.error || !res.data.session) {
        localStorage.removeItem(STORAGE_SESSION_KEY);
        localStorage.removeItem(STORAGE_TOKEN_KEY);
        return false;
      }
      return true;
    }
    return isAuthenticated();
  }

  function setCustomConfig(url, key) {
    if (url && key) {
      localStorage.setItem(STORAGE_CUSTOM_URL, url.trim());
      localStorage.setItem(STORAGE_CUSTOM_KEY, key.trim());
      state.initialized = false;
      state.initPromise = null;
      return true;
    }
    return false;
  }

  function clearCustomConfig() {
    localStorage.removeItem(STORAGE_CUSTOM_URL);
    localStorage.removeItem(STORAGE_CUSTOM_KEY);
    state.initialized = false;
    state.initPromise = null;
  }

  // Auto-initialize in background on page load
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() { init(); });
    } else {
      init();
    }
  }

  // Export public API
  window.CyberScopeAuth = {
    init: init,
    getUser: getUser,
    isAuthenticated: isAuthenticated,
    getAuthHeaders: getAuthHeaders,
    signIn: signIn,
    signUp: signUp,
    signOut: signOut,
    resetPassword: resetPassword,
    verifySession: verifySession,
    setCustomConfig: setCustomConfig,
    clearCustomConfig: clearCustomConfig,
    isConfigured: function() { return state.configured; },
    getConfig: function() { return { url: state.url, configured: state.configured }; },
    DEMO_ACCOUNT: DEMO_ACCOUNT
  };

})(typeof window !== 'undefined' ? window : this);
