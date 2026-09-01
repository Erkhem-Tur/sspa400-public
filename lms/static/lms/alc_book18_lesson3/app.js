(function () {
  "use strict";

  const sections = [
    { name: "Orientation", start: 0, end: 1 },
    { name: "Employment & job search", start: 2, end: 4 },
    { name: "Negative questions", start: 5, end: 8 },
    { name: "Policies & logical impossibility", start: 9, end: 13 },
    { name: "Point of view & communication", start: 14, end: 22 },
    { name: "Word building & writing", start: 23, end: 27 }
  ];

  const titles = [
    "Lesson overview: Employment",
    "Preview: vocabulary, grammar, and language functions",
    "Conducting a successful job search",
    "Job-search vocabulary practice",
    "New employee training",
    "Negative questions: form and purpose",
    "Negative-question transformations",
    "Negative questions: agreement, surprise, and information",
    "Partner practice with negative questions",
    "Company benefits and policies",
    "Benefits and policies: vocabulary practice",
    "Logical impossibility with can’t be / couldn’t be",
    "Logical-impossibility practice",
    "Reading a diagram: soccer tournament",
    "Keep it professional",
    "Professional communication: vocabulary practice",
    "What’s your point of view?",
    "Point-of-view comprehension and vocabulary",
    "Vocabulary review",
    "Word forms in context",
    "Word-form practice",
    "Agreeing and disagreeing",
    "Tag questions and intonation",
    "Suffix -ness: adjectives to nouns",
    "Suffixes -ness and -ment",
    "Suffix -ment: practice",
    "Organizing a text with a visual map",
    "Writing a summary"
  ];

  const pages = titles.map((title, index) => ({
    index,
    title,
    bookPage: 61 + index,
    src: `assets/page-${String(index + 1).padStart(2, "0")}.jpg`,
    section: sections.find(section => index >= section.start && index <= section.end).name
  }));

  const storageKey = "alc-book18-lesson3-progress-v1";
  const answersKey = "alc-book18-lesson3-answers-v1";
  const ui = {
    toc: document.getElementById("toc"),
    pageImage: document.getElementById("pageImage"),
    pageFrame: document.getElementById("pageFrame"),
    pageStage: document.getElementById("pageStage"),
    loader: document.getElementById("loader"),
    pageTitle: document.getElementById("pageTitle"),
    sectionLabel: document.getElementById("sectionLabel"),
    pagePosition: document.getElementById("pagePosition"),
    pageSelect: document.getElementById("pageSelect"),
    zoomSelect: document.getElementById("zoomSelect"),
    previousButton: document.getElementById("previousButton"),
    nextButton: document.getElementById("nextButton"),
    progressLabel: document.getElementById("progressLabel"),
    progressPercent: document.getElementById("progressPercent"),
    progressBar: document.getElementById("progressBar"),
    completionCard: document.getElementById("completionCard"),
    announcement: document.getElementById("announcement"),
    sidebar: document.getElementById("sidebar"),
    menuButton: document.getElementById("menuButton"),
    sidebarClose: document.getElementById("sidebarClose"),
    scrim: document.getElementById("scrim"),
    fullscreenButton: document.getElementById("fullscreenButton"),
    practiceJump: document.getElementById("practiceJump"),
    translanguagingToggle: document.getElementById("translanguagingToggle"),
    translanguagingPanel: document.getElementById("translanguagingPanel"),
    translanguagingMn: document.getElementById("translanguagingMn"),
    translanguagingKeywords: document.getElementById("translanguagingKeywords"),
    translanguagingFrame: document.getElementById("translanguagingFrame"),
    workbook: document.getElementById("workbook"),
    workbookTitle: document.getElementById("workbookTitle"),
    workbookIntro: document.getElementById("workbookIntro"),
    activityForm: document.getElementById("activityForm"),
    answerCount: document.getElementById("answerCount"),
    answerProgressBar: document.getElementById("answerProgressBar"),
    saveIndicator: document.getElementById("saveIndicator"),
    clearAnswers: document.getElementById("clearAnswers"),
    checkAnswers: document.getElementById("checkAnswers"),
    revealAnswers: document.getElementById("revealAnswers"),
    gradeSummary: document.getElementById("gradeSummary"),
    gradeScore: document.getElementById("gradeScore"),
    gradeTitle: document.getElementById("gradeTitle"),
    gradeMessage: document.getElementById("gradeMessage"),
    lmsStatus: document.getElementById("lmsStatus"),
    statusDot: document.getElementById("statusDot")
  };

  let state = { current: 0, viewed: [0], completed: false, zoom: "fit", translanguaging: true, practice: {}, grades: {}, attempts: {}, itemAttempts: {} };
  let answers = safeParse(localStorage.getItem(answersKey)) || {};
  let scormConnected = false;
  let answerSaveTimer = null;
  const objectiveTotal = window.LESSON_ACTIVITIES.reduce((lessonTotal, activity) =>
    lessonTotal + activity.groups.reduce((groupTotal, activityGroup) =>
      groupTotal + (Array.isArray(activityGroup.answers)
        ? activityGroup.answers.filter(expected => expected !== null && expected !== undefined).length
        : 0), 0), 0);

  function safeParse(value) {
    try { return JSON.parse(value); } catch (_) { return null; }
  }

  function normalizeState(candidate) {
    if (!candidate || typeof candidate !== "object") return;
    const current = Number(candidate.current);
    if (Number.isInteger(current) && current >= 0 && current < pages.length) state.current = current;
    if (Array.isArray(candidate.viewed)) {
      state.viewed = [...new Set(candidate.viewed.map(Number).filter(value => Number.isInteger(value) && value >= 0 && value < pages.length))];
    }
    if (!state.viewed.includes(state.current)) state.viewed.push(state.current);
    state.completed = Boolean(candidate.completed) || state.viewed.length === pages.length;
    if (["fit", "100", "125", "150", "200"].includes(candidate.zoom)) state.zoom = candidate.zoom;
    if (typeof candidate.translanguaging === "boolean") state.translanguaging = candidate.translanguaging;
    if (candidate.practice && typeof candidate.practice === "object") state.practice = candidate.practice;
    if (candidate.grades && typeof candidate.grades === "object") state.grades = candidate.grades;
    if (candidate.attempts && typeof candidate.attempts === "object") state.attempts = candidate.attempts;
    if (candidate.itemAttempts && typeof candidate.itemAttempts === "object") state.itemAttempts = candidate.itemAttempts;
  }

  function restoreState() {
    normalizeState(safeParse(localStorage.getItem(storageKey)));
    scormConnected = window.ScormBridge.initialize();
    if (scormConnected) {
      normalizeState(safeParse(window.ScormBridge.get("cmi.suspend_data")));
      const location = Number(window.ScormBridge.get("cmi.core.lesson_location"));
      if (Number.isInteger(location) && location >= 1 && location <= pages.length) state.current = location - 1;
      const status = window.ScormBridge.get("cmi.core.lesson_status");
      if (status === "completed" || status === "passed") state.completed = true;
      ui.lmsStatus.textContent = "Connected to LMS · progress is tracked";
      ui.statusDot.classList.add("connected");
    }
    if (!state.viewed.includes(state.current)) state.viewed.push(state.current);
  }

  function persistState() {
    state.viewed.sort((a, b) => a - b);
    if (state.viewed.length === pages.length) state.completed = true;
    const payload = JSON.stringify(state);
    try { localStorage.setItem(storageKey, payload); } catch (_) { /* private mode */ }
    if (scormConnected) {
      const correct = Object.values(state.grades).reduce((sum, grade) => sum + (Number(grade.correct) || 0), 0);
      const percent = objectiveTotal ? Math.round((correct / objectiveTotal) * 100) : 0;
      window.ScormBridge.set("cmi.core.lesson_location", state.current + 1);
      const scormPayload = JSON.stringify({
        current: state.current,
        viewed: state.viewed,
        completed: state.completed,
        zoom: state.zoom,
        translanguaging: state.translanguaging,
        practice: state.practice,
        grades: state.grades,
        attempts: state.attempts
      });
      window.ScormBridge.set("cmi.suspend_data", scormPayload);
      window.ScormBridge.set("cmi.core.score.min", "0");
      window.ScormBridge.set("cmi.core.score.max", "100");
      window.ScormBridge.set("cmi.core.score.raw", percent);
      window.ScormBridge.set("cmi.core.lesson_status", state.completed ? "completed" : "incomplete");
      window.ScormBridge.commit();
    }
  }

  function buildContents() {
    ui.toc.innerHTML = "";
    sections.forEach(section => {
      const wrapper = document.createElement("section");
      wrapper.className = "toc-group";
      const heading = document.createElement("h3");
      heading.textContent = section.name;
      const list = document.createElement("div");
      list.className = "toc-list";

      pages.slice(section.start, section.end + 1).forEach(page => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "toc-button";
        button.dataset.page = String(page.index);
        button.innerHTML = `<span class="toc-number">${page.bookPage}</span><span class="toc-title">${page.title}</span><span class="toc-check" aria-hidden="true"></span>`;
        button.setAttribute("aria-label", `Book page ${page.bookPage}: ${page.title}`);
        button.addEventListener("click", () => {
          showPage(page.index);
          closeSidebar();
        });
        list.appendChild(button);
      });
      wrapper.append(heading, list);
      ui.toc.appendChild(wrapper);
    });

    pages.forEach(page => {
      const option = document.createElement("option");
      option.value = String(page.index);
      option.textContent = `${page.bookPage} · ${page.title}`;
      ui.pageSelect.appendChild(option);
    });
  }

  function updateContents() {
    document.querySelectorAll(".toc-button").forEach(button => {
      const index = Number(button.dataset.page);
      if (index === state.current) button.setAttribute("aria-current", "page");
      else button.removeAttribute("aria-current");
      button.querySelector(".toc-check").textContent = state.viewed.includes(index) ? "✓" : "";
    });
  }

  function updateProgress() {
    const viewed = state.viewed.length;
    const percent = Math.round((viewed / pages.length) * 100);
    ui.progressLabel.textContent = `${viewed} of ${pages.length} pages viewed`;
    ui.progressPercent.textContent = `${percent}%`;
    ui.progressBar.style.width = `${percent}%`;
    ui.completionCard.hidden = !state.completed;
  }

  function preload(index) {
    [index - 1, index + 1].filter(value => value >= 0 && value < pages.length).forEach(value => {
      const image = new Image();
      image.src = pages[value].src;
    });
  }

  function answerKey(pageIndex, groupIndex, itemIndex) {
    return `p${pageIndex + 1}-g${groupIndex + 1}-q${itemIndex + 1}`;
  }

  function saveAnswersLocally() {
    try { localStorage.setItem(answersKey, JSON.stringify(answers)); } catch (_) { /* private mode */ }
  }

  function setSaveIndicator(saving) {
    ui.saveIndicator.classList.toggle("saving", saving);
    ui.saveIndicator.innerHTML = saving
      ? '<span aria-hidden="true">…</span> Saving answers…'
      : '<span aria-hidden="true">✓</span> Answers saved automatically';
  }

  function updateAnswerProgress(pageIndex) {
    const fields = [...ui.activityForm.querySelectorAll("[data-answer-key]")];
    const answered = fields.filter(field => field.value.trim().length > 0).length;
    const total = fields.length;
    state.practice[pageIndex] = { answered, total };
    ui.answerCount.textContent = `${answered}/${total}`;
    ui.answerProgressBar.style.width = total ? `${Math.round((answered / total) * 100)}%` : "0%";
  }

  function queueAnswerSave(pageIndex) {
    saveAnswersLocally();
    updateAnswerProgress(pageIndex);
    setSaveIndicator(true);
    window.clearTimeout(answerSaveTimer);
    answerSaveTimer = window.setTimeout(() => {
      persistState();
      setSaveIndicator(false);
    }, 450);
  }

  function normalizeAnswer(value) {
    return window.AnswerGrader.normalize(value);
  }

  function matchesExpected(value, expected) {
    return window.AnswerGrader.matches(value, expected);
  }

  function expectedLabel(expected) {
    return window.AnswerGrader.label(expected);
  }

  function withMongolian(english, mongolian) {
    return state.translanguaging ? `${english} · Монгол: ${mongolian}` : english;
  }

  function renderTranslanguaging(pageIndex) {
    const support = window.TRANSLANGUAGING_SUPPORT[pageIndex];
    ui.translanguagingPanel.hidden = !state.translanguaging;
    ui.translanguagingToggle.setAttribute("aria-pressed", String(state.translanguaging));
    ui.translanguagingToggle.textContent = `EN ↔ MN Support: ${state.translanguaging ? "On" : "Off"}`;
    if (!support) return;
    ui.translanguagingMn.textContent = support.mn;
    ui.translanguagingKeywords.textContent = support.keywords.join(" · ");
    ui.translanguagingFrame.textContent = support.frame;
    ui.workbookIntro.textContent = state.translanguaging
      ? "Type one answer, then Check · Шалгах. Буруу бол English + Монгол correction guide ашиглаад дахин оролдоорой."
      : "Type one answer and select Check for instant feedback. If it is wrong, use the correction guide and try again.";
    ui.activityForm.querySelectorAll(".item-check").forEach(button => {
      const reviewOnly = button.dataset.reviewOnly === "true";
      button.textContent = state.translanguaging
        ? (reviewOnly ? "Submit · Илгээх" : "Check · Шалгах")
        : (reviewOnly ? "Submit" : "Check");
    });
    ui.activityForm.querySelectorAll(".item-reveal").forEach(button => {
      button.textContent = state.translanguaging ? "Show answer · Хариу харах" : "Show answer";
    });
    const reviewOnlyPage = ui.checkAnswers.dataset.reviewOnly === "true";
    ui.checkAnswers.textContent = state.translanguaging
      ? (reviewOnlyPage ? "Submit page · Багшид илгээх" : "Check page · Хуудсаар шалгах")
      : (reviewOnlyPage ? "Submit for teacher review" : "Check answers");
  }

  function toggleTranslanguaging() {
    state.translanguaging = !state.translanguaging;
    renderTranslanguaging(state.current);
    persistState();
    ui.announcement.textContent = state.translanguaging
      ? "English and Mongolian translanguaging support is on."
      : "English and Mongolian translanguaging support is off.";
  }

  function expectedWordCount(expected) {
    const label = expectedLabel(expected).split(" / ")[0].trim();
    return label ? label.split(/\s+/).length : 0;
  }

  function correctionGuide(activityGroup, expected, attempt) {
    const title = activityGroup.title.toLowerCase();
    const hint = activityGroup.hint.toLowerCase();
    const label = expectedLabel(expected).split(" / ")[0];
    const firstLetter = normalizeAnswer(label).charAt(0).toUpperCase();
    const wordCount = expectedWordCount(expected);
    const extraClue = attempt >= 2 && firstLetter
      ? ` It starts with “${firstLetter}”${wordCount > 1 ? ` and has ${wordCount} words` : ""}.`
      : "";
    const extraClueMn = attempt >= 2 && firstLetter
      ? ` Эхний үсэг нь “${firstLetter}”${wordCount > 1 ? `, нийт ${wordCount} үгтэй` : ""}.`
      : "";

    if (expected && typeof expected === "object" && Array.isArray(expected.all)) {
      return withMongolian(
        `This item needs ${expected.all.length} related forms. Check the part of speech for every blank and include all forms.${extraClue}`,
        `Энэ item-д холбоотой ${expected.all.length} form хэрэгтэй. Blank бүрийн part of speech-ийг шалгаад бүх form-ыг оруул.${extraClueMn}`
      );
    }
    if (hint.includes("t or f")) {
      return withMongolian(
        `Re-read the exact statement on the book page. Start with T if every detail is true, or F and then correct the false detail.${extraClue}`,
        `Өгүүлбэрийн бүх мэдээллийг дахин шалга. Бүгд зөв бол T; нэг хэсэг буруу бол F гэж эхлээд буруу detail-ийг зас.${extraClueMn}`
      );
    }
    if (hint.includes("matching letter")) {
      return withMongolian(
        `Match the whole meaning, not just one familiar word. Compare the item with every option, then enter one letter.${extraClue}`,
        `Зөвхөн танил нэг үгээр биш, бүтэн утгаар нь match хий. Item-ийг бүх option-той харьцуулаад нэг үсэг бич.${extraClueMn}`
      );
    }
    if (title.includes("exercise d") && hint.includes("a, s/a, or i")) {
      return withMongolian(
        "Check the speaker’s purpose: A = agreement, S/A = surprise or annoyance, and I = asking for information.",
        "Speaker-ийн зорилгыг шалга: A = санал нийлэх, S/A = гайхах эсвэл дургүйцэх, I = мэдээлэл асуух."
      );
    }
    if (label.endsWith("?")) {
      return withMongolian(
        `Use negative auxiliary + subject + main verb, keep the original tense, and finish with a question mark.${extraClue}`,
        `Negative auxiliary + subject + main verb бүтцийг хэрэглэж, эх tense-ийг хадгалаад question mark-аар төгсгө.${extraClueMn}`
      );
    }
    if (hint.includes("a, b, or c")) {
      return withMongolian(
        `Return to the sentence and test all three choices for meaning and grammar. Enter only a, b, or c.${extraClue}`,
        `Өгүүлбэрт буцаж очоод гурван choice-ийг утга ба grammar хоёроор шалга. Зөвхөн a, b, эсвэл c бич.${extraClueMn}`
      );
    }
    if (hint.includes("word from the box") || hint.includes("words from the box") || hint.includes("replacement word")) {
      return withMongolian(
        `Use the word box and check both meaning and grammar. Make sure the word form fits the sentence exactly.${extraClue}`,
        `Word box-оо ашиглаад утга болон grammar-ийг хамтад нь шалга. Word form өгүүлбэрт яг таарч байгаа эсэхийг нягтал.${extraClueMn}`
      );
    }
    if (hint.includes("-ness")) {
      return withMongolian(
        `The blank needs the noun form. Check spelling when adding -ness, especially final y → i.${extraClue}`,
        `Blank-д noun form хэрэгтэй. -ness залгах spelling, ялангуяа төгсгөлийн y → i өөрчлөлтийг шалга.${extraClueMn}`
      );
    }
    if (hint.includes("-ment") || hint.includes("verb or noun")) {
      return withMongolian(
        `Decide whether the blank needs a verb or a noun. Use -ment only when the sentence needs the noun form.${extraClue}`,
        `Blank-д verb эсвэл noun аль нь хэрэгтэйг эхлээд шийд. Sentence noun form шаардаж байвал -ment хэрэглэ.${extraClueMn}`
      );
    }
    if (hint.includes("word form") || hint.includes("related word")) {
      return withMongolian(
        `Use the sentence position to identify the part of speech, then check singular/plural and the correct suffix.${extraClue}`,
        `Sentence position-оос part of speech-ийг тогтоогоод singular/plural болон зөв suffix-ийг шалга.${extraClueMn}`
      );
    }
    return withMongolian(
      `Check the source sentence again for meaning, spelling, and the exact word form.${extraClue}`,
      `Source sentence-ээ дахин уншаад утга, spelling болон яг зөв word form-оо шалга.${extraClueMn}`
    );
  }

  function setFieldResult(wrapper, status, message) {
    wrapper.classList.remove("correct", "incorrect", "review");
    if (status) wrapper.classList.add(status);
    const feedback = wrapper.querySelector(".answer-feedback");
    feedback.textContent = message;
    feedback.dataset.status = status || "";
  }

  function showSingleAnswer(pageIndex, groupIndex, itemIndex) {
    const activityGroup = window.LESSON_ACTIVITIES[pageIndex].groups[groupIndex];
    const expected = Array.isArray(activityGroup.answers) ? activityGroup.answers[itemIndex] : undefined;
    if (expected === null || expected === undefined) return;
    const field = document.getElementById(answerKey(pageIndex, groupIndex, itemIndex));
    const wrapper = field.closest(".answer-field");
    setFieldResult(
      wrapper,
      matchesExpected(field.value, expected) ? "correct" : "incorrect",
      withMongolian(`Correct answer: ${expectedLabel(expected)}`, `Зөв хариу: ${expectedLabel(expected)}`)
    );
    wrapper.querySelector(".item-reveal").hidden = true;
    field.focus();
  }

  function checkSingleAnswer(pageIndex, groupIndex, itemIndex) {
    const activityGroup = window.LESSON_ACTIVITIES[pageIndex].groups[groupIndex];
    const displayNumber = (activityGroup.start || 1) + itemIndex;
    const expected = Array.isArray(activityGroup.answers) ? activityGroup.answers[itemIndex] : undefined;
    const key = answerKey(pageIndex, groupIndex, itemIndex);
    const field = document.getElementById(key);
    const wrapper = field.closest(".answer-field");
    const revealButton = wrapper.querySelector(".item-reveal");
    const value = field.value.trim();

    if (expected === null || expected === undefined) {
      setFieldResult(wrapper, "review", value
        ? withMongolian("Saved for teacher review.", "Багш шалгахаар хадгалагдлаа.")
        : withMongolian("Write a response before submitting it.", "Илгээхийн өмнө хариултаа бичээрэй."));
      revealButton.hidden = true;
      ui.announcement.textContent = value ? "Response saved for teacher review." : "A response is required.";
      return;
    }

    if (!value) {
      setFieldResult(wrapper, "incorrect", withMongolian(
        "Write an answer first, then select Check.",
        "Эхлээд хариултаа бичээд Check товчийг дар."
      ));
      revealButton.hidden = true;
      field.focus();
      ui.announcement.textContent = `Item ${displayNumber} needs an answer.`;
      return;
    }

    state.itemAttempts[key] = (Number(state.itemAttempts[key]) || 0) + 1;
    const attempt = state.itemAttempts[key];
    if (matchesExpected(value, expected)) {
      setFieldResult(wrapper, "correct", attempt === 1
        ? withMongolian("Correct — well done!", "Зөв — маш сайн!")
        : withMongolian("Correct — good correction!", "Зөв — алдаагаа сайн заслаа!"));
      revealButton.hidden = true;
      ui.announcement.textContent = `Item ${displayNumber} is correct.`;
    } else {
      setFieldResult(wrapper, "incorrect", `${withMongolian("Not yet.", "Одоохондоо буруу байна.")} ${correctionGuide(activityGroup, expected, attempt)}`);
      revealButton.hidden = attempt < 2;
      ui.announcement.textContent = `Item ${displayNumber} is not correct yet. Use the guidance and try again.`;
    }
    delete state.grades[pageIndex];
    ui.gradeSummary.hidden = false;
    ui.gradeSummary.classList.remove("success");
    ui.gradeSummary.classList.toggle("needs-work", !matchesExpected(value, expected));
    ui.gradeScore.textContent = matchesExpected(value, expected) ? "✓" : "Try";
    ui.gradeTitle.textContent = matchesExpected(value, expected)
      ? withMongolian("This answer is correct", "Энэ хариулт зөв байна")
      : withMongolian("Correct this answer and check again", "Хариултаа засаад дахин шалга");
    ui.gradeMessage.textContent = matchesExpected(value, expected)
      ? withMongolian("Continue to the next item.", "Дараагийн item рүү үргэлжлүүл.")
      : attempt >= 2
        ? withMongolian("A stronger clue is shown. You may also reveal only this answer.", "Нэмэлт clue гарлаа. Зөвхөн энэ item-ийн answer-ийг харж болно.")
        : withMongolian("Use the hint directly below the field.", "Field-ийн доорх clue-г ашигла.");
    saveAnswersLocally();
    persistState();
  }

  function clearGradeDisplay() {
    ui.activityForm.querySelectorAll(".answer-field").forEach(wrapper => {
      wrapper.classList.remove("correct", "incorrect", "review");
      const feedback = wrapper.querySelector(".answer-feedback");
      if (feedback) {
        feedback.textContent = "";
        feedback.dataset.status = "";
      }
      const itemReveal = wrapper.querySelector(".item-reveal");
      if (itemReveal) itemReveal.hidden = true;
    });
    ui.gradeSummary.hidden = true;
    ui.gradeSummary.classList.remove("success", "needs-work");
    ui.revealAnswers.hidden = true;
  }

  function gradePage(pageIndex, incrementAttempt = true) {
    const activity = window.LESSON_ACTIVITIES[pageIndex];
    if (incrementAttempt) state.attempts[pageIndex] = (Number(state.attempts[pageIndex]) || 0) + 1;
    const attempts = Number(state.attempts[pageIndex]) || 0;
    let correct = 0;
    let total = 0;
    let review = 0;
    let answeredForReview = 0;

    activity.groups.forEach((activityGroup, groupIndex) => {
      for (let itemIndex = 0; itemIndex < activityGroup.count; itemIndex += 1) {
        const key = answerKey(pageIndex, groupIndex, itemIndex);
        const field = document.getElementById(key);
        const wrapper = field.closest(".answer-field");
        const feedback = wrapper.querySelector(".answer-feedback");
        const expected = Array.isArray(activityGroup.answers) ? activityGroup.answers[itemIndex] : undefined;
        wrapper.classList.remove("correct", "incorrect", "review");

        if (expected === null || expected === undefined) {
          review += 1;
          if (field.value.trim()) answeredForReview += 1;
          setFieldResult(wrapper, "review", field.value.trim()
            ? withMongolian("Saved for teacher review", "Багш шалгахаар хадгалагдлаа")
            : withMongolian("Teacher review item", "Багш шалгах item"));
          continue;
        }

        total += 1;
        if (matchesExpected(field.value, expected)) {
          correct += 1;
          setFieldResult(wrapper, "correct", withMongolian("Correct — well done!", "Зөв — маш сайн!"));
        } else {
          setFieldResult(wrapper, "incorrect", field.value.trim()
            ? `${withMongolian("Not yet.", "Одоохондоо буруу байна.")} ${correctionGuide(activityGroup, expected, attempts || 1)}`
            : withMongolian("Answer required", "Хариулт бичих шаардлагатай"));
          const revealButton = wrapper.querySelector(".item-reveal");
          if (revealButton) revealButton.hidden = attempts < 2;
        }
      }
    });

    state.grades[pageIndex] = { correct, total, review, answeredForReview, attempts };

    ui.gradeSummary.hidden = false;
    ui.gradeSummary.classList.toggle("success", total > 0 && correct === total);
    ui.gradeSummary.classList.toggle("needs-work", total > 0 && correct < total);
    if (total > 0) {
      const percent = Math.round((correct / total) * 100);
      ui.gradeScore.textContent = `${percent}%`;
      ui.gradeTitle.textContent = correct === total ? "Excellent — all auto-graded answers are correct" : `${correct} of ${total} correct`;
      ui.gradeMessage.textContent = review
        ? `${review} additional response${review === 1 ? " requires" : "s require"} teacher review. Attempt ${attempts}.`
        : `Attempt ${attempts}. Correct the highlighted fields and check again.`;
    } else {
      ui.gradeScore.textContent = "Review";
      ui.gradeTitle.textContent = "Submitted for teacher review";
      ui.gradeMessage.textContent = `${answeredForReview} of ${review} response${review === 1 ? "" : "s"} completed.`;
    }
    ui.revealAnswers.hidden = !(total > 0 && attempts >= 2);
    if (incrementAttempt) persistState();
    return { correct, total, review };
  }

  function revealCurrentPageAnswers() {
    const activity = window.LESSON_ACTIVITIES[state.current];
    activity.groups.forEach((activityGroup, groupIndex) => {
      if (!Array.isArray(activityGroup.answers)) return;
      activityGroup.answers.forEach((expected, itemIndex) => {
        if (expected === null || expected === undefined) return;
        const field = document.getElementById(answerKey(state.current, groupIndex, itemIndex));
        const wrapper = field.closest(".answer-field");
        if (!matchesExpected(field.value, expected)) {
          setFieldResult(wrapper, "incorrect", withMongolian(
            `Correct answer: ${expectedLabel(expected)}`,
            `Зөв хариу: ${expectedLabel(expected)}`
          ));
          wrapper.querySelector(".item-reveal").hidden = true;
        }
      });
    });
    ui.announcement.textContent = `Correct answers are now shown for book page ${pages[state.current].bookPage}.`;
  }

  function createAnswerField(pageIndex, groupIndex, itemIndex, activityGroup) {
    const key = answerKey(pageIndex, groupIndex, itemIndex);
    const wrapper = document.createElement("div");
    wrapper.className = "answer-field";
    const label = document.createElement("label");
    label.htmlFor = key;
    const displayNumber = (activityGroup.start || 1) + itemIndex;
    label.innerHTML = `<span class="answer-number">${displayNumber}</span><span>${activityGroup.count === 1 ? "Response" : `Item ${displayNumber}`}</span>`;

    const isLong = activityGroup.type === "long" || activityGroup.type === "essay";
    const field = document.createElement(isLong ? "textarea" : "input");
    field.id = key;
    field.name = key;
    field.dataset.answerKey = key;
    field.dataset.page = String(pageIndex);
    field.value = typeof answers[key] === "string" ? answers[key] : "";
    field.placeholder = activityGroup.type === "essay" ? "Write your summary here…" : "Type your answer…";
    if (activityGroup.type === "essay") field.classList.add("essay");
    if (field.value.trim()) wrapper.classList.add("filled");
    field.addEventListener("input", event => {
      const value = event.target.value;
      if (value.trim()) answers[key] = value;
      else delete answers[key];
      wrapper.classList.toggle("filled", Boolean(value.trim()));
      delete state.grades[pageIndex];
      wrapper.classList.remove("correct", "incorrect", "review");
      feedback.textContent = "";
      feedback.dataset.status = "";
      itemReveal.hidden = true;
      ui.gradeSummary.hidden = true;
      ui.revealAnswers.hidden = true;
      queueAnswerSave(pageIndex);
    });

    const feedback = document.createElement("span");
    feedback.className = "answer-feedback";
    feedback.setAttribute("aria-live", "polite");
    const entry = document.createElement("div");
    entry.className = "answer-entry";
    const itemCheck = document.createElement("button");
    itemCheck.type = "button";
    itemCheck.className = "item-check";
    const expected = Array.isArray(activityGroup.answers) ? activityGroup.answers[itemIndex] : undefined;
    const reviewOnly = expected === null || expected === undefined;
    itemCheck.dataset.reviewOnly = String(reviewOnly);
    itemCheck.textContent = reviewOnly
      ? (state.translanguaging ? "Submit · Илгээх" : "Submit")
      : (state.translanguaging ? "Check · Шалгах" : "Check");
    itemCheck.setAttribute("aria-label", `${itemCheck.textContent} item ${displayNumber}`);
    itemCheck.addEventListener("click", () => checkSingleAnswer(pageIndex, groupIndex, itemIndex));
    const itemReveal = document.createElement("button");
    itemReveal.type = "button";
    itemReveal.className = "item-reveal";
    itemReveal.textContent = state.translanguaging ? "Show answer · Хариу харах" : "Show answer";
    itemReveal.hidden = true;
    itemReveal.setAttribute("aria-label", `Show the correct answer for item ${displayNumber}`);
    itemReveal.addEventListener("click", () => showSingleAnswer(pageIndex, groupIndex, itemIndex));
    if (!isLong) {
      field.addEventListener("keydown", event => {
        if (event.key === "Enter") {
          event.preventDefault();
          checkSingleAnswer(pageIndex, groupIndex, itemIndex);
        }
      });
    }
    entry.append(field, itemCheck, itemReveal);
    wrapper.append(label, entry, feedback);
    return wrapper;
  }

  function renderWorkbook(pageIndex) {
    const page = pages[pageIndex];
    const activity = window.LESSON_ACTIVITIES[pageIndex];
    ui.workbookTitle.textContent = `Book page ${page.bookPage} practice`;
    ui.workbookIntro.textContent = state.translanguaging
      ? "Type one answer, then Check · Шалгах. Буруу бол English + Монгол correction guide ашиглаад дахин оролдоорой."
      : "Type one answer and select Check for instant feedback. If it is wrong, use the correction guide and try again.";
    ui.activityForm.innerHTML = "";
    clearGradeDisplay();

    if (activity.note) {
      const note = document.createElement("p");
      note.className = "activity-note";
      note.textContent = activity.note;
      ui.activityForm.appendChild(note);
    }

    activity.groups.forEach((activityGroup, groupIndex) => {
      const fieldset = document.createElement("fieldset");
      fieldset.className = "activity-group";
      const legend = document.createElement("legend");
      legend.textContent = activityGroup.title;
      fieldset.appendChild(legend);

      if (activityGroup.hint) {
        const hint = document.createElement("p");
        hint.className = "activity-hint";
        hint.textContent = activityGroup.hint;
        fieldset.appendChild(hint);
      }

      const grid = document.createElement("div");
      grid.className = `answer-grid ${activityGroup.type === "long" ? "long-grid" : ""} ${activityGroup.type === "essay" ? "essay-grid" : ""}`;
      for (let itemIndex = 0; itemIndex < activityGroup.count; itemIndex += 1) {
        grid.appendChild(createAnswerField(pageIndex, groupIndex, itemIndex, activityGroup));
      }
      fieldset.appendChild(grid);
      ui.activityForm.appendChild(fieldset);
    });

    updateAnswerProgress(pageIndex);
    setSaveIndicator(false);
    const gradedTotal = activity.groups.reduce((sum, activityGroup) =>
      sum + (Array.isArray(activityGroup.answers)
        ? activityGroup.answers.filter(expected => expected !== null && expected !== undefined).length
        : 0), 0);
    ui.checkAnswers.dataset.reviewOnly = String(!gradedTotal);
    ui.checkAnswers.textContent = state.translanguaging
      ? (gradedTotal ? "Check page · Хуудсаар шалгах" : "Submit page · Багшид илгээх")
      : (gradedTotal ? "Check answers" : "Submit for teacher review");
    if (state.grades[pageIndex]) gradePage(pageIndex, false);
  }

  function clearCurrentPageAnswers() {
    const page = pages[state.current];
    const confirmed = window.confirm(`Clear all saved answers for book page ${page.bookPage}?`);
    if (!confirmed) return;
    const prefix = `p${state.current + 1}-`;
    Object.keys(answers).filter(key => key.startsWith(prefix)).forEach(key => delete answers[key]);
    Object.keys(state.itemAttempts).filter(key => key.startsWith(prefix)).forEach(key => delete state.itemAttempts[key]);
    delete state.grades[state.current];
    delete state.attempts[state.current];
    saveAnswersLocally();
    renderWorkbook(state.current);
    persistState();
    ui.announcement.textContent = `Answers for book page ${page.bookPage} were cleared.`;
  }

  function showPage(index, announce = true) {
    const target = Math.max(0, Math.min(pages.length - 1, Number(index)));
    const page = pages[target];
    state.current = target;
    if (!state.viewed.includes(target)) state.viewed.push(target);

    ui.pageFrame.classList.add("loading");
    ui.loader.hidden = false;
    ui.pageStage.setAttribute("aria-busy", "true");
    ui.pageImage.src = page.src;
    ui.pageImage.alt = `Book page ${page.bookPage}: ${page.title}`;
    ui.pageTitle.textContent = page.title;
    ui.sectionLabel.textContent = page.section;
    ui.pagePosition.textContent = `Book page ${page.bookPage} · Lesson page ${target + 1} of ${pages.length}`;
    ui.pageSelect.value = String(target);
    ui.previousButton.disabled = target === 0;
    ui.nextButton.disabled = target === pages.length - 1;

    renderWorkbook(target);
    renderTranslanguaging(target);
    updateContents();
    persistState();
    updateProgress();
    preload(target);
    ui.pageStage.scrollTo({ top: 0, left: 0, behavior: "instant" });
    if (announce) ui.announcement.textContent = `Opened ${page.title}, book page ${page.bookPage}.`;
  }

  function applyZoom(value) {
    state.zoom = value;
    if (value === "fit") {
      ui.pageFrame.classList.add("fit");
      ui.pageFrame.style.removeProperty("--page-width");
    } else {
      ui.pageFrame.classList.remove("fit");
      ui.pageFrame.style.setProperty("--page-width", `${value}%`);
    }
    persistState();
  }

  function stepZoom(direction) {
    const levels = ["fit", "100", "125", "150", "200"];
    let index = levels.indexOf(state.zoom);
    if (direction > 0 && index < levels.length - 1) index += 1;
    if (direction < 0 && index > 0) index -= 1;
    ui.zoomSelect.value = levels[index];
    applyZoom(levels[index]);
  }

  function openSidebar() {
    ui.sidebar.classList.add("open");
    ui.menuButton.setAttribute("aria-expanded", "true");
    ui.scrim.hidden = false;
    ui.sidebarClose.focus();
  }

  function closeSidebar() {
    ui.sidebar.classList.remove("open");
    ui.menuButton.setAttribute("aria-expanded", "false");
    ui.scrim.hidden = true;
  }

  function bindEvents() {
    ui.pageImage.addEventListener("load", () => {
      ui.pageFrame.classList.remove("loading");
      ui.loader.hidden = true;
      ui.pageStage.setAttribute("aria-busy", "false");
    });
    ui.pageImage.addEventListener("error", () => {
      ui.loader.textContent = "This page image could not be loaded.";
      ui.pageStage.setAttribute("aria-busy", "false");
    });
    ui.previousButton.addEventListener("click", () => showPage(state.current - 1));
    ui.nextButton.addEventListener("click", () => showPage(state.current + 1));
    ui.pageSelect.addEventListener("change", event => showPage(Number(event.target.value)));
    ui.zoomSelect.addEventListener("change", event => applyZoom(event.target.value));
    ui.practiceJump.addEventListener("click", () => ui.workbook.scrollIntoView({ behavior: "smooth", block: "start" }));
    ui.translanguagingToggle.addEventListener("click", toggleTranslanguaging);
    ui.activityForm.addEventListener("submit", event => event.preventDefault());
    ui.clearAnswers.addEventListener("click", clearCurrentPageAnswers);
    ui.checkAnswers.addEventListener("click", () => gradePage(state.current, true));
    ui.revealAnswers.addEventListener("click", revealCurrentPageAnswers);
    ui.menuButton.addEventListener("click", openSidebar);
    ui.sidebarClose.addEventListener("click", closeSidebar);
    ui.scrim.addEventListener("click", closeSidebar);
    ui.fullscreenButton.addEventListener("click", async () => {
      try {
        if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
        else await document.exitFullscreen();
      } catch (_) { /* fullscreen may be restricted by LMS */ }
    });
    document.addEventListener("fullscreenchange", () => {
      ui.fullscreenButton.setAttribute("aria-label", document.fullscreenElement ? "Exit fullscreen" : "Enter fullscreen");
    });
    document.addEventListener("keydown", event => {
      if (event.target.matches("input, select, textarea, button")) return;
      if (event.key === "ArrowLeft") showPage(state.current - 1);
      else if (event.key === "ArrowRight") showPage(state.current + 1);
      else if (event.key === "Home") showPage(0);
      else if (event.key === "End") showPage(pages.length - 1);
      else if (event.key === "+" || event.key === "=") stepZoom(1);
      else if (event.key === "-") stepZoom(-1);
      else if (event.key === "Escape") closeSidebar();
    });
    window.addEventListener("pagehide", () => {
      saveAnswersLocally();
      persistState();
      if (scormConnected) window.ScormBridge.finish();
    });
  }

  restoreState();
  buildContents();
  bindEvents();
  ui.zoomSelect.value = state.zoom;
  applyZoom(state.zoom);
  showPage(state.current, false);
})();
