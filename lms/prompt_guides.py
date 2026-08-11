"""Readable prompt-design guides for LMS course authors."""


PROMPT_GUIDES = [
    {
        "slug": "prompt-design-lms",
        "title": "Prompt Design for LMS Content Creation",
        "subtitle": "A practical guide for turning AI into useful course content.",
        "summary": (
            "Learn how to write clear prompts for lessons, video scripts, quizzes, "
            "activities, summaries, glossaries, localisation, and learner feedback."
        ),
        "audience": "Instructors, course creators, and LMS content reviewers",
        "level": "Beginner friendly",
        "time": "25 minutes",
        "hero_icon": "bi-magic",
        "overview": [
            {
                "title": "Why prompt design matters",
                "body": [
                    "AI can create lessons, quizzes, activities, scripts, and summaries, but vague requests usually produce vague training material.",
                    "A strong LMS prompt gives the AI a role, learner level, topic, objective, output format, and quality rules.",
                ],
                "bullets": [
                    "Use a clear role, such as instructional designer or assessment specialist.",
                    "Name the learners and their level.",
                    "State the exact learning objective.",
                    "Ask for a format that can be uploaded or adapted in the LMS.",
                    "Add quality rules so the result stays useful and readable.",
                ],
            },
            {
                "title": "Simple formula",
                "body": [
                    "Use this structure whenever you need a reliable first draft.",
                ],
                "example": """Act as a [role].
Create [type of LMS content].
The topic is [topic].
The learners are [audience and level].
The goal is [learning objective].
Use this format: [format].
Follow these rules: [quality requirements].""",
            },
            {
                "title": "Example prompt",
                "body": [
                    "This version is specific enough for AI to create a usable lesson draft.",
                ],
                "example": """Act as an instructional designer.
Create a beginner-friendly lesson for an LMS.
The topic is workplace safety vocabulary.
The learners are security officers learning English.
The goal is to help them understand and use 10 key safety terms.
Use short explanations, examples, one practice activity, and a 5-question quiz.
Use clear language and avoid difficult grammar.""",
            },
        ],
        "prompt_groups": [
            {
                "title": "10 Useful AI Prompt Types for LMS Content",
                "intro": "Choose the prompt type that matches the task you are building today.",
                "prompts": [
                    {
                        "number": 1,
                        "title": "Course Structure Prompt",
                        "use": "Use this when you need to plan a whole course from the beginning.",
                        "template": """Act as an expert instructional designer.

Design a complete online course for an LMS.

Course topic: [topic]
Learners: [audience and level]
Main goal: [what learners should be able to do]

Create:
1. A short course promise
2. 4 to 6 modules in logical order
3. 3 to 5 lessons per module
4. A learning objective for each module
5. Suggested lesson formats, such as video, reading, checklist, worksheet, or quiz
6. A final practical project or assessment

Write in clear Markdown.""",
                        "best_for": [
                            "Planning a new course",
                            "Organizing modules and lessons",
                            "Creating a complete learning path",
                        ],
                    },
                    {
                        "number": 2,
                        "title": "Video Lesson Script Prompt",
                        "use": "Use this when you need a short training video that is easy to hear and follow.",
                        "template": """Act as an educational scriptwriter.

Write a video lesson script for an LMS.

Course topic: [topic]
Lesson title: [lesson title]
Learners: [audience and level]
Tone: [friendly, professional, practical, etc.]
Length: [3 to 5 minutes]

Structure the script with:
1. Hook: get attention quickly
2. Promise: explain what learners will learn
3. Main teaching: maximum 3 key points
4. Practical example
5. Short summary and next step

Format the output as a two-column table:
- Visual / screen direction
- Audio / voiceover

Use short sentences and natural spoken language.""",
                        "best_for": [
                            "Narrated LMS videos",
                            "Microlearning scripts",
                            "Trainer recording notes",
                        ],
                    },
                    {
                        "number": 3,
                        "title": "Quiz and Question Bank Prompt",
                        "use": "Use this when you need fair questions that test real understanding.",
                        "template": """Act as an educational assessment specialist.

Create a quiz for an LMS.

Topic: [topic]
Learners: [audience and level]
Number of questions: [number]
Assessment type: [practice quiz or final quiz]

Create mostly scenario-based multiple-choice questions.

For each question, include:
1. Question statement
2. Four answer options
3. Correct answer
4. Feedback explaining why the answer is correct

Rules:
- No trick questions
- No confusing double negatives
- Wrong answers should be realistic learner mistakes
- All answer choices should be similar in length""",
                        "best_for": [
                            "Practice quizzes",
                            "Final checks",
                            "Reusable question banks",
                        ],
                    },
                    {
                        "number": 4,
                        "title": "Simplification Prompt",
                        "use": "Use this when source text is too technical, academic, or difficult.",
                        "template": '''Act as a science communicator and instructional designer.

Rewrite the text below so beginners can understand it.

Topic: [topic]
Learners: [audience and level]
Tone: clear, respectful, and practical
Output format: [lesson, article, script, summary, etc.]

Original text:
"""
[paste difficult text here]
"""

Rewrite it with:
1. A short "why this matters" opening
2. One everyday analogy
3. 3 to 5 key ideas
4. A quick glossary for difficult terms
5. A practical next step

Rules:
- Use active voice
- Use short paragraphs
- Keep important facts and numbers
- Do not talk down to the learner''',
                        "best_for": [
                            "Turning policy into lessons",
                            "Making source text beginner friendly",
                            "Preparing teacher-reviewed drafts",
                        ],
                    },
                    {
                        "number": 5,
                        "title": "Case Study Prompt",
                        "use": "Use this when learners need to see how theory works in real life.",
                        "template": """Act as an educational storyteller.

Create a realistic case study for an LMS lesson.

Topic: [topic]
Learning objective: [what learners should learn]
Learners: [audience and level]
Scenario: [workplace, school, business, security post, etc.]

Include:
1. Context and main character
2. Problem or conflict
3. Decision point
4. Step-by-step resolution
5. Three key takeaways
6. Two reflection questions

Rules:
- Make the character realistic
- Show pressure, mistakes, and decisions
- Do not make the solution too easy
- Use simple, direct language""",
                        "best_for": [
                            "Scenario lessons",
                            "Discussion sections",
                            "Reflection activities",
                        ],
                    },
                    {
                        "number": 6,
                        "title": "Interactive Activity Prompt",
                        "use": "Use this when learners need to practise, not only read or watch.",
                        "template": """Act as a learning experience designer.

Create an interactive activity for an LMS.

Topic: [topic]
Learners: [audience and level]
Submission format: [worksheet, forum post, upload, checklist, etc.]
Time needed: [10 minutes, 20 minutes, etc.]

Include:
1. Purpose: why the activity matters
2. Step-by-step instructions
3. Expected final result
4. A short worked example
5. A success checklist

Rules:
- Make the activity practical
- Use clear action verbs
- Start with an easy first step
- Keep instructions short""",
                        "best_for": [
                            "Worksheets",
                            "Forum posts",
                            "Upload tasks and checklists",
                        ],
                    },
                    {
                        "number": 7,
                        "title": "Microlearning Summary Prompt",
                        "use": "Use this when you need a short review focused on one idea.",
                        "template": '''Act as a microlearning specialist.

Turn the lesson below into a short LMS summary.

Topic: [topic]
Learners: [audience]
Source material:
"""
[paste lesson text here]
"""

Create:
1. One-sentence hook
2. The main idea in 3 bullet points or fewer
3. One action step learners can use today
4. One memorable takeaway sentence

Keep the final text under 200 words.''',
                        "best_for": [
                            "Lesson recaps",
                            "Quick review blocks",
                            "Pre-quiz refreshers",
                        ],
                    },
                    {
                        "number": 8,
                        "title": "Glossary Prompt",
                        "use": "Use this when learners need clear definitions of key terms.",
                        "template": '''Act as an educational glossary writer.

Create a glossary for an LMS course.

Course topic: [topic]
Learner level: [beginner, intermediate, advanced]
Number of terms: [number]
Source material or term list:
"""
[paste text or terms here]
"""

For each term, include:
1. Term and acronym if any
2. Simple definition
3. Real-life example sentence

Rules:
- Put terms in alphabetical order
- Avoid circular definitions
- Use plain language''',
                        "best_for": [
                            "Vocabulary lessons",
                            "Technical courses",
                            "Operational term banks",
                        ],
                    },
                    {
                        "number": 9,
                        "title": "Translation and Localisation Prompt",
                        "use": "Use this to adapt learning content for another language or region.",
                        "template": '''Act as an eLearning localisation expert.

Localise this LMS content.

Source language: [language]
Target language and region: [language and country/region]
Learners: [audience]
Content type: [lesson, video script, quiz, worksheet]
Tone: [professional, friendly, formal, etc.]

Original text:
"""
[paste text here]
"""

Requirements:
1. Translate naturally
2. Adapt examples and metaphors for the target region
3. Convert dates, measurements, and currencies if needed
4. Keep key terminology consistent

At the end, add short localisation notes explaining the main changes.''',
                        "best_for": [
                            "Bilingual course content",
                            "Regional examples",
                            "Consistent terminology",
                        ],
                    },
                    {
                        "number": 10,
                        "title": "Feedback Prompt",
                        "use": "Use this when learners submit open-ended answers or assignments.",
                        "template": '''Act as a virtual tutor and academic evaluator.

Review this learner submission.

Course topic: [topic]
Assignment brief: [what the learner was asked to do]
Rubric: [criteria for success]
Tone: encouraging, clear, and professional

Learner submission:
"""
[paste learner answer here]
"""

Give feedback with:
1. Positive opening
2. Strengths
3. Areas for improvement
4. One or two reflection questions
5. Clear next steps
6. Suggested grade or status if required

Rules:
- Be specific
- Do not be condescending
- Do not write the perfect answer for the learner
- Guide the learner toward improvement''',
                        "best_for": [
                            "Essay feedback",
                            "Forum response coaching",
                            "Assignment review",
                        ],
                    },
                ],
            }
        ],
        "workflow_title": "How to use AI content in an LMS",
        "workflow": [
            "Generate the draft with a clear prompt.",
            "Review the content as a teacher or trainer.",
            "Check accuracy, examples, tone, and difficulty level.",
            "Add activities, quizzes, and learner instructions.",
            "Upload the final version into the LMS.",
            "Test the lesson as a student before releasing it.",
        ],
        "rules": [
            {
                "title": "Give clear context",
                "body": "Tell the AI who it should act as, who the learners are, and what the output must do.",
            },
            {
                "title": "Improve the first output",
                "body": "Ask for revisions such as: make it simpler, add one practical example, turn this into a quiz, or add a learner activity.",
            },
            {
                "title": "Keep human review",
                "body": "A teacher or trainer must still check accuracy, examples, level, assessments, grammar, and tone.",
            },
        ],
        "final_note": "AI helps create faster drafts, but humans make the learning meaningful, accurate, and motivating.",
    },
    {
        "slug": "ai-instructional-design",
        "title": "AI in Instructional Design Prompt Library",
        "subtitle": "A complete, organized library of the 33 supplied instructional-design prompts.",
        "summary": (
            "Use AI across analysis, design, development, implementation, evaluation, "
            "scenario brainstorming, and branching-scenario planning."
        ),
        "audience": "Instructional designers, instructors, and training managers",
        "level": "Beginner to intermediate",
        "time": "35 minutes",
        "hero_icon": "bi-diagram-3",
        "overview": [
            {
                "title": "Simple overview",
                "body": [
                    "Instructional designers create course outlines, storyboards, scripts, scenarios, quizzes, LMS announcements, and feedback surveys.",
                    "AI helps with brainstorming, drafting, rewriting, and organizing ideas. The designer still checks quality, accuracy, learner level, and learning value.",
                ],
            },
            {
                "title": "What is a prompt?",
                "body": [
                    "A prompt is the instruction you give to AI. Better prompts include context, learner audience, output format, and constraints.",
                ],
                "example": """Create a 3-module course outline about healthcare compliance.
The learners are new hospital employees.
Include scenario-based examples and one quiz per module.""",
            },
            {
                "title": "Prompt quality checklist",
                "body": [
                    "Before using AI, include the topic, learner audience, learner level, learning goal, course format, tone, output format, and constraints.",
                ],
            },
        ],
        "prompt_groups": [
            {
                "title": "1. Analysis Phase",
                "intro": "Use these prompts before building the course. The goal is to understand learners, job needs, skill gaps, and training goals.",
                "prompts": [
                    {
                        "number": 1,
                        "title": "Create Learner Personas",
                        "template": "Create learner personas for a course on [topic].\nInclude their job roles, challenges, and motivations.",
                        "best_for": ["Early research", "ADDIE analysis", "Audience profiling"],
                    },
                    {
                        "number": 2,
                        "title": "Identify Performance Gaps",
                        "template": "List common performance gaps in [job role] that training could address.",
                        "best_for": ["Needs analysis", "Workplace training design", "Understanding real job challenges"],
                    },
                    {
                        "number": 3,
                        "title": "Create Needs Analysis Questions",
                        "template": "Write interview questions to find out learning needs for [department].",
                        "best_for": ["Stakeholder interviews", "Training needs assessments", "Planning before course design"],
                    },
                    {
                        "number": 4,
                        "title": "Suggest Learning Objectives",
                        "template": "Suggest learning objectives for a course on [topic] using [ID model].",
                        "best_for": ["Defining course goals", "Writing measurable objectives", "Connecting content to outcomes"],
                    },
                    {
                        "number": 5,
                        "title": "Identify Key Skills",
                        "template": "What are the key skills needed for success in [job role]?",
                        "best_for": ["Competency mapping", "Role-based training", "Job-specific curriculum planning"],
                    },
                ],
                "tip": "If your LMS has learner data, include completion rates, quiz scores, common failed questions, and learner feedback carefully.",
            },
            {
                "title": "2. Design Phase",
                "intro": "Use these prompts after you understand the learners. The goal is to plan how the learning experience will work.",
                "prompts": [
                    {
                        "number": 6,
                        "title": "Create a Storyboard Outline",
                        "template": "Create a storyboard outline for a [topic] microlearning module.",
                        "best_for": ["Storyboarding", "Early course planning", "Microlearning design"],
                    },
                    {
                        "number": 7,
                        "title": "Build an eLearning Flow",
                        "template": "Generate an eLearning flow using [ID model] for [topic].",
                        "best_for": ["Lesson sequencing", "Course structure", "Designing the learner journey"],
                    },
                    {
                        "number": 8,
                        "title": "Write an Intro Lesson Script",
                        "template": "Write an engaging script for an introductory lesson on [topic]\nthat motivates learners to complete the module.",
                        "best_for": ["Course introductions", "Setting tone", "Increasing learner motivation"],
                    },
                    {
                        "number": 9,
                        "title": "Design a Branching Scenario",
                        "template": "Design a branching scenario with 3 decision points for [situation],\nincluding correct and incorrect choices.",
                        "best_for": ["Scenario-based learning", "Decision-making practice", "Interactive lessons"],
                    },
                    {
                        "number": 10,
                        "title": "Suggest Visual and Multimedia Elements",
                        "template": "Suggest visual and multimedia elements like images, icons,\nand interactions for a lesson about [topic].",
                        "best_for": ["Visual planning", "Multimedia lesson design", "Authoring tool preparation"],
                    },
                ],
                "tip": "Ask AI for several options, then combine the best ideas into one course plan.",
            },
            {
                "title": "3. Development Phase",
                "intro": "Use these prompts when you are creating the actual learning content.",
                "prompts": [
                    {
                        "number": 11,
                        "title": "Write a Dialogue for Feedback Skills",
                        "template": "Write a 2-minute dialogue between a manager and an employee\nthat shows effective feedback.",
                        "best_for": ["Scenario scripts", "Soft skills training", "Dialogue-based learning"],
                    },
                    {
                        "number": 12,
                        "title": "Generate Multiple-Choice Questions",
                        "template": "Generate 5 multiple-choice questions with explanations\nfor each correct answer about [topic].",
                        "best_for": ["Knowledge checks", "Quizzes", "Assessment practice"],
                    },
                    {
                        "number": 13,
                        "title": "Create a Case Study Scenario",
                        "template": "Create a short case study scenario with 3 discussion questions for learners.",
                        "best_for": ["Critical thinking", "Group discussion", "Reflection activities"],
                    },
                    {
                        "number": 14,
                        "title": "Write a Short Video Script",
                        "template": "Write an engaging script for a 3-minute video explaining [concept].",
                        "best_for": ["Microlearning videos", "Explainer content", "Narrated lessons"],
                    },
                    {
                        "number": 15,
                        "title": "Suggest Visual Aids",
                        "template": "Suggest visuals, icons, and examples that make [concept] easier to understand.",
                        "best_for": ["Graphics", "Slides", "Visual explanation"],
                    },
                ],
                "tip": "If AI gives a generic answer, add learner level, tone, workplace context, and the exact task.",
            },
            {
                "title": "4. Implementation Phase",
                "intro": "Use these prompts when the course is ready to launch in the LMS.",
                "prompts": [
                    {
                        "number": 16,
                        "title": "Write an LMS Course Announcement",
                        "template": "Write an enthusiastic course announcement for the LMS\nabout a new [topic] module.",
                        "best_for": ["Course launches", "Learner motivation", "LMS homepage updates"],
                    },
                    {
                        "number": 17,
                        "title": "Write an LMS Course Description",
                        "template": "Create a short LMS description that highlights key points\nfor [course name]. Keep it under 150 words.",
                        "best_for": ["Course catalog listings", "Short promotional text", "LMS course cards"],
                    },
                    {
                        "number": 18,
                        "title": "Create Welcome Messages",
                        "template": "Generate welcome messages for learners starting their first online course in [LMS].",
                        "best_for": ["Learner onboarding", "First-course experience", "Engagement"],
                    },
                    {
                        "number": 19,
                        "title": "Draft Reminder Emails",
                        "template": "Draft reminder emails for learners who have not finished their training yet.",
                        "best_for": ["Increasing completion rates", "Re-engaging inactive learners", "Automated LMS communication"],
                    },
                    {
                        "number": 20,
                        "title": "Write Completion Messages",
                        "template": "Write friendly completion messages to congratulate learners\nwho finished the course.",
                        "best_for": ["Positive reinforcement", "Completion screens", "Certificates and course endings"],
                    },
                ],
                "tip": "Try formal, friendly, motivational, and short direct versions before publishing.",
            },
            {
                "title": "5. Evaluation Phase",
                "intro": "Use these prompts after learners complete the course. The goal is to measure effectiveness and improve future versions.",
                "prompts": [
                    {
                        "number": 21,
                        "title": "Write Post-Training Survey Questions",
                        "template": "Generate 5 post-training survey questions to measure\nknowledge retention and engagement.",
                        "best_for": ["Feedback collection", "Kirkpatrick Level 1 evaluation", "Learner satisfaction surveys"],
                    },
                    {
                        "number": 22,
                        "title": "Summarize Learner Feedback",
                        "template": "Summarize learner feedback comments to find suggested improvements.",
                        "best_for": ["Feedback analysis", "Finding common themes", "Course improvement planning"],
                    },
                    {
                        "number": 23,
                        "title": "Create a Training Results Summary",
                        "template": "Write a short summary of training results for [stakeholder].\nUse a professional tone.",
                        "best_for": ["Reporting", "Stakeholder communication", "Management summaries"],
                    },
                    {
                        "number": 24,
                        "title": "Recommend Course Improvements",
                        "template": "Suggest ways to improve course engagement based on this feedback:\n[paste learner comments].",
                        "best_for": ["Continuous improvement", "Course revision", "Learner engagement planning"],
                    },
                    {
                        "number": 25,
                        "title": "Create Reflection Prompts",
                        "template": "Create prompts for encouraging learners to apply new skills after the course.",
                        "best_for": ["Post-training reflection", "Skill transfer", "Follow-up activities"],
                    },
                ],
                "tip": "Paste survey responses into AI and ask it to group them into positive feedback, negative feedback, and suggested improvements.",
            },
            {
                "title": "6. Scenario Brainstorming",
                "intro": "Use these prompts when you need realistic training situations, workplace dilemmas, ethical challenges, and scenario themes.",
                "prompts": [
                    {
                        "number": 26,
                        "title": "Generate Scenario Ideas",
                        "template": "Generate 5 realistic scenario ideas for a training on [topic]\nthat helps learners practice [skill].",
                        "best_for": ["Early brainstorming", "Scenario concept development", "Practice-based learning"],
                    },
                    {
                        "number": 27,
                        "title": "Create a Workplace Dilemma",
                        "template": "Create a workplace dilemma related to [topic]\nthat encourages critical thinking.",
                        "best_for": ["Scenario inspiration", "Ethics training", "Problem-solving lessons"],
                    },
                    {
                        "number": 28,
                        "title": "List Ethical Challenges",
                        "template": "List 3 ethical challenges a [job role] might face in [industry].",
                        "best_for": ["Compliance training", "Ethics training", "Decision-making practice"],
                    },
                    {
                        "number": 29,
                        "title": "Suggest Scenario Themes",
                        "template": "Suggest scenario themes for teaching [topic] to entry-level employees.",
                        "best_for": ["Beginner-friendly scenarios", "Onboarding", "Entry-level workplace training"],
                    },
                ],
            },
            {
                "title": "7. Branching Scenario Prompts",
                "intro": "Branching scenarios let learners make choices. Each choice leads to a consequence, which makes learning more active and realistic.",
                "prompts": [
                    {
                        "number": 30,
                        "title": "Create a Branching Scenario",
                        "template": "Create a branching scenario with 3 decision points for a [topic] training.\nEach choice should lead to realistic consequences.",
                        "best_for": ["Interactive scenarios", "Complex decision-making", "Practice with consequences"],
                    },
                    {
                        "number": 31,
                        "title": "Generate a Decision Tree Table",
                        "template": "Generate a table outlining a decision tree for [situation],\nshowing choices, consequences, and feedback messages.",
                        "best_for": ["Scenario planning", "Storyboard structure", "LMS interaction design"],
                    },
                    {
                        "number": 32,
                        "title": "Fast vs. Correct Decision Scenario",
                        "template": "Write a scenario where a learner must choose between doing what is fast\nand doing what is correct. Show how each decision affects the outcome.",
                        "best_for": ["Quality training", "Compliance training", "Time-pressure decisions"],
                    },
                    {
                        "number": 33,
                        "title": "Leadership Style Scenario",
                        "template": "Design a problem-solving scenario where each learner choice\nreveals a different leadership style.",
                        "best_for": ["Leadership training", "Interpersonal skills", "Self-awareness activities"],
                    },
                ],
            },
        ],
        "workflow_title": "How to use this prompt library in an LMS",
        "workflow": [
            "Start with analysis prompts to understand learners.",
            "Use design prompts to plan modules and storyboards.",
            "Use development prompts to create content and quizzes.",
            "Use implementation prompts to launch and communicate the course.",
            "Use evaluation prompts to improve the course after learners complete it.",
        ],
        "rules": [
            {
                "title": "Replace brackets with real context",
                "body": "Swap every bracketed placeholder for your real topic, learner group, level, tool, or goal.",
            },
            {
                "title": "Review as an instructional designer",
                "body": "Check whether the draft supports a real learning outcome and fits the learner level.",
            },
            {
                "title": "Revise before publishing",
                "body": "Ask AI to simplify, localize, make the activity more practical, or add stronger feedback.",
            },
        ],
        "final_note": "The source text references 41 prompts, but the attached material includes prompts 1 through 33. This page organizes all 33 supplied prompts.",
    },
]


for guide in PROMPT_GUIDES:
    guide["prompt_count"] = sum(
        len(group["prompts"]) for group in guide.get("prompt_groups", [])
    )
    guide["group_count"] = len(guide.get("prompt_groups", []))


PROMPT_GUIDE_MAP = {guide["slug"]: guide for guide in PROMPT_GUIDES}


def list_prompt_guides():
    """Return all public prompt guides."""
    return PROMPT_GUIDES


def get_prompt_guide(slug):
    """Return a guide by slug, or None when the slug is unknown."""
    return PROMPT_GUIDE_MAP.get(slug)
