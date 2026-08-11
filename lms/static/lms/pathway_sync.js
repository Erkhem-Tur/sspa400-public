(() => {
  'use strict';

  function csrfToken() {
    const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function normalized(state) {
    return {
      completed: Array.isArray(state?.completed) ? state.completed : [],
      drafts: state?.drafts && typeof state.drafts === 'object' ? state.drafts : {},
      scores: state?.scores && typeof state.scores === 'object' ? state.scores : {},
    };
  }

  function create(endpoint) {
    let timer = null;
    let pending = null;

    async function hydrate(localState) {
      const local = normalized(localState);
      if (!endpoint) return local;
      try {
        const response = await fetch(endpoint, {credentials: 'same-origin', headers: {'Accept': 'application/json'}});
        if (!response.ok) return local;
        const server = normalized(await response.json());
        return {
          completed: [...new Set([...server.completed, ...local.completed].map(String))],
          drafts: {...server.drafts, ...local.drafts},
          scores: {...server.scores, ...local.scores},
        };
      } catch (_) {
        return local;
      }
    }

    async function flush() {
      timer = null;
      if (!endpoint || !pending) return;
      const payload = pending;
      pending = null;
      try {
        await fetch(endpoint, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken()},
          body: JSON.stringify(normalized(payload)),
        });
      } catch (_) {
        // The local copy remains available and will merge on the next visit.
      }
    }

    function save(state) {
      if (!endpoint) return;
      pending = state;
      window.clearTimeout(timer);
      timer = window.setTimeout(flush, 450);
    }

    window.addEventListener('pagehide', flush);
    return {hydrate, save, flush};
  }

  window.PathwayProgressSync = {create};
})();
