(function () {
  'use strict';

  const root = document.getElementById('courseLibrary');
  if (!root) return;

  const rows = Array.from(document.querySelectorAll('.course-row'));
  const storageKey = 'sspa-course-library-complete';
  let completed;
  try {
    completed = new Set(JSON.parse(localStorage.getItem(storageKey) || '[]').map(Number));
  } catch (error) {
    completed = new Set();
  }
  const requestedLevel = new URLSearchParams(window.location.search).get('level');
  let activeLevel = ['A1', 'A2', 'B1'].includes(requestedLevel) ? requestedLevel : 'all';

  function saveCompleted() {
    localStorage.setItem(storageKey, JSON.stringify(Array.from(completed).sort((a, b) => a - b)));
  }

  function updateProgress() {
    const count = completed.size;
    const percent = Math.round((count / rows.length) * 100);
    document.getElementById('courseProgressText').textContent = `${count} / ${rows.length}`;
    document.getElementById('courseProgressFill').style.width = `${percent}%`;
    document.querySelector('.course-progress-track').setAttribute('aria-valuenow', String(count));
    const next = rows.find((row) => !completed.has(Number(row.dataset.number)));
    document.getElementById('courseProgressNote').textContent = next ? `Lesson ${next.dataset.number} is next.` : 'Course complete.';
    document.querySelectorAll('[data-complete-lesson]').forEach((button) => {
      button.classList.toggle('is-done', completed.has(Number(button.dataset.completeLesson)));
    });
  }

  function applyFilters() {
    const query = document.getElementById('courseSearch').value.toLowerCase().trim();
    let visible = 0;
    rows.forEach((row) => {
      const levelMatch = activeLevel === 'all' || row.dataset.level === activeLevel;
      const searchMatch = !query || row.dataset.search.includes(query);
      const show = levelMatch && searchMatch;
      row.hidden = !show;
      if (show) visible += 1;
    });
    document.getElementById('courseVisibleCount').textContent = `${visible} lesson${visible === 1 ? '' : 's'}`;
    document.getElementById('courseEmpty').style.display = visible ? 'none' : 'block';
  }

  function toggleDetail(number, forceOpen) {
    const detail = document.getElementById(`course-detail-${number}`);
    const button = document.querySelector(`[data-expand-lesson="${number}"]`);
    const open = typeof forceOpen === 'boolean' ? forceOpen : !detail.classList.contains('open');
    detail.classList.toggle('open', open);
    button.setAttribute('aria-expanded', String(open));
  }

  document.querySelectorAll('.course-filter').forEach((button) => {
    const selected = button.dataset.level === activeLevel;
    button.classList.toggle('active', selected);
    button.addEventListener('click', () => {
      activeLevel = button.dataset.level;
      document.querySelectorAll('.course-filter').forEach((item) => item.classList.toggle('active', item === button));
      applyFilters();
    });
  });

  document.getElementById('courseSearch').addEventListener('input', applyFilters);
  document.querySelectorAll('[data-expand-lesson]').forEach((button) => {
    button.addEventListener('click', () => toggleDetail(button.dataset.expandLesson));
  });
  document.querySelectorAll('[data-complete-lesson]').forEach((button) => {
    button.addEventListener('click', () => {
      const number = Number(button.dataset.completeLesson);
      if (completed.has(number)) completed.delete(number); else completed.add(number);
      saveCompleted();
      updateProgress();
    });
  });

  document.getElementById('continueCourse').addEventListener('click', () => {
    const next = rows.find((row) => !completed.has(Number(row.dataset.number)) && !row.hidden);
    if (!next) return;
    toggleDetail(next.dataset.number, true);
    next.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });

  const lessonParam = Number(new URLSearchParams(window.location.search).get('lesson'));
  if (lessonParam && document.getElementById(`course-lesson-${lessonParam}`)) {
    toggleDetail(lessonParam, true);
    document.getElementById(`course-lesson-${lessonParam}`).scrollIntoView({ block: 'center' });
  }

  updateProgress();
  applyFilters();
}());
