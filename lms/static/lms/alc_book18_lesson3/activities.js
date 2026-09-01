(function (global) {
  "use strict";

  const group = (title, count, type = "short", hint = "", answers = null, start = 1) => ({
    title, count, type, hint, answers, start
  });
  const starts = value => ({ startsWith: value });
  const all = (...values) => ({ all: values });

  global.LESSON_ACTIVITIES = [
    {
      note: "Set your goals for this lesson.",
      groups: [group("Before you begin", 1, "long", "What do you want to improve in this lesson?")]
    },
    {
      note: "Use this page to preview the lesson language.",
      groups: [group("Vocabulary to remember", 5, "short", "Write five useful words or expressions from the preview.")]
    },
    {
      groups: [group("Comprehension A–C", 3, "long", "Answer the question in each labeled section: A, B, and C.")]
    },
    {
      groups: [
        group("Exercise A", 8, "short", "Write T or F. Correct false statements in the same field.", [
          starts("f"), starts("t"), starts("t"), starts("f"), starts("t"), starts("t"), starts("f"), starts("f")
        ]),
        group("Exercise B", 8, "short", "Write the replacement word or expression.", [
          "point out", "head", "benefit", "policies", "indefinitely", "now that", "excellent", "employee"
        ])
      ]
    },
    {
      note: "Record key information from the training dialog.",
      groups: [group("Training notes", 4, "long", "Write four important facts from the dialog.")]
    },
    {
      groups: [group("Exercise A", 4, "long", "Write the negative questions you identified in the dialog.", [
        "Wasn't he going to begin training?",
        "Didn't you get his message?",
        "Hasn't his father been very ill for a long time?",
        "Wouldn't it be a good idea to send get-well cards to Paul's father?"
      ])]
    },
    {
      groups: [
        group("Exercise B", 7, "long", "Change each statement into a negative question.", [
          "Doesn't your plane leave at 4:00?",
          "Couldn't Mike finish his report on time?",
          "Hasn't Brenda been to Rome?",
          "Won't Jim fly to Chicago before he flies to London?",
          "Didn't John pass his test?",
          "Wasn't the first sergeant at the meeting?",
          ["Aren't I getting an assignment to Alaska?", "Am I not getting an assignment to Alaska?"]
        ]),
        group("Exercise C", 3, "long", "Rewrite any three questions using the formal pattern shown.")
      ]
    },
    {
      groups: [group("Exercise D", 6, "short", "Write A, S/A, or I for each item.", [
        "S/A", "A", "I", "S/A", "A", "I"
      ])]
    },
    {
      groups: [
        group("Exercise E", 6, "short", "Write your personal Yes/No answer."),
        group("Exercise F", 6, "long", "Complete each question for a partner."),
        group("Bonus", 1, "long", "Write one negative Why question.")
      ]
    },
    {
      note: "Use the handbook page as a reference.",
      groups: [
        group("Benefits", 3, "short", "List three benefits."),
        group("Policies", 3, "short", "List three policies.")
      ]
    },
    {
      groups: [
        group("Exercise A", 6, "short", "Write the correct word.", [
          "hire", "agree", "get off", "concern", "supervise", "employment"
        ]),
        group("Exercise B", 5, "short", "Complete the paragraph with words from the box.", [
          "mainly", "point out", "permitted", "fired", "definite"
        ]),
        group("Exercise C: Benefits", 3),
        group("Exercise C: Policies", 3)
      ]
    },
    {
      groups: [group("Exercise A", 8, "short", "Write the matching letter.", [
        "h", "f", "g", "b", "c", "a", "d", "e"
      ])]
    },
    {
      groups: [
        group("Exercise B", 4, "long", "Respond with can’t be or couldn’t be and give a reason."),
        group("Exercise C", 3, "long", "Write three false or unlikely things about yourself.")
      ]
    },
    {
      note: "The six answers depend on the teacher's spoken questions.",
      groups: [group("Reading a diagram", 6, "short", "Record your answers for the teacher-led questions.")]
    },
    {
      note: "Read the three professional e-mail messages.",
      groups: [group("Main ideas", 3, "long", "Write one main idea for each message.")]
    },
    {
      groups: [
        group("Exercise A", 8, "short", "Write the matching letter.", [
          "d", "h", "a", "g", "b", "c", "e", "f"
        ]),
        group("Exercise B", 6, "short", "Write a, b, or c.", [
          "a", "b", "a", "a", "a", "c"
        ])
      ]
    },
    {
      note: "Read both sides of the editorial.",
      groups: [group("Susan’s point of view", 2, "long"), group("Tom’s point of view", 2, "long")]
    },
    {
      groups: [
        group("Exercise A", 7, "short", "Write Susan, Tom, Neither, or both names where appropriate.", [
          "susan", "neither", "susan", "tom", ["susan and tom", "tom and susan", "both"], "susan", "tom"
        ]),
        group("Exercise B", 7, "short", "Complete each blank with a word from the box.", [
          "convince", "get rid of", "disagree", "to tell you the truth", "definitely", "unemployment", "point of view"
        ])
      ]
    },
    {
      groups: [group("Exercise C", 8, "short", "Write a, b, or c.", [
        "c", "a", "c", "c", "c", "b", "a", "b"
      ])]
    },
    {
      groups: [
        group("Exercise D", 6, "short", "Complete the paragraph with words from the box.", [
          "disagrees", "unemployed", "on the one hand", "employ", "on the other hand", "point"
        ]),
        group("Exercise E", 10, "long", "Write the missing word form(s) for each row. Separate multiple answers with commas.", [
          null, "agreement", "supervise", "definitely", all("employee", "employer", "employment"),
          "disagreement", "indefinite", "main", "unemployment", "personally"
        ])
      ]
    },
    {
      groups: [group("Exercise F", 10, "long", "Write the related word form(s) that complete each numbered item.", [
        "chief", "agreement", "supervise", "definitely", all("employees", "employer", "employment"),
        "disagreements", "indefinite", "main", "unemployment", "personally"
      ])]
    },
    {
      groups: [
        group("Your opinion", 5, "short", "Write strongly agree, agree, disagree, or strongly disagree."),
        group("Partner discussion", 1, "long", "Record your strongest reason or useful language from the discussion.")
      ]
    },
    {
      note: "Audio was not included with the source PDF, so these responses require teacher review.",
      groups: [
        group("Intonation practice", 10, "short", "Write Falling or Rising after listening with your teacher."),
        group("Speaking reflection", 1, "long", "Write one tag question you can use in conversation.")
      ]
    },
    {
      groups: [
        group("Exercise A", 7, "short", "Choose the adjective or noun.", [
          "illness", "nervousness", "softness", "dark", "bitter", "tightness", "polite"
        ]),
        group("Exercise B", 3, "short", "Choose the adjective or noun.", [
          "happiness", "friendly", "readiness"
        ])
      ]
    },
    {
      groups: [
        group("Exercise C", 8, "short", "Change the adjective to a noun with -ness.", [
          "cleverness", "aloneness", "smoothness", "illness", "laziness", "thickness", "dizziness", "hardness"
        ]),
        group("Exercise A", 3, "short", "Choose the verb or noun with -ment.", [
          "retirement", "government", "measure"
        ])
      ]
    },
    {
      groups: [
        group("Exercise A continued", 7, "short", "Choose the verb or noun.", [
          "appoint", "employment", "enlistment", "disagree", "agree", "argument", ["judgment", "judgement"]
        ], 4),
        group("Exercise B", 8, "short", "Change the verb and complete the blank.", [
          "entertainment", "postponement", "attachment", "argument", "treatment", "placement", "advertisement", "requirement"
        ])
      ]
    },
    {
      groups: [
        group("Past robots", 1, "long", "List details that apply to past robots."),
        group("Both", 1, "long", "List similarities."),
        group("Today’s robots", 1, "long", "List details that apply to today’s robots.")
      ]
    },
    {
      groups: [group("Exercise A: Summary", 1, "essay", "Write a short summary using your own words. Include the main idea and important information; do not add your opinion.")]
    }
  ];
})(window);
