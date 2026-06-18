(() => {
  'use strict';

  const root = document.getElementById('beginnerPathway');
  if (!root) return;

  const lessons = JSON.parse(document.getElementById('beginnerLessonData').textContent);
  const storageKey = 'sspa-beginner-alc-pack';
  const draftVersion = 2;
  const requested = new URLSearchParams(window.location.search).get('lesson');
  const state = {
    current: lessons.some((lesson) => lesson.slug === requested) ? requested : lessons[0].slug,
    saved: loadState(),
    resizeObserver: null,
  };

  const frame = document.getElementById('bpFrame');

  function loadState() {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
      return {
        completed: Array.isArray(saved.completed) ? saved.completed : [],
        drafts: saved.draftVersion === draftVersion ? (saved.drafts || {}) : {},
        draftVersion,
      };
    } catch (_) {
      return { completed: [], drafts: {}, draftVersion };
    }
  }

  function saveState() {
    localStorage.setItem(storageKey, JSON.stringify(state.saved));
  }

  function currentLesson() {
    return lessons.find((lesson) => lesson.slug === state.current);
  }

  function updateUi() {
    const lesson = currentLesson();
    const completed = new Set(state.saved.completed);
    document.getElementById('bpLessonBook').textContent = lesson.book;
    document.getElementById('bpLessonTitle').textContent = lesson.title;
    document.getElementById('bpCurrentText').textContent = lesson.book;
    document.querySelectorAll('[data-lesson]').forEach((button) => {
      const active = button.dataset.lesson === state.current;
      button.classList.toggle('active', active);
      button.querySelector('.bp-check').classList.toggle('done', completed.has(button.dataset.lesson));
    });
    const completeButton = document.getElementById('bpComplete');
    const done = completed.has(state.current);
    completeButton.className = `btn ${done ? 'btn-success' : 'btn-outline-success'} btn-sm`;
    completeButton.innerHTML = `<i class="bi bi-check2-circle me-1"></i>${done ? 'Completed' : 'Mark complete'}`;
    const count = lessons.filter((item) => completed.has(item.slug)).length;
    document.getElementById('bpProgressText').textContent = `${count} / ${lessons.length} complete`;
    document.getElementById('bpProgressFill').style.width = `${(count / lessons.length) * 100}%`;
    document.querySelector('.bp-progress-track').setAttribute('aria-valuenow', String(count));
    const index = lessons.findIndex((item) => item.slug === state.current);
    document.getElementById('bpPrevious').disabled = index === 0;
    document.getElementById('bpNext').disabled = index === lessons.length - 1;
  }

  function setUrl() {
    const url = new URL(window.location.href);
    url.searchParams.set('lesson', state.current);
    window.history.replaceState({}, '', url);
  }

  function openLesson(slug, updateFrame = true) {
    if (!lessons.some((lesson) => lesson.slug === slug)) return;
    state.current = slug;
    setUrl();
    updateUi();
    if (updateFrame) frame.src = `${root.dataset.base}${slug}.html`;
  }

  function toggleComplete() {
    const completed = new Set(state.saved.completed);
    if (completed.has(state.current)) completed.delete(state.current); else completed.add(state.current);
    state.saved.completed = [...completed];
    saveState();
    updateUi();
  }

  function move(direction) {
    const index = lessons.findIndex((lesson) => lesson.slug === state.current);
    const next = lessons[index + direction];
    if (next) openLesson(next.slug);
  }

  function syncFrame() {
    let documentRef;
    try {
      documentRef = frame.contentDocument;
      const filename = new URL(frame.contentWindow.location.href).pathname.split('/').pop();
      const slug = filename?.replace('.html', '');
      if (lessons.some((lesson) => lesson.slug === slug)) openLesson(slug, false);
    } catch (_) {
      return;
    }
    if (!documentRef?.body) return;

    const resize = () => {
      frame.style.height = `${Math.max(1200, documentRef.documentElement.scrollHeight + 20)}px`;
    };
    resize();
    if (state.resizeObserver) state.resizeObserver.disconnect();
    if ('ResizeObserver' in window) {
      state.resizeObserver = new ResizeObserver(resize);
      state.resizeObserver.observe(documentRef.body);
    }

    const fields = [...documentRef.querySelectorAll('input, textarea')];
    fields.forEach((field, index) => {
      const key = `${state.current}-${index}`;
      if (state.saved.drafts[key] != null) field.value = state.saved.drafts[key];
      field.addEventListener('input', () => {
        state.saved.drafts[key] = field.value;
        saveState();
      });
    });
  }

  document.querySelectorAll('[data-lesson]').forEach((button) => {
    button.addEventListener('click', () => openLesson(button.dataset.lesson));
  });
  document.getElementById('bpComplete').addEventListener('click', toggleComplete);
  document.getElementById('bpPrevious').addEventListener('click', () => move(-1));
  document.getElementById('bpNext').addEventListener('click', () => move(1));
  frame.addEventListener('load', syncFrame);

  updateUi();
  frame.src = `${root.dataset.base}${state.current}.html`;
})();
