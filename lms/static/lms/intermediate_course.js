(() => {
  'use strict';

  const root = document.getElementById('intermediatePathway');
  if (!root) return;

  const STORAGE_KEY = 'sspa-intermediate-pathway';
  const operational = JSON.parse(document.getElementById('operationalLessonData').textContent);
  const params = new URLSearchParams(window.location.search);
  const state = {
    foundation: [],
    lessons: [],
    diagnostic: null,
    final: null,
    current: Number(params.get('lesson')) || 1,
    view: 'lesson',
    tab: 'overview',
    progress: loadProgress(),
    diagnosticAnswers: {},
    diagnosticSubmitted: false,
    answersVisible: false,
  };

  const el = (id) => document.getElementById(id);
  const esc = (value) => String(value ?? '').replace(/[&<>'"]/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
  })[char]);

  function loadProgress() {
    try {
      const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      return { completed: Array.isArray(data.completed) ? data.completed : [], drafts: data.drafts || {} };
    } catch (_) {
      return { completed: [], drafts: {} };
    }
  }

  function saveProgress() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.progress));
  }

  function lessonKey(lesson) {
    return lesson.kind === 'foundation' ? `foundation-${lesson.number}` : `operational-${lesson.number}`;
  }

  function updateProgress() {
    const completed = new Set(state.progress.completed);
    const count = state.lessons.filter((lesson) => completed.has(lessonKey(lesson))).length;
    el('ipProgressText').textContent = `${count} / ${state.lessons.length} complete`;
    el('ipProgressFill').style.width = `${(count / state.lessons.length) * 100}%`;
    document.querySelector('.ip-progress-track').setAttribute('aria-valuenow', String(count));
    const next = state.lessons.find((lesson) => !completed.has(lessonKey(lesson)));
    el('ipNextText').textContent = next ? `Lesson ${next.pathway_number} is next` : 'Intermediate pathway complete';
  }

  function setUrlLesson(number) {
    const url = new URL(window.location.href);
    url.searchParams.set('lesson', number);
    window.history.replaceState({}, '', url);
  }

  function renderList() {
    const query = el('ipSearch').value.toLocaleLowerCase().trim();
    const completed = new Set(state.progress.completed);
    const groups = [
      { kind: 'foundation', heading: 'Phase 1 · Foundation' },
      { kind: 'operational', heading: 'Phase 2 · Operational' },
    ];
    let html = '';
    let visible = 0;
    groups.forEach((group) => {
      const matches = state.lessons.filter((lesson) => {
        const content = [lesson.title, lesson.level, lesson.language_focus || lesson.grammar, lesson.scenario || ''].join(' ').toLocaleLowerCase();
        return lesson.kind === group.kind && (!query || content.includes(query));
      });
      if (!matches.length) return;
      html += `<div class="ip-list-heading">${group.heading}</div>`;
      html += matches.map((lesson) => {
        visible += 1;
        const done = completed.has(lessonKey(lesson));
        return `
          <button class="ip-lesson-button ${state.view === 'lesson' && lesson.pathway_number === state.current ? 'active' : ''}" type="button" data-lesson="${lesson.pathway_number}">
            <span class="ip-list-number">${String(lesson.pathway_number).padStart(2, '0')}</span>
            <span><span class="ip-list-title">${esc(lesson.title)}</span><span class="ip-list-meta">${esc(lesson.level)} · ${lesson.kind === 'foundation' ? '90 min' : 'Operational application'}</span></span>
            <i class="bi bi-check-circle-fill ip-list-check ${done ? 'done' : ''}"></i>
          </button>`;
      }).join('');
    });
    el('ipLessonList').innerHTML = visible ? html : '<div class="ip-empty">No matching lessons.</div>';
  }

  function renderLesson() {
    if (state.view === 'diagnostic') return renderDiagnostic();
    if (state.view === 'final') return renderFinal();
    const lesson = state.lessons.find((item) => item.pathway_number === state.current);
    if (!lesson) return;
    updatePhase(lesson.kind);
    if (lesson.kind === 'foundation') renderFoundation(lesson);
    else renderOperational(lesson);
  }

  function lessonHeader(lesson, subtitle) {
    const done = state.progress.completed.includes(lessonKey(lesson));
    return `
      <header class="ip-lesson-head">
        <div><div class="ip-kicker">Lesson ${lesson.pathway_number} · ${lesson.kind === 'foundation' ? 'Phase 1 Foundation' : 'Phase 2 Operational'}</div><h2>${esc(lesson.title)}</h2><div class="ip-meta">${esc(subtitle)}</div></div>
        <button class="btn ${done ? 'btn-success' : 'btn-outline-success'} btn-sm ip-complete" type="button" data-action="complete"><i class="bi bi-check2-circle me-1"></i>${done ? 'Completed' : 'Mark complete'}</button>
      </header>`;
  }

  function tabBar(tabs) {
    return `<nav class="ip-tabs" aria-label="Lesson sections">${tabs.map(([id, label, icon]) => `
      <button class="ip-tab ${state.tab === id ? 'active' : ''}" type="button" data-tab="${id}"><i class="bi ${icon} me-1"></i>${label}</button>
    `).join('')}</nav>`;
  }

  function renderFoundation(lesson) {
    const tabs = [
      ['overview', 'Lesson Plan', 'bi-list-check'],
      ['vocabulary', 'Vocabulary', 'bi-book'],
      ['reading', 'Reading & Listening', 'bi-volume-up'],
      ['practice', 'Practice & Homework', 'bi-pencil-square'],
    ];
    let panel = '';
    if (state.tab === 'overview') {
      panel = `
        <div class="ip-section"><h3>Learning outcomes</h3><ul class="ip-outcomes">${lesson.outcomes.map((item) => `<li>${esc(item)}</li>`).join('')}</ul></div>
        <div class="ip-section"><h3>Language focus</h3><div class="ip-focus">${esc(lesson.language_focus)}</div></div>
        <div class="ip-section"><h3>90-minute sequence</h3><div class="ip-timeline">${lesson.sequence.map((stage) => `<div class="ip-stage"><time>${esc(stage.time)}</time><strong>${esc(stage.stage)}</strong><span>${esc(stage.action)}</span></div>`).join('')}</div></div>
        <div class="ip-section"><h3>Main performance task</h3><div class="ip-task">${esc(lesson.performance_task)}</div></div>`;
    } else if (state.tab === 'vocabulary') {
      panel = `<div class="ip-section"><h3>Target vocabulary · 6 words</h3><div class="ip-vocab-grid">${lesson.vocabulary.map((item, index) => `
        <article class="ip-vocab-item"><div class="ip-vocab-top"><strong>${esc(item.word)}</strong><button class="ip-icon-button" type="button" data-speak-vocab="${index}" title="Listen" aria-label="Listen to ${esc(item.word)}"><i class="bi bi-volume-up"></i></button></div><p>${esc(item.meaning)}</p><small>${esc(item.example)}</small></article>
      `).join('')}</div></div>`;
    } else if (state.tab === 'reading') {
      panel = `
        <div class="ip-section"><h3>${esc(lesson.reading_title)}</h3><div class="ip-reading-toolbar"><button class="btn btn-outline-primary btn-sm" type="button" data-action="speak-reading"><i class="bi bi-volume-up me-1"></i>Listen</button><button class="btn btn-outline-secondary btn-sm" type="button" data-action="stop-audio"><i class="bi bi-stop-fill me-1"></i>Stop</button></div><div class="ip-reading">${esc(lesson.reading)}</div></div>
        <div class="ip-section"><h3>Reading check</h3>${questionInputs(lesson, 'reading')}</div>`;
    } else {
      panel = `
        <div class="ip-section"><h3>Language practice</h3>${questionInputs(lesson, 'language')}</div>
        <div class="ip-section"><h3>Speaking task</h3><div class="ip-task">${esc(lesson.performance_task)}</div></div>
        <div class="ip-section"><h3>Homework</h3><div class="ip-homework">${esc(lesson.homework)}</div></div>`;
    }
    el('ipContent').innerHTML = lessonHeader(lesson, `${lesson.level} · ${lesson.time} · ${lesson.language_focus}`) + tabBar(tabs) + `<div class="ip-tab-panel">${panel}</div>`;
  }

  function questionInputs(lesson, type) {
    const questions = type === 'reading' ? lesson.reading_questions : lesson.language_practice;
    const answers = type === 'reading' ? lesson.reading_answers : lesson.language_answers;
    return `${questions.map((question, index) => {
      const draftKey = `${lessonKey(lesson)}-${type}-${index}`;
      return `<div class="ip-question"><label for="draft-${type}-${index}">${index + 1}. ${esc(question)}</label><textarea class="form-control form-control-sm" id="draft-${type}-${index}" rows="2" data-draft="${esc(draftKey)}" placeholder="Write your answer...">${esc(state.progress.drafts[draftKey] || '')}</textarea><div class="ip-answer ${state.answersVisible ? 'show' : ''}"><strong>Model answer:</strong> ${esc(answers[index] || 'Teacher check required.')}</div></div>`;
    }).join('')}<button class="btn btn-outline-success btn-sm mt-2" type="button" data-action="toggle-answers"><i class="bi bi-eye me-1"></i>${state.answersVisible ? 'Hide model answers' : 'Show model answers'}</button>`;
  }

  function renderOperational(lesson) {
    el('ipContent').innerHTML = lessonHeader(lesson, `B1 · Course Library lesson ${lesson.number} · ${lesson.grammar}`) + `
      <div class="ip-tab-panel">
        <div class="ip-operational-grid">
          <section class="ip-op-block wide"><div class="ip-label">Operational scenario</div><p>${esc(lesson.scenario)}</p></section>
          <section class="ip-op-block"><div class="ip-label">Grammar & communication</div><p>${esc(lesson.grammar)}</p></section>
          <section class="ip-op-block"><div class="ip-label">Target vocabulary</div><div class="ip-chips">${lesson.vocabulary.map((word) => `<span class="ip-chip">${esc(word)}</span>`).join('')}</div></section>
          <section class="ip-op-block"><div class="ip-label">Performance task</div><p>${esc(lesson.role_play)}</p></section>
          <section class="ip-op-block"><div class="ip-label">Writing task</div><p>${esc(lesson.writing)}</p></section>
        </div>
        <div class="ip-resource-links">
          <a class="btn btn-primary btn-sm" href="/worksheets/?tab=worksheets&level=B1"><i class="bi bi-journal-text me-1"></i>B1 Worksheets</a>
          <a class="btn btn-outline-primary btn-sm" href="/terminology/?level=B1"><i class="bi bi-book me-1"></i>B1 Terminology</a>
          <a class="btn btn-outline-secondary btn-sm" href="/course/?level=B1&lesson=${lesson.number}"><i class="bi bi-box-arrow-up-right me-1"></i>Course Library lesson</a>
        </div>
      </div>`;
  }

  function renderDiagnostic() {
    updatePhase('foundation');
    const result = diagnosticResult();
    el('ipContent').innerHTML = `<div class="ip-assessment">
      <header class="ip-assessment-head"><div><div class="ip-kicker">Before Lesson 1 · 15-20 minutes</div><h2>Diagnostic Test</h2><p class="ip-meta">Choose the best answer. Complete without a dictionary.</p></div><button class="btn btn-outline-secondary btn-sm" type="button" data-action="return-lesson"><i class="bi bi-x-lg"></i></button></header>
      ${state.diagnostic.questions.map((question, qIndex) => `<div class="ip-mcq"><p>${question.number}. ${esc(question.prompt)}</p><div class="ip-mcq-options">${question.options.map((option, index) => {
        const selected = state.diagnosticAnswers[qIndex] === index;
        let mark = selected ? 'selected' : '';
        if (state.diagnosticSubmitted && index === question.answer) mark = 'correct';
        if (state.diagnosticSubmitted && selected && index !== question.answer) mark = 'wrong';
        return `<button class="ip-mcq-option ${mark}" type="button" data-diagnostic-q="${qIndex}" data-diagnostic-option="${index}">${String.fromCharCode(65 + index)}. ${esc(option)}</button>`;
      }).join('')}</div></div>`).join('')}
      <button class="btn btn-primary mt-3" type="button" data-action="submit-diagnostic">Submit diagnostic</button>
      ${state.diagnosticSubmitted ? `<div class="ip-result"><strong>${result.score} / 15 · ${esc(result.profile.label)}</strong><div class="mt-1">${esc(result.profile.guidance)}</div></div>` : ''}
    </div>`;
  }

  function diagnosticResult() {
    const score = state.diagnostic.questions.reduce((total, question, index) => total + (state.diagnosticAnswers[index] === question.answer ? 1 : 0), 0);
    const profile = state.diagnostic.profiles.find((item) => score >= item.min && score <= item.max) || state.diagnostic.profiles[0];
    return { score, profile };
  }

  function renderFinal() {
    updatePhase('operational');
    el('ipContent').innerHTML = `<div class="ip-assessment">
      <header class="ip-assessment-head"><div><div class="ip-kicker">After Lesson 20 · 75 points</div><h2>Final Assessment</h2><p class="ip-meta">Reading and language 30 · Writing 20 · Speaking 25</p></div><button class="btn btn-outline-secondary btn-sm" type="button" data-action="return-lesson"><i class="bi bi-x-lg"></i></button></header>
      <section class="ip-section"><h3>Part A · Reading</h3><div class="ip-reading">${esc(state.final.reading)}</div>${assessmentQuestions(state.final.reading_questions, state.final.reading_answers, 'final-reading')}</section>
      <section class="ip-section"><h3>Part A · Language</h3>${assessmentQuestions(state.final.language_questions, state.final.language_answers, 'final-language')}</section>
      <section class="ip-section"><h3>Part B · Writing</h3><div class="ip-homework">${esc(state.final.writing)}</div><textarea class="form-control mt-2" rows="8" data-draft="final-writing" placeholder="Write 120-150 words...">${esc(state.progress.drafts['final-writing'] || '')}</textarea></section>
      <section class="ip-section"><h3>Part C · Speaking</h3><div class="ip-task">${esc(state.final.speaking)}</div></section>
    </div>`;
  }

  function assessmentQuestions(questions, answers, prefix) {
    return questions.map((question, index) => `<div class="ip-question"><label>${index + 1}. ${esc(question)}</label><textarea class="form-control form-control-sm" rows="2" data-draft="${prefix}-${index}">${esc(state.progress.drafts[`${prefix}-${index}`] || '')}</textarea><div class="ip-answer ${state.answersVisible ? 'show' : ''}"><strong>Answer guide:</strong> ${esc(answers[index])}</div></div>`).join('') + `<button class="btn btn-outline-success btn-sm mt-2" type="button" data-action="toggle-answers"><i class="bi bi-eye me-1"></i>Show / hide answer guide</button>`;
  }

  function updatePhase(kind) {
    document.querySelectorAll('.ip-phase').forEach((button) => button.classList.toggle('active', button.dataset.phase === kind));
  }

  function selectLesson(number) {
    state.current = number;
    state.view = 'lesson';
    state.tab = number <= 8 ? 'overview' : 'operational';
    state.answersVisible = false;
    setUrlLesson(number);
    renderList();
    renderLesson();
    el('ipContent').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function toggleComplete() {
    const lesson = state.lessons.find((item) => item.pathway_number === state.current);
    const key = lessonKey(lesson);
    const completed = new Set(state.progress.completed);
    if (completed.has(key)) completed.delete(key); else completed.add(key);
    state.progress.completed = [...completed];
    saveProgress();
    updateProgress();
    renderList();
    renderLesson();
  }

  function speak(text) {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 0.92;
    window.speechSynthesis.speak(utterance);
  }

  function bindEvents() {
    el('ipSearch').addEventListener('input', renderList);
    el('ipLessonList').addEventListener('click', (event) => {
      const button = event.target.closest('[data-lesson]');
      if (button) selectLesson(Number(button.dataset.lesson));
    });
    document.querySelectorAll('.ip-phase').forEach((button) => {
      button.addEventListener('click', () => selectLesson(button.dataset.phase === 'foundation' ? 1 : 9));
    });
    el('diagnosticOpen').addEventListener('click', () => { state.view = 'diagnostic'; state.answersVisible = false; renderList(); renderLesson(); });
    el('finalOpen').addEventListener('click', () => { state.view = 'final'; state.answersVisible = false; renderList(); renderLesson(); });
    el('ipContent').addEventListener('click', (event) => {
      const tab = event.target.closest('[data-tab]');
      if (tab) { state.tab = tab.dataset.tab; state.answersVisible = false; renderLesson(); return; }
      const action = event.target.closest('[data-action]')?.dataset.action;
      if (action === 'complete') toggleComplete();
      if (action === 'toggle-answers') { state.answersVisible = !state.answersVisible; renderLesson(); }
      if (action === 'speak-reading') {
        const lesson = state.lessons.find((item) => item.pathway_number === state.current);
        speak(lesson.reading);
      }
      if (action === 'stop-audio' && 'speechSynthesis' in window) window.speechSynthesis.cancel();
      if (action === 'return-lesson') selectLesson(state.current);
      if (action === 'submit-diagnostic') { state.diagnosticSubmitted = true; renderDiagnostic(); }
      const vocabButton = event.target.closest('[data-speak-vocab]');
      if (vocabButton) {
        const lesson = state.lessons.find((item) => item.pathway_number === state.current);
        const item = lesson.vocabulary[Number(vocabButton.dataset.speakVocab)];
        speak(`${item.word}. ${item.example}`);
      }
      const option = event.target.closest('[data-diagnostic-q]');
      if (option && !state.diagnosticSubmitted) {
        state.diagnosticAnswers[Number(option.dataset.diagnosticQ)] = Number(option.dataset.diagnosticOption);
        renderDiagnostic();
      }
    });
    el('ipContent').addEventListener('input', (event) => {
      if (!event.target.dataset.draft) return;
      state.progress.drafts[event.target.dataset.draft] = event.target.value;
      saveProgress();
    });
  }

  async function init() {
    bindEvents();
    try {
      const response = await fetch(root.dataset.source);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      state.foundation = data.lessons.map((lesson) => ({ ...lesson, kind: 'foundation', pathway_number: lesson.number }));
      const operationalLessons = operational.map((lesson) => ({ ...lesson, kind: 'operational' }));
      state.lessons = [...state.foundation, ...operationalLessons];
      state.diagnostic = data.diagnostic;
      state.final = data.final_assessment;
      if (!state.lessons.some((lesson) => lesson.pathway_number === state.current)) state.current = 1;
      updateProgress();
      renderList();
      renderLesson();
    } catch (_) {
      el('ipContent').innerHTML = '';
      el('ipError').textContent = 'Intermediate course data could not be loaded. Please refresh the page.';
      el('ipError').classList.remove('d-none');
    }
  }

  init();
})();
