"""Convert the integrated A2-B1 DOCX course pack into LMS JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


def blocks(document):
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield "paragraph", Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield "table", Table(child, document)


def clean_prompt(text: str) -> str:
    text = re.sub(r"\s*Answer:\s*_+\s*", "", text.replace("\n", " / "))
    return re.sub(r"\s+", " ", text).strip(" / ")


def table_rows(table: Table) -> list[list[str]]:
    return [
        [re.sub(r"\s+", " ", cell.text).strip() for cell in row.cells]
        for row in table.rows
    ]


def parse_diagnostic(texts: list[str], answer_text: str) -> list[dict]:
    answer_letters = {
        int(number): letter
        for number, letter in re.findall(r"(\d+)\s+([a-d])", answer_text.lower())
    }
    questions = []
    for number, text in enumerate(texts, start=1):
        parts = re.split(r"\s+([a-d])\)\s+", text)
        if len(parts) != 9:
            raise ValueError(f"Could not parse diagnostic question {number}: {text}")
        prompt = parts[0].strip()
        options = [parts[index].strip() for index in (2, 4, 6, 8)]
        answer = ord(answer_letters[number]) - ord("a")
        questions.append({"number": number, "prompt": prompt, "options": options, "answer": answer})
    return questions


def convert(source: Path, destination: Path) -> None:
    document = Document(source)
    lessons: list[dict] = []
    lesson = None
    section = ""
    in_answer_keys = False
    answer_lesson = None
    answer_section = ""
    answer_map: dict[int, dict[str, list[str]]] = {}
    diagnostic_texts: list[str] = []
    diagnostic_answer_text = ""
    final = {"reading": "", "reading_questions": [], "language_questions": [], "writing": "", "speaking": ""}
    final_section = ""

    for kind, block in blocks(document):
        if kind == "paragraph":
            text = block.text.strip()
            if not text:
                continue
            style = block.style.name

            if style == "Heading 1":
                if text == "Answer Keys":
                    in_answer_keys = True
                    lesson = None
                    continue
                match = re.match(r"Lesson (\d+):\s*(.+)", text)
                if match and not in_answer_keys:
                    lesson = {
                        "number": int(match.group(1)),
                        "title": match.group(2),
                        "level": "",
                        "time": "90 minutes",
                        "language_focus": "",
                        "outcomes": [],
                        "sequence": [],
                        "vocabulary": [],
                        "reading_title": "",
                        "reading": "",
                        "reading_questions": [],
                        "language_practice": [],
                        "performance_task": "",
                        "homework": "",
                    }
                    lessons.append(lesson)
                    section = ""
                    continue
                if text == "Diagnostic Test":
                    section = "diagnostic"
                    lesson = None
                    continue
                if text == "Final Assessment":
                    section = "final"
                    final_section = ""
                    lesson = None
                    continue

            if in_answer_keys:
                match = re.match(r"Lesson (\d+):", text) if style == "Heading 2" else None
                if match:
                    answer_lesson = int(match.group(1))
                    answer_map.setdefault(answer_lesson, {"reading": [], "language": []})
                    answer_section = ""
                elif style == "Heading 2" and text == "Diagnostic test":
                    answer_lesson = None
                    answer_section = "diagnostic"
                elif style == "Heading 2" and text.startswith("Final assessment"):
                    answer_lesson = None
                    answer_section = "final"
                elif style == "Heading 3" and text == "Reading check":
                    answer_section = "reading"
                elif style == "Heading 3" and text == "Language focus":
                    answer_section = "language"
                elif answer_section == "diagnostic" and style == "Normal":
                    diagnostic_answer_text = text
                elif answer_lesson and answer_section in ("reading", "language") and style == "Course Number":
                    answer_map[answer_lesson][answer_section].append(text)
                continue

            if section == "diagnostic" and style == "Course Number":
                diagnostic_texts.append(text)
                continue

            if section == "final":
                if style == "Heading 2":
                    final_section = text
                elif style == "Heading 3":
                    final_section = text
                elif style == "Normal" and final_section.startswith("Part A"):
                    final["reading"] = text
                elif style == "Course Number" and final_section.startswith("Reading questions"):
                    final["reading_questions"].append(clean_prompt(text))
                elif style == "Course Number" and final_section.startswith("Language questions"):
                    final["language_questions"].append(clean_prompt(text))
                continue

            if not lesson:
                continue

            if style == "Heading 2":
                known = {
                    "Learning outcomes": "outcomes",
                    "Teacher sequence": "sequence",
                    "Target vocabulary": "vocabulary",
                    "Language focus": "language",
                    "Main speaking task": "performance",
                    "Homework": "homework",
                }
                if text in known:
                    section = known[text]
                else:
                    section = "reading"
                    lesson["reading_title"] = text
                continue
            if style == "Heading 3" and text == "Reading check":
                section = "reading_questions"
                continue

            if section == "outcomes" and style == "Course Bullet":
                lesson["outcomes"].append(text)
            elif section == "reading" and style in ("Normal", "Course Dialogue"):
                lesson["reading"] += ("\n" if lesson["reading"] else "") + text
            elif section == "reading_questions" and style == "Course Number":
                lesson["reading_questions"].append(clean_prompt(text))
            elif section == "language" and style == "Course Number":
                lesson["language_practice"].append(clean_prompt(text))
            elif section == "homework" and style == "Normal":
                lesson["homework"] += (" " if lesson["homework"] else "") + text

        else:
            rows = table_rows(block)
            if not rows:
                continue
            header = rows[0]
            first = header[0]
            if lesson and header == ["Level", "Time", "Language focus"] and len(rows) > 1:
                lesson["level"], lesson["time"], lesson["language_focus"] = rows[1]
            elif lesson and header == ["Time", "Stage", "Teacher and learner action"]:
                lesson["sequence"] = [
                    {"time": row[0], "stage": row[1], "action": row[2]} for row in rows[1:]
                ]
            elif lesson and header == ["Word", "Plain-English meaning", "Example"]:
                lesson["vocabulary"] = [
                    {"word": row[0], "meaning": row[1], "example": row[2]} for row in rows[1:]
                ]
            elif lesson and first.startswith("Task:"):
                lesson["performance_task"] = first.removeprefix("Task:").strip()
            elif section == "final" and first.startswith("Prompt:"):
                final["writing"] = first.removeprefix("Prompt:").strip()
            elif section == "final" and first.startswith("Choose one task:"):
                final["speaking"] = first

    if len(lessons) != 8:
        raise ValueError(f"Expected 8 lessons, found {len(lessons)}")
    for item in lessons:
        answers = answer_map.get(item["number"], {})
        item["reading_answers"] = answers.get("reading", [])
        item["language_answers"] = answers.get("language", [])
        if len(item["vocabulary"]) != 6 or not item["reading"] or not item["homework"]:
            raise ValueError(f"Lesson {item['number']} is incomplete")

    final_reading_answers = [
        "Three days.",
        "Their travel documents.",
        "Any two: quiet study rooms, dining area, fitness room.",
        "Professional greetings, directions, and clarification questions.",
        "Preparation, accurate reporting, and verified instructions.",
        "Read a historical or global-affairs text and present a neutral briefing.",
        "To distinguish supported facts from unsupported claims or opinions.",
    ]
    final_language_answers = [
        "are", "must", "should not", "A hotel was reserved by the center.",
        "Could I have the schedule, please?", "a small modern fitness room", "accurately",
        "Accept any accurate first conditional, e.g., If the flight is delayed, I will check the departure screen.",
        "Fact", "Opinion",
    ]
    final["reading_answers"] = final_reading_answers
    final["language_answers"] = final_language_answers

    payload = {
        "meta": {
            "title": "Integrated English Course Pack",
            "level": "A2-B1",
            "lesson_count": 8,
            "minutes_per_lesson": 90,
            "total_hours": 12,
        },
        "diagnostic": {
            "questions": parse_diagnostic(diagnostic_texts, diagnostic_answer_text),
            "profiles": [
                {"min": 0, "max": 5, "label": "A1 foundations", "guidance": "Use extra modeling, translation support, and paired reading."},
                {"min": 6, "max": 10, "label": "Developing A2", "guidance": "Follow the core course and use sentence frames."},
                {"min": 11, "max": 13, "label": "Strong A2", "guidance": "Use the core course plus extension questions."},
                {"min": 14, "max": 15, "label": "B1 entry", "guidance": "Use leadership roles and advanced extension tasks."},
            ],
        },
        "lessons": lessons,
        "final_assessment": final,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    convert(args.source, args.destination)


if __name__ == "__main__":
    main()
