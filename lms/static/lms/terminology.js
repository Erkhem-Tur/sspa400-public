(() => {
  'use strict';

  const root = document.querySelector('.term-page');
  if (!root) return;

  const STORAGE_KEY = 'sspaTerminologyProgress';
  const params = new URLSearchParams(window.location.search);
  const state = {
    items: [],
    filtered: [],
    selectedId: null,
    mode: params.get('mode') === 'listening' ? 'listening' : 'vocabulary',
    level: ['A2', 'B1', 'B2', 'C1'].includes(params.get('level')) ? params.get('level') : 'all',
    activity: 'choice',
    speed: 1,
    currentListen: null,
    answered: false,
    session: { correct: 0, attempts: 0, streak: 0 },
    progress: loadProgress(),
  };

  const el = (id) => document.getElementById(id);
  const esc = (value) => String(value ?? '').replace(/[&<>'"]/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
  })[char]);

  function loadProgress() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      return {
        learned: Array.isArray(saved.learned) ? saved.learned : [],
        favorites: Array.isArray(saved.favorites) ? saved.favorites : [],
      };
    } catch (_) {
      return { learned: [], favorites: [] };
    }
  }

  function saveProgress() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.progress));
    updateProgress();
  }

  function updateProgress() {
    const count = state.progress.learned.length;
    el('termProgressText').textContent = `${count} / ${state.items.length || 310}`;
    el('termProgressFill').style.width = `${state.items.length ? (count / state.items.length) * 100 : 0}%`;
  }

  function unique(values) {
    return [...new Set(values)];
  }

  function shuffle(values) {
    const output = [...values];
    for (let i = output.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [output[i], output[j]] = [output[j], output[i]];
    }
    return output;
  }

  function normalize(value) {
    return String(value || '')
      .toLocaleLowerCase('en')
      .replace(/[\u2018\u2019]/g, "'")
      .replace(/[^a-z0-9' ]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function initModules(modules) {
    const select = el('termModule');
    modules.forEach((module) => {
      const option = document.createElement('option');
      option.value = module;
      option.textContent = module;
      select.appendChild(option);
    });
  }

  function applyFilters({ resetListening = true } = {}) {
    const query = normalize(el('termSearch').value);
    const module = el('termModule').value;
    const type = el('termType').value;
    const priority = el('termPriority').value;
    const status = el('termStatus').value;
    const learned = new Set(state.progress.learned);
    const favorites = new Set(state.progress.favorites);

    state.filtered = state.items.filter((item) => {
      const haystack = normalize([
        item.front, item.back_mn, item.definition_en, item.example_en, item.tags, item.module,
      ].join(' '));
      if (query && !haystack.includes(query)) return false;
      if (module !== 'all' && item.module !== module) return false;
      if (type !== 'all' && item.item_type !== type) return false;
      if (priority !== 'all' && item.priority !== priority) return false;
      if (state.level !== 'all' && item.difficulty !== state.level) return false;
      if (status === 'learned' && !learned.has(item.item_id)) return false;
      if (status === 'unlearned' && learned.has(item.item_id)) return false;
      if (status === 'favorite' && !favorites.has(item.item_id)) return false;
      return true;
    });

    if (!state.filtered.some((item) => item.item_id === state.selectedId)) {
      state.selectedId = state.filtered[0]?.item_id || null;
    }
    renderList();
    renderDetail();
    if (resetListening && state.mode === 'listening') nextListeningItem();
  }

  function renderList() {
    const learned = new Set(state.progress.learned);
    el('termCount').textContent = `${state.filtered.length} of ${state.items.length} items`;
    if (!state.filtered.length) {
      el('termList').innerHTML = '<div class="term-empty"><i class="bi bi-search d-block fs-3 mb-2"></i>No terminology matches these filters.</div>';
      return;
    }
    el('termList').innerHTML = state.filtered.map((item) => `
      <button class="term-row ${item.item_id === state.selectedId ? 'active' : ''}" type="button" data-id="${esc(item.item_id)}">
        <span class="term-id">${esc(item.item_id)}</span>
        <span><span class="term-word">${esc(item.front)}</span><span class="term-translation">${esc(item.back_mn)}</span></span>
        <span class="term-badges">
          <span class="term-badge">${esc(item.difficulty)}</span>
          <span class="term-badge ${item.priority === 'Core' ? 'core' : ''}">${esc(item.priority)}</span>
          ${learned.has(item.item_id) ? '<span class="term-badge learned"><i class="bi bi-check-lg"></i></span>' : ''}
        </span>
      </button>
    `).join('');
  }

  function renderDetail() {
    const item = state.items.find((entry) => entry.item_id === state.selectedId);
    if (!item) {
      el('termDetail').innerHTML = '<div class="term-empty">Select a terminology item to study it.</div>';
      return;
    }
    const isLearned = state.progress.learned.includes(item.item_id);
    const isFavorite = state.progress.favorites.includes(item.item_id);
    el('termDetail').innerHTML = `
      <div class="term-detail-top">
        <div><div class="term-kicker">${esc(item.module)} · ${esc(item.difficulty)}</div><h2>${esc(item.front)}</h2></div>
        <button class="icon-btn ${isFavorite ? 'active' : ''}" type="button" data-action="favorite" title="Favorite" aria-label="Favorite"><i class="bi bi-star${isFavorite ? '-fill' : ''}"></i></button>
      </div>
      <div class="term-mn">${esc(item.back_mn)}</div>
      <div class="term-detail-block"><div class="term-label">Definition</div><p>${esc(item.definition_en)}</p></div>
      ${item.example_en ? `<div class="term-detail-block"><div class="term-label">Operational example</div><p>${esc(item.example_en)}</p></div>` : ''}
      <div class="term-detail-block"><div class="term-label">Study note</div><p>${esc(item.review_note)} · ${esc(item.item_type === 'operational_phrase' ? 'Operational phrase' : 'Terminology')}</p></div>
      <div class="term-actions">
        <button class="btn btn-primary" type="button" data-action="speak"><i class="bi bi-volume-up me-1"></i>Pronunciation</button>
        <button class="btn btn-outline-primary" type="button" data-action="full-audio"><i class="bi bi-headphones me-1"></i>Full audio</button>
        <button class="btn ${isLearned ? 'btn-success' : 'btn-outline-success'}" type="button" data-action="learned"><i class="bi bi-check2-circle me-1"></i>${isLearned ? 'Learned' : 'Mark learned'}</button>
      </div>
      <div class="source-note">Source: ${esc(item.source_reference)}</div>
    `;
  }

  function toggleProgress(key, itemId) {
    const values = new Set(state.progress[key]);
    if (values.has(itemId)) values.delete(itemId);
    else values.add(itemId);
    state.progress[key] = [...values];
    saveProgress();
    applyFilters({ resetListening: false });
  }

  function speak(text) {
    if (!('speechSynthesis' in window)) {
      showError('Audio is not supported in this browser. Please use a current version of Chrome or Edge.');
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = state.speed;
    const voices = window.speechSynthesis.getVoices();
    utterance.voice = voices.find((voice) => voice.lang.startsWith('en-US'))
      || voices.find((voice) => voice.lang.startsWith('en'))
      || null;
    window.speechSynthesis.speak(utterance);
  }

  function showError(message) {
    el('termError').textContent = message;
    el('termError').classList.remove('d-none');
  }

  function setMode(mode, updateUrl = true) {
    state.mode = mode;
    document.querySelectorAll('.term-mode').forEach((button) => {
      button.classList.toggle('active', button.dataset.mode === mode);
    });
    el('vocabularyView').classList.toggle('active', mode === 'vocabulary');
    el('listeningView').classList.toggle('active', mode === 'listening');
    if (mode === 'listening' && !state.currentListen) nextListeningItem();
    if (updateUrl) {
      const url = new URL(window.location.href);
      if (mode === 'listening') url.searchParams.set('mode', 'listening');
      else url.searchParams.delete('mode');
      window.history.replaceState({}, '', url);
    }
  }

  function nextListeningItem() {
    const pool = state.filtered.length ? state.filtered : state.items;
    if (!pool.length) return;
    const candidates = pool.filter((item) => item.item_id !== state.currentListen?.item_id);
    state.currentListen = (candidates.length ? candidates : pool)[Math.floor(Math.random() * (candidates.length || pool.length))];
    state.answered = false;
    renderListeningQuestion();
    window.setTimeout(() => speak(listeningText()), 120);
  }

  function listeningText() {
    if (!state.currentListen) return '';
    return state.activity === 'dictation' ? state.currentListen.front : state.currentListen.audio_script;
  }

  function renderListeningQuestion() {
    const item = state.currentListen;
    if (!item) return;
    el('listenFeedback').className = 'listen-feedback';
    el('listenFeedback').textContent = '';
    el('listenPrompt').textContent = state.activity === 'dictation'
      ? 'Listen and type the English term or operational phrase.'
      : 'Listen carefully, then choose the Mongolian meaning.';
    if (state.activity === 'dictation') {
      el('listenQuestion').innerHTML = `
        <div class="dictation-row">
          <input class="form-control" id="dictationInput" type="text" autocomplete="off" placeholder="Type what you hear..." aria-label="Dictation answer">
          <button class="btn btn-primary" id="dictationCheck" type="button">Check</button>
        </div>`;
      el('dictationInput').addEventListener('keydown', (event) => {
        if (event.key === 'Enter') checkDictation();
      });
      el('dictationCheck').addEventListener('click', checkDictation);
    } else {
      const distractorPool = unique(state.items
        .filter((entry) => entry.item_id !== item.item_id)
        .map((entry) => entry.back_mn));
      const options = shuffle([item.back_mn, ...shuffle(distractorPool).slice(0, 3)]);
      el('listenQuestion').innerHTML = `<div class="listen-options">${options.map((option) => `
        <button class="listen-option" type="button" data-answer="${esc(option)}">${esc(option)}</button>
      `).join('')}</div>`;
    }
  }

  function answerListening(correct, answerText = '') {
    if (state.answered) return;
    state.answered = true;
    state.session.attempts += 1;
    if (correct) {
      state.session.correct += 1;
      state.session.streak += 1;
    } else {
      state.session.streak = 0;
    }
    const feedback = el('listenFeedback');
    feedback.className = `listen-feedback ${correct ? 'correct' : 'wrong'}`;
    feedback.innerHTML = correct
      ? `<i class="bi bi-check-circle-fill me-1"></i>Correct. <span class="listen-answer">${esc(state.currentListen.front)}</span>`
      : `<i class="bi bi-x-circle-fill me-1"></i>${answerText ? `Your answer: ${esc(answerText)}. ` : ''}Correct answer: <span class="listen-answer">${esc(state.currentListen.front)} · ${esc(state.currentListen.back_mn)}</span>`;
    updateListeningStats();
  }

  function checkDictation() {
    if (state.answered) return;
    const input = el('dictationInput');
    const answer = input.value.trim();
    if (!answer) return;
    const correct = normalize(answer) === normalize(state.currentListen.front);
    input.classList.toggle('is-valid', correct);
    input.classList.toggle('is-invalid', !correct);
    answerListening(correct, answer);
  }

  function updateListeningStats() {
    el('listenCorrect').textContent = state.session.correct;
    el('listenAttempts').textContent = state.session.attempts;
    el('listenAccuracy').textContent = `${state.session.attempts ? Math.round((state.session.correct / state.session.attempts) * 100) : 0}%`;
    el('listenStreak').textContent = state.session.streak;
  }

  function bindEvents() {
    let searchTimer;
    el('termSearch').addEventListener('input', () => {
      window.clearTimeout(searchTimer);
      searchTimer = window.setTimeout(() => applyFilters(), 120);
    });
    ['termModule', 'termType', 'termPriority', 'termStatus'].forEach((id) => {
      el(id).addEventListener('change', () => applyFilters());
    });
    el('termLevels').addEventListener('click', (event) => {
      const button = event.target.closest('[data-level]');
      if (!button) return;
      state.level = button.dataset.level;
      document.querySelectorAll('.term-level').forEach((entry) => entry.classList.toggle('active', entry === button));
      applyFilters();
    });
    document.querySelectorAll('.term-mode').forEach((button) => {
      button.addEventListener('click', () => setMode(button.dataset.mode));
    });
    el('termList').addEventListener('click', (event) => {
      const row = event.target.closest('[data-id]');
      if (!row) return;
      state.selectedId = row.dataset.id;
      renderList();
      renderDetail();
    });
    el('termDetail').addEventListener('click', (event) => {
      const button = event.target.closest('[data-action]');
      const item = state.items.find((entry) => entry.item_id === state.selectedId);
      if (!button || !item) return;
      if (button.dataset.action === 'favorite') toggleProgress('favorites', item.item_id);
      if (button.dataset.action === 'learned') toggleProgress('learned', item.item_id);
      if (button.dataset.action === 'speak') speak(item.front);
      if (button.dataset.action === 'full-audio') speak(item.audio_script);
    });
    el('listenActivities').addEventListener('click', (event) => {
      const button = event.target.closest('[data-activity]');
      if (!button) return;
      state.activity = button.dataset.activity;
      document.querySelectorAll('[data-activity]').forEach((entry) => entry.classList.toggle('active', entry === button));
      nextListeningItem();
    });
    el('listenSpeeds').addEventListener('click', (event) => {
      const button = event.target.closest('[data-speed]');
      if (!button) return;
      state.speed = Number(button.dataset.speed);
      document.querySelectorAll('[data-speed]').forEach((entry) => entry.classList.toggle('active', entry === button));
      speak(listeningText());
    });
    el('listenPlay').addEventListener('click', () => speak(listeningText()));
    el('listenNext').addEventListener('click', nextListeningItem);
    el('listenQuestion').addEventListener('click', (event) => {
      const button = event.target.closest('[data-answer]');
      if (!button || state.answered) return;
      const correct = button.dataset.answer === state.currentListen.back_mn;
      document.querySelectorAll('.listen-option').forEach((option) => {
        if (option.dataset.answer === state.currentListen.back_mn) option.classList.add('correct');
      });
      if (!correct) button.classList.add('wrong');
      answerListening(correct);
    });
  }

  async function init() {
    bindEvents();
    try {
      const response = await fetch(root.dataset.source);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (!Array.isArray(data.items) || data.items.length !== 310) throw new Error('Unexpected terminology data');
      state.items = data.items;
      initModules(data.meta.modules);
      state.selectedId = state.items[0].item_id;
      document.querySelectorAll('.term-level').forEach((button) => {
        button.classList.toggle('active', button.dataset.level === state.level);
      });
      updateProgress();
      applyFilters({ resetListening: false });
      setMode(state.mode, false);
    } catch (_) {
      showError('Terminology data could not be loaded. Please refresh the page.');
      el('termCount').textContent = 'Unavailable';
    }
  }

  init();
})();
