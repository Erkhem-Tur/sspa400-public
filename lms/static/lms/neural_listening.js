(() => {
  'use strict';

  const engine = {
    voice: null,
    voices: [],
    activeButton: null,
    activeUtterance: null,
    keepAlive: null,
    enabled: 'speechSynthesis' in window,
  };

  function pickVoice(voices) {
    const english = voices.filter((voice) => /^en[-_]/i.test(voice.lang || ''));
    return english.find((voice) => /natural|neural|online/i.test(voice.name))
      || english.find((voice) => /google.*us english/i.test(voice.name))
      || english.find((voice) => /microsoft.*(aria|jenny|guy|zira|david)/i.test(voice.name))
      || english.find((voice) => /^en-US/i.test(voice.lang || ''))
      || english.find((voice) => /^en-GB/i.test(voice.lang || ''))
      || english[0]
      || voices[0]
      || null;
  }

  function refreshVoices() {
    if (!engine.enabled) return [];
    engine.voices = window.speechSynthesis.getVoices();
    engine.voice = pickVoice(engine.voices);
    return engine.voices;
  }

  if (engine.enabled) {
    refreshVoices();
    window.speechSynthesis.onvoiceschanged = refreshVoices;
    window.setTimeout(refreshVoices, 250);
    window.setTimeout(refreshVoices, 1200);
  }

  function setButton(button, isSpeaking) {
    if (!button) return;
    if (!button.dataset.originalHtml) button.dataset.originalHtml = button.innerHTML;
    button.disabled = isSpeaking;
    button.innerHTML = isSpeaking
      ? '<span class="spinner-border spinner-border-sm me-1"></span>Playing'
      : button.dataset.originalHtml;
  }

  function emitStatus(callback, status, detail = '') {
    if (typeof callback === 'function') callback({
      status,
      detail,
      voice: engine.voice ? `${engine.voice.name} (${engine.voice.lang})` : 'Browser default voice',
      supported: engine.enabled,
    });
  }

  function stop(callback) {
    window.clearInterval(engine.keepAlive);
    engine.keepAlive = null;
    if (engine.activeButton) setButton(engine.activeButton, false);
    engine.activeButton = null;
    engine.activeUtterance = null;
    if (engine.enabled) window.speechSynthesis.cancel();
    emitStatus(callback, 'stopped', 'Audio stopped.');
  }

  function cleanText(text) {
    return String(text || '')
      .replace(/\s+/g, ' ')
      .replace(/\s+([.,!?;:])/g, '$1')
      .trim();
  }

  function chunks(text, maxLength = 230) {
    const sentences = cleanText(text).match(/[^.!?]+[.!?]*/g) || [];
    const output = [];
    let current = '';
    sentences.forEach((sentence) => {
      const next = `${current} ${sentence}`.trim();
      if (next.length > maxLength && current) {
        output.push(current);
        current = sentence.trim();
      } else {
        current = next;
      }
    });
    if (current) output.push(current);
    return output.length ? output : [cleanText(text)];
  }

  function speakChunk(queue, options) {
    const text = queue.shift();
    if (!text) {
      stop(options.onStatus);
      emitStatus(options.onStatus, 'complete', 'Listening complete.');
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = options.lang || 'en-US';
    utterance.rate = Number(options.rate || 1);
    utterance.pitch = Number(options.pitch || 1);
    utterance.volume = 1;
    if (engine.voice) utterance.voice = engine.voice;
    engine.activeUtterance = utterance;

    utterance.onstart = () => emitStatus(options.onStatus, 'playing', options.label || 'Neural listening active.');
    utterance.onend = () => speakChunk(queue, options);
    utterance.onerror = (event) => {
      if (event.error !== 'interrupted') emitStatus(options.onStatus, 'error', 'Audio was blocked. Press play again.');
      stop(options.onStatus);
    };

    window.speechSynthesis.speak(utterance);
  }

  function speak(text, options = {}) {
    if (!engine.enabled) {
      emitStatus(options.onStatus, 'unsupported', 'This browser does not support speech playback.');
      return;
    }
    refreshVoices();
    stop(options.onStatus);
    engine.activeButton = options.button || null;
    setButton(engine.activeButton, true);
    emitStatus(options.onStatus, 'loading', 'Preparing clear English audio...');

    const queue = chunks(text, options.maxChunkLength || 230);
    engine.keepAlive = window.setInterval(() => {
      if (!window.speechSynthesis.speaking) return;
      window.speechSynthesis.pause();
      window.speechSynthesis.resume();
    }, 9000);

    window.setTimeout(() => speakChunk(queue, options), 40);
  }

  function explain(text) {
    const words = cleanText(text)
      .toLowerCase()
      .replace(/[^a-z0-9' -]/g, ' ')
      .split(/\s+/)
      .filter((word) => word.length > 4);
    const keyWords = [...new Set(words)].slice(0, 6);
    return {
      preview: cleanText(text).slice(0, 160),
      keyWords,
      steps: [
        'First listen for the situation.',
        'Second listen for names, numbers, time, and location.',
        'Third listen and repeat the key phrase aloud.',
      ],
    };
  }

  window.NeuralListeningEngine = {
    speak,
    stop,
    explain,
    refreshVoices,
    getVoiceLabel: () => (engine.voice ? `${engine.voice.name} (${engine.voice.lang})` : 'Browser default voice'),
    isSupported: () => engine.enabled,
  };
  document.documentElement.dataset.neuralListening = 'ready';
})();
