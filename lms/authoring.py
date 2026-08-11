"""Prompt-driven authoring workflow for LMS course builders."""

from .prompt_guides import list_prompt_guides


AUTHORING_STEPS = [
    {
        "key": "analysis",
        "title": "1. Analysis",
        "summary": "Understand learners, duties, skill gaps, and the reason training is needed.",
        "outputs": [
            "Learner persona",
            "Performance gap list",
            "Needs-analysis questions",
            "Measurable objectives",
        ],
    },
    {
        "key": "design",
        "title": "2. Design",
        "summary": "Plan the learning path before creating lessons, scripts, or quizzes.",
        "outputs": [
            "Course structure",
            "Storyboard outline",
            "Lesson flow",
            "Scenario map",
        ],
    },
    {
        "key": "development",
        "title": "3. Development",
        "summary": "Create the actual lesson material in a learner-friendly format.",
        "outputs": [
            "Video script",
            "Case study",
            "Interactive activity",
            "Question bank",
        ],
    },
    {
        "key": "implementation",
        "title": "4. Implementation",
        "summary": "Prepare LMS-facing text that helps learners start and finish the course.",
        "outputs": [
            "Course description",
            "Announcement",
            "Welcome message",
            "Reminder message",
        ],
    },
    {
        "key": "evaluation",
        "title": "5. Evaluation",
        "summary": "Collect evidence, summarize feedback, and improve the next course version.",
        "outputs": [
            "Survey questions",
            "Feedback summary",
            "Training results report",
            "Improvement plan",
        ],
    },
    {
        "key": "scenario",
        "title": "6. Scenario Practice",
        "summary": "Turn theory into realistic decisions, workplace dilemmas, and reflection tasks.",
        "outputs": [
            "Scenario ideas",
            "Workplace dilemma",
            "Ethical challenge",
            "Scenario themes",
        ],
    },
    {
        "key": "branching",
        "title": "7. Branching Decisions",
        "summary": "Build interactive choices with consequences, feedback, and decision trees.",
        "outputs": [
            "Branching scenario",
            "Decision tree",
            "Fast-vs-correct decision",
            "Leadership-style scenario",
        ],
    },
]


AUTHORING_CHECKLIST = [
    "The learner audience and level are named clearly.",
    "The learning goal says what learners should be able to do.",
    "The output format matches the LMS page, quiz, worksheet, video, or announcement.",
    "The prompt asks for plain language and realistic examples.",
    "The final draft is reviewed by a teacher or trainer before publishing.",
    "The activity, quiz, or feedback helps learners practise a real task.",
]


COURSE_PACK_DEFAULTS = {
    "title": "SSPA Checkpoint English and Visitor Screening",
    "level": "A2",
    "scenario": "checkpoint, visitor screening, radio communication, and incident notes",
    "final_task": "Learners complete a visitor-screening role-play and write a short incident note.",
    "modules": [
        {
            "title": "Learner Needs and Duty Language",
            "outcome": "Learners understand the duty situation, key roles, and the language they must use on post.",
            "lessons": [
                "Course welcome and learner goals",
                "Core vocabulary with simple examples",
                "Common performance gaps and mistakes",
                "Short diagnostic check",
            ],
        },
        {
            "title": "Scenario Vocabulary and Models",
            "outcome": "Learners can recognize and use essential terms in realistic checkpoint situations.",
            "lessons": [
                "Visitor and ID vocabulary",
                "Useful question forms",
                "Model checkpoint dialogue",
                "Microlearning review",
            ],
        },
        {
            "title": "Practice, Quiz, and Feedback",
            "outcome": "Learners practise decisions, receive feedback, and correct realistic mistakes.",
            "lessons": [
                "Scenario-based multiple-choice quiz",
                "Interactive worksheet",
                "Branching decision practice",
                "Feedback and revision task",
            ],
        },
        {
            "title": "Implementation and Communication",
            "outcome": "Learners know how to start, continue, and complete the LMS course successfully.",
            "lessons": [
                "Course announcement",
                "Welcome message",
                "Reminder message",
                "Completion message",
            ],
        },
        {
            "title": "Evaluation and Certificate",
            "outcome": "Learners show the skill in a final task and receive clear next steps.",
            "lessons": [
                "Final performance task",
                "Post-training survey",
                "Reflection prompt",
                "Certificate completion checklist",
            ],
        },
    ],
    "certificate_rules": [
        "Complete every module activity.",
        "Score at least 80% on the final quiz.",
        "Submit the final role-play note or practical task.",
        "Review trainer feedback before the certificate is issued.",
    ],
}


def list_authoring_recipes():
    """Flatten all guide prompts into selectable Authoring Studio recipes."""
    recipes = []
    for guide in list_prompt_guides():
        for group in guide.get("prompt_groups", []):
            phase = group["title"]
            for prompt in group.get("prompts", []):
                recipes.append({
                    "id": f"{guide['slug']}-{prompt['number']}",
                    "guide": guide["title"],
                    "guide_slug": guide["slug"],
                    "phase": phase,
                    "number": prompt["number"],
                    "title": prompt["title"],
                    "use": prompt.get("use", ""),
                    "template": prompt["template"],
                    "best_for": prompt.get("best_for", []),
                })
    return recipes
