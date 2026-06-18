(function () {
  'use strict';

  const root = document.getElementById('alcLesson');
  if (!root) return;

  const lessonId = root.dataset.lessonId;
  const storageKey = `alc-book4-lesson2-${lessonId}`;
  const defaultState = {
    learned: [],
    completed: [],
    homework: [],
    bestQuiz: 0,
  };

  let state;
  try {
    state = Object.assign({}, defaultState, JSON.parse(localStorage.getItem(storageKey) || '{}'));
  } catch (error) {
    state = Object.assign({}, defaultState);
  }

  function saveState() {
    localStorage.setItem(storageKey, JSON.stringify(state));
  }

  function speak(text, rate) {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = rate || 0.82;
    window.speechSynthesis.speak(utterance);
  }

  function shuffle(items) {
    const copy = items.slice();
    for (let index = copy.length - 1; index > 0; index -= 1) {
      const swapIndex = Math.floor(Math.random() * (index + 1));
      [copy[index], copy[swapIndex]] = [copy[swapIndex], copy[index]];
    }
    return copy;
  }

  function normalize(text) {
    return text.toLowerCase().replace(/[?.!,]/g, '').replace(/\s+/g, ' ').trim();
  }

  const vocabulary = [
    { en: 'soldier', mn: 'армийн цэргийн алба хаагч', group: 'people' },
    { en: 'sailor', mn: 'тэнгисийн цэргийн алба хаагч', group: 'people' },
    { en: 'airman', mn: 'агаарын хүчний алба хаагч', group: 'people' },
    { en: 'Army post', mn: 'армийн анги, байрлал', group: 'people' },
    { en: 'naval base', mn: 'тэнгисийн цэргийн бааз', group: 'people' },
    { en: 'Air Force base', mn: 'агаарын хүчний бааз', group: 'people' },
    { en: 'uniform', mn: 'дүрэмт хувцас', group: 'duty' },
    { en: 'rank', mn: 'цол', group: 'duty' },
    { en: 'insignia', mn: 'цолны тэмдэг', group: 'duty' },
    { en: 'stripe', mn: 'цолны зураас', group: 'duty' },
    { en: 'ID card', mn: 'албаны үнэмлэх', group: 'duty' },
    { en: 'name tag', mn: 'нэрийн тэмдэг', group: 'duty' },
    { en: 'report for duty', mn: 'үүрэг гүйцэтгэхээр илтгэх', group: 'duty' },
    { en: 'on time', mn: 'цагтаа', group: 'duty' },
    { en: 'take a break', mn: 'завсарлага авах', group: 'duty' },
    { en: 'instructor', mn: 'сургагч багш', group: 'duty' },
    { en: 'General · Gen', mn: 'генерал', group: 'rank' },
    { en: 'Colonel · Col', mn: 'хурандаа', group: 'rank' },
    { en: 'Lieutenant Colonel · Lt Col', mn: 'дэд хурандаа', group: 'rank' },
    { en: 'Major · Maj', mn: 'хошууч', group: 'rank' },
    { en: 'Captain · Capt', mn: 'ахмад', group: 'rank' },
    { en: 'First Lieutenant · 1st Lt', mn: 'ахлах дэслэгч', group: 'rank' },
    { en: 'Second Lieutenant · 2nd Lt', mn: 'дэслэгч', group: 'rank' },
  ];

  const groupLabels = {
    people: 'People & places',
    duty: 'Uniform & duty',
    rank: 'Officer rank',
  };

  let activeFilter = 'all';

  function renderVocabulary() {
    const grid = document.getElementById('vocabGrid');
    const words = activeFilter === 'all' ? vocabulary : vocabulary.filter((word) => word.group === activeFilter);
    grid.innerHTML = words.map((word) => {
      const learned = state.learned.includes(word.en);
      return `
        <article class="word-card${learned ? ' learned' : ''}">
          <div>
            <div class="word-kind">${groupLabels[word.group]}</div>
            <div class="word-en">${word.en}</div>
            <div class="word-mn">${word.mn}</div>
          </div>
          <div class="word-actions">
            <button type="button" class="icon-btn word-listen" data-word="${word.en}" title="Listen" aria-label="Listen to ${word.en}"><i class="bi bi-volume-up"></i></button>
            <button type="button" class="icon-btn learn-toggle${learned ? ' active' : ''}" data-word="${word.en}" title="Mark learned" aria-label="Mark ${word.en} learned"><i class="bi bi-check2"></i></button>
          </div>
        </article>`;
    }).join('');

    document.getElementById('learnedCount').textContent = `${state.learned.length} of ${vocabulary.length} words learned`;

    grid.querySelectorAll('.word-listen').forEach((button) => {
      button.addEventListener('click', () => speak(button.dataset.word));
    });
    grid.querySelectorAll('.learn-toggle').forEach((button) => {
      button.addEventListener('click', () => {
        const word = button.dataset.word;
        if (state.learned.includes(word)) {
          state.learned = state.learned.filter((item) => item !== word);
        } else {
          state.learned.push(word);
        }
        saveState();
        renderVocabulary();
      });
    });
  }

  document.querySelectorAll('#vocabFilters button').forEach((button) => {
    button.addEventListener('click', () => {
      activeFilter = button.dataset.filter;
      document.querySelectorAll('#vocabFilters button').forEach((item) => item.classList.toggle('active', item === button));
      renderVocabulary();
    });
  });

  const stageOrder = ['vocabulary', 'pronunciation', 'grammar', 'time', 'reading', 'quiz'];

  function updateProgress() {
    const completedCount = state.completed.filter((item) => stageOrder.includes(item)).length;
    const percent = Math.round((completedCount / stageOrder.length) * 100);
    document.getElementById('progressText').textContent = `${completedCount} / ${stageOrder.length}`;
    document.getElementById('progressFill').style.width = `${percent}%`;
    document.querySelector('.alc-progress-track').setAttribute('aria-valuenow', String(completedCount));
    document.getElementById('progressNote').textContent = completedCount === stageOrder.length
      ? 'Lesson complete. Finish your service timeline.'
      : `Next: ${stageOrder.find((item) => !state.completed.includes(item)).replace(/^./, (letter) => letter.toUpperCase())}`;
    document.querySelectorAll('.complete-btn').forEach((button) => {
      const complete = state.completed.includes(button.dataset.complete);
      button.classList.toggle('is-complete', complete);
      button.innerHTML = complete
        ? '<i class="bi bi-check2-circle me-1"></i> Stage complete'
        : '<i class="bi bi-check2-circle me-1"></i> Mark stage complete';
    });
  }

  document.querySelectorAll('.complete-btn').forEach((button) => {
    button.addEventListener('click', () => {
      const section = button.dataset.complete;
      if (state.completed.includes(section)) {
        state.completed = state.completed.filter((item) => item !== section);
      } else {
        state.completed.push(section);
      }
      saveState();
      updateProgress();
    });
  });

  const pronunciationWords = [
    { word: 'checked', sound: 't' }, { word: 'watched', sound: 't' },
    { word: 'worked', sound: 't' }, { word: 'cleaned', sound: 'd' },
    { word: 'learned', sound: 'd' }, { word: 'called', sound: 'd' },
    { word: 'counted', sound: 'id' }, { word: 'repeated', sound: 'id' },
    { word: 'wanted', sound: 'id' }, { word: 'selected', sound: 'id' },
  ];
  let pronIndex = 0;
  let pronCorrect = 0;
  let pronAttempts = 0;
  let pronLocked = false;

  function renderPronunciation() {
    const item = pronunciationWords[pronIndex % pronunciationWords.length];
    document.getElementById('pronWord').textContent = item.word;
    document.querySelectorAll('#pronAnswers button').forEach((button) => button.classList.remove('correct', 'wrong'));
    pronLocked = false;
  }

  document.getElementById('pronListen').addEventListener('click', () => {
    speak(pronunciationWords[pronIndex % pronunciationWords.length].word, 0.7);
  });
  document.querySelectorAll('#pronAnswers button').forEach((button) => {
    button.addEventListener('click', () => {
      if (pronLocked) return;
      pronLocked = true;
      const item = pronunciationWords[pronIndex % pronunciationWords.length];
      const correct = button.dataset.sound === item.sound;
      pronAttempts += 1;
      if (correct) pronCorrect += 1;
      button.classList.add(correct ? 'correct' : 'wrong');
      document.querySelector(`#pronAnswers [data-sound="${item.sound}"]`).classList.add('correct');
      const feedback = document.getElementById('pronFeedback');
      feedback.className = `feedback ${correct ? 'ok' : 'no'}`;
      feedback.textContent = `${correct ? 'Correct' : 'Try the highlighted sound'}: ${item.word} ends with /${item.sound}/. Score ${pronCorrect} / ${pronAttempts}`;
      window.setTimeout(() => {
        pronIndex += 1;
        renderPronunciation();
      }, 1100);
    });
  });

  const irregularVerbs = [
    ['begin', 'began'], ['bring', 'brought'], ['come', 'came'], ['do', 'did'],
    ['drive', 'drove'], ['get up', 'got up'], ['go', 'went'], ['have', 'had'],
    ['hear', 'heard'], ['know', 'knew'], ['leave', 'left'], ['read', 'read'],
    ['say', 'said'], ['see', 'saw'], ['sit', 'sat'], ['speak', 'spoke'],
    ['take', 'took'], ['write', 'wrote'],
  ];
  let verbIndex = 6;
  let verbLocked = false;

  function renderVerb() {
    verbLocked = false;
    const [base, past] = irregularVerbs[verbIndex % irregularVerbs.length];
    document.getElementById('verbPrompt').textContent = `${base} → ?`;
    const distractors = shuffle(irregularVerbs.filter((item) => item[1] !== past).map((item) => item[1])).slice(0, 3);
    const options = shuffle([past].concat(distractors));
    const holder = document.getElementById('verbAnswers');
    holder.innerHTML = options.map((option) => `<button type="button" class="answer-btn" data-answer="${option}">${option}</button>`).join('');
    holder.querySelectorAll('button').forEach((button) => {
      button.addEventListener('click', () => {
        if (verbLocked) return;
        verbLocked = true;
        const correct = button.dataset.answer === past;
        button.classList.add(correct ? 'correct' : 'wrong');
        holder.querySelector(`[data-answer="${past}"]`).classList.add('correct');
        const feedback = document.getElementById('verbFeedback');
        feedback.className = `feedback ${correct ? 'ok' : 'no'}`;
        feedback.textContent = `${base} → ${past}`;
        speak(`${base}, ${past}`, 0.72);
        window.setTimeout(() => {
          verbIndex = (verbIndex + 1) % irregularVerbs.length;
          renderVerb();
        }, 1100);
      });
    });
  }

  const questionTasks = [
    { statement: 'She went to training.', answer: 'Yes, she went to training.', question: 'Did she go to training?' },
    { statement: 'He wrote the report.', answer: 'Yes, he wrote the report.', question: 'Did he write the report?' },
    { statement: 'They left at 1630.', answer: 'They left at 1630.', question: 'When did they leave?' },
    { statement: 'Captain Naran worked at the post.', answer: 'She worked at the post.', question: 'Where did Captain Naran work?' },
  ];
  let questionIndex = 0;

  function renderQuestionTask() {
    const task = questionTasks[questionIndex % questionTasks.length];
    document.getElementById('questionStatement').textContent = task.statement;
    document.getElementById('questionAnswer').textContent = `Answer: ${task.answer}`;
    document.getElementById('questionInput').value = '';
    const feedback = document.getElementById('questionFeedback');
    feedback.className = 'feedback';
    feedback.textContent = 'Use: Did + subject + base verb?';
  }

  document.getElementById('checkQuestion').addEventListener('click', () => {
    const task = questionTasks[questionIndex % questionTasks.length];
    const input = document.getElementById('questionInput');
    const correct = normalize(input.value) === normalize(task.question);
    const feedback = document.getElementById('questionFeedback');
    feedback.className = `feedback ${correct ? 'ok' : 'no'}`;
    feedback.textContent = correct ? 'Correct. Good question form.' : `Answer: ${task.question}`;
    if (correct) {
      window.setTimeout(() => {
        questionIndex = (questionIndex + 1) % questionTasks.length;
        renderQuestionTask();
      }, 1100);
    }
  });
  document.getElementById('questionInput').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') document.getElementById('checkQuestion').click();
  });

  const timeTasks = [
    { face: '0730', direction: 'Military time', question: 'What is the civilian time?', answer: '7:30 a.m.', options: ['7:30 a.m.', '7:30 p.m.', '3:70 a.m.', '5:30 a.m.'] },
    { face: '1500', direction: 'Military time', question: 'What is the civilian time?', answer: '3:00 p.m.', options: ['5:00 p.m.', '3:00 p.m.', '1:50 p.m.', '3:00 a.m.'] },
    { face: '10:30 p.m.', direction: 'Civilian time', question: 'What is the military time?', answer: '2230', options: ['1030', '2030', '2230', '2300'] },
    { face: '1200', direction: 'Military time', question: 'What time is this?', answer: 'Noon', options: ['Midnight', 'Noon', '2:00 p.m.', '10:00 a.m.'] },
    { face: '1630', direction: 'Military time', question: 'Say the time in words.', answer: 'sixteen thirty', options: ['six thirty', 'sixteen thirty', 'fourteen thirty', 'sixty thirty'] },
  ];
  let timeIndex = 0;
  let timeLocked = false;

  function renderTime() {
    timeLocked = false;
    const task = timeTasks[timeIndex % timeTasks.length];
    document.getElementById('timeFace').textContent = task.face;
    document.getElementById('timeDirection').textContent = task.direction;
    document.getElementById('timeQuestion').textContent = task.question;
    const holder = document.getElementById('timeAnswers');
    holder.innerHTML = task.options.map((option) => `<button type="button" class="answer-btn" data-answer="${option}">${option}</button>`).join('');
    const feedback = document.getElementById('timeFeedback');
    feedback.className = 'feedback';
    feedback.textContent = 'Choose one answer.';
    holder.querySelectorAll('button').forEach((button) => {
      button.addEventListener('click', () => {
        if (timeLocked) return;
        timeLocked = true;
        const correct = button.dataset.answer === task.answer;
        button.classList.add(correct ? 'correct' : 'wrong');
        holder.querySelector(`[data-answer="${task.answer}"]`).classList.add('correct');
        feedback.className = `feedback ${correct ? 'ok' : 'no'}`;
        feedback.textContent = correct ? 'Correct.' : `Correct answer: ${task.answer}`;
        speak(task.answer, 0.75);
        window.setTimeout(() => {
          timeIndex = (timeIndex + 1) % timeTasks.length;
          renderTime();
        }, 1200);
      });
    });
  }

  const readingText = 'Captain Naran joined the academy in 2018. She completed protection training in 2019 and began work at an S S P A post in 2020. Yesterday, she reported for duty at zero seven thirty. She checked her uniform and I D card. At twelve hundred, she took a short break. She left the post at sixteen thirty.';
  const readingItems = [
    { text: 'Captain Naran joined the academy in 2018.', answer: true },
    { text: 'She began work at an SSPA post in 2019.', answer: false },
    { text: 'She reported for duty at 0730.', answer: true },
    { text: 'She left the post at 1200.', answer: false },
  ];
  let readingAnswered = new Set();
  let readingCorrect = 0;

  function renderReadingQuestions() {
    const holder = document.getElementById('readingQuestions');
    holder.innerHTML = readingItems.map((item, index) => `
      <div class="tf-item" data-index="${index}">
        <span>${index + 1}. ${item.text}</span>
        <div class="tf-options"><button type="button" data-value="true">T</button><button type="button" data-value="false">F</button></div>
      </div>`).join('');
    holder.querySelectorAll('.tf-options button').forEach((button) => {
      button.addEventListener('click', () => {
        const itemNode = button.closest('.tf-item');
        const index = Number(itemNode.dataset.index);
        if (readingAnswered.has(index)) return;
        readingAnswered.add(index);
        const correct = String(readingItems[index].answer) === button.dataset.value;
        if (correct) readingCorrect += 1;
        button.classList.add(correct ? 'correct' : 'wrong');
        const correctButton = itemNode.querySelector(`[data-value="${readingItems[index].answer}"]`);
        correctButton.classList.add('correct');
        const feedback = document.getElementById('readingFeedback');
        feedback.className = `feedback ${correct ? 'ok' : 'no'}`;
        feedback.textContent = `Reading score: ${readingCorrect} / ${readingAnswered.size}`;
      });
    });
  }
  document.getElementById('readingListen').addEventListener('click', () => speak(readingText, 0.76));

  const quizItems = [
    { q: 'A person who works on an Army post is a...', options: ['sailor', 'soldier', 'airman', 'instructor'], answer: 'soldier', note: 'A soldier works in the Army.' },
    { q: 'What shows an officer\'s rank on a uniform?', options: ['insignia', 'break', 'base', 'clock'], answer: 'insignia', note: 'Insignia shows rank.' },
    { q: 'Choose the past form of go.', options: ['goed', 'gone', 'went', 'go'], answer: 'went', note: 'go → went' },
    { q: 'Choose the correct question.', options: ['Did she went to class?', 'Did she go to class?', 'Does she went to class?', 'She did go to class?'], answer: 'Did she go to class?', note: 'After did, use the base verb.' },
    { q: 'What is the final sound in watched?', options: ['/t/', '/d/', '/id/', '/s/'], answer: '/t/', note: 'watched ends with /t/.' },
    { q: '1500 is...', options: ['1:50 p.m.', '5:00 p.m.', '3:00 p.m.', '3:00 a.m.'], answer: '3:00 p.m.', note: '1500 = fifteen hundred hours = 3 p.m.' },
    { q: 'Complete: She ___ for duty at 0730.', options: ['reported', 'reporting', 'reports yesterday', 'report'], answer: 'reported', note: 'A completed past action uses reported.' },
    { q: 'Choose the past form of take.', options: ['taked', 'took', 'taken', 'takes'], answer: 'took', note: 'take → took' },
    { q: 'Choose the correct information question.', options: ['Where did he work?', 'Where he did work?', 'Where did he worked?', 'Where he worked did?'], answer: 'Where did he work?', note: 'Question word + did + subject + base verb.' },
    { q: 'How do we say 0730?', options: ['seven thirteen', 'zero seven thirty', 'seventy thirty', 'zero thirty seven'], answer: 'zero seven thirty', note: '0730 is zero seven thirty.' },
  ];
  let quizIndex = 0;
  let quizScore = 0;
  let quizLocked = false;

  function renderQuiz() {
    const shell = document.getElementById('finalQuiz');
    if (quizIndex >= quizItems.length) {
      const percent = Math.round((quizScore / quizItems.length) * 100);
      state.bestQuiz = Math.max(state.bestQuiz || 0, quizScore);
      if (!state.completed.includes('quiz')) state.completed.push('quiz');
      saveState();
      updateProgress();
      shell.innerHTML = `
        <div class="quiz-result">
          <div class="practice-label">Final score</div>
          <div class="quiz-score">${quizScore} / ${quizItems.length}</div>
          <p>${percent >= 80 ? 'Ready for the performance task.' : 'Review the lesson and try again.'}</p>
          <button type="button" class="btn btn-primary" id="retryQuiz"><i class="bi bi-arrow-clockwise me-1"></i> Try again</button>
        </div>`;
      document.getElementById('retryQuiz').addEventListener('click', () => {
        quizIndex = 0;
        quizScore = 0;
        shell.innerHTML = `
          <div class="quiz-top"><span id="quizCounter"></span><span id="quizRunningScore"></span></div>
          <div class="quiz-question" id="quizQuestion"></div><div class="quiz-options" id="quizOptions"></div>
          <div class="feedback" id="quizFeedback" aria-live="polite"></div>
          <div class="d-flex justify-content-end mt-3"><button type="button" class="btn btn-primary" id="quizNext" disabled>Next question</button></div>`;
        document.getElementById('quizNext').addEventListener('click', nextQuizQuestion);
        renderQuiz();
      });
      return;
    }

    quizLocked = false;
    const item = quizItems[quizIndex];
    document.getElementById('quizCounter').textContent = `Question ${quizIndex + 1} of ${quizItems.length}`;
    document.getElementById('quizRunningScore').textContent = `Score ${quizScore}`;
    document.getElementById('quizQuestion').textContent = item.q;
    const holder = document.getElementById('quizOptions');
    holder.innerHTML = item.options.map((option) => `<button type="button" class="quiz-option" data-answer="${option}">${option}</button>`).join('');
    const feedback = document.getElementById('quizFeedback');
    feedback.className = 'feedback';
    feedback.textContent = 'Choose the best answer.';
    const nextButton = document.getElementById('quizNext');
    nextButton.disabled = true;
    nextButton.textContent = quizIndex === quizItems.length - 1 ? 'Show result' : 'Next question';
    holder.querySelectorAll('button').forEach((button) => {
      button.addEventListener('click', () => {
        if (quizLocked) return;
        quizLocked = true;
        const correct = button.dataset.answer === item.answer;
        if (correct) quizScore += 1;
        button.classList.add(correct ? 'correct' : 'wrong');
        holder.querySelector(`[data-answer="${CSS.escape(item.answer)}"]`).classList.add('correct');
        feedback.className = `feedback ${correct ? 'ok' : 'no'}`;
        feedback.textContent = `${correct ? 'Correct.' : 'Not quite.'} ${item.note}`;
        document.getElementById('quizRunningScore').textContent = `Score ${quizScore}`;
        nextButton.disabled = false;
      });
    });
  }

  function nextQuizQuestion() {
    if (!quizLocked) return;
    quizIndex += 1;
    renderQuiz();
  }
  document.getElementById('quizNext').addEventListener('click', nextQuizQuestion);

  function loadHomework() {
    const rows = document.querySelectorAll('.timeline-row');
    rows.forEach((row, index) => {
      const saved = state.homework[index] || { year: '', event: '' };
      row.querySelector('.homework-year').value = saved.year;
      row.querySelector('.homework-event').value = saved.event;
    });
  }

  document.getElementById('saveHomework').addEventListener('click', () => {
    state.homework = Array.from(document.querySelectorAll('.timeline-row')).map((row) => ({
      year: row.querySelector('.homework-year').value.trim(),
      event: row.querySelector('.homework-event').value.trim(),
    }));
    saveState();
    document.getElementById('homeworkStatus').textContent = 'Homework saved on this device.';
  });

  document.getElementById('clearHomework').addEventListener('click', () => {
    state.homework = [];
    saveState();
    loadHomework();
    document.getElementById('homeworkStatus').textContent = 'Homework cleared.';
  });

  renderVocabulary();
  renderPronunciation();
  renderVerb();
  renderQuestionTask();
  renderTime();
  renderReadingQuestions();
  renderQuiz();
  loadHomework();
  updateProgress();
}());
