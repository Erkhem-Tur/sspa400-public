"""Extract multiple-choice questions and highlighted answers from the source PDF."""

import json
import re
import sys
from pathlib import Path

import pdfplumber


HEADING_RE = re.compile(r"^[А-ЯӨҮЁ\s]+(?:ТЕСТ|ТУХАЙ|ХУУЛЬ)$")
QUESTION_RE = re.compile(r"^(\d+)\s*[.)]\s*(.*)$")
OPTION_RE = re.compile(r"^([a-d])\s*[.)]\s*(.*)$", re.IGNORECASE)


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def highlighted_markers(page):
    words = page.extract_words(x_tolerance=2, y_tolerance=3)
    hits = []
    for annot in page.annots:
        quads = annot["data"].get("QuadPoints", [])
        selected = []
        for index in range(0, len(quads), 8):
            xs = quads[index:index + 8:2]
            ys = quads[index + 1:index + 8:2]
            if len(xs) != 4 or len(ys) != 4:
                continue
            x0, x1 = min(xs) - 1, max(xs) + 1
            top, bottom = page.height - max(ys) - 1, page.height - min(ys) + 1
            selected.extend(
                word for word in words
                if word["x1"] >= x0 and word["x0"] <= x1
                and word["bottom"] >= top and word["top"] <= bottom
            )
        selected.sort(key=lambda word: (word["top"], word["x0"]))
        markers = [
            match.group(1).lower()
            for word in selected
            if (match := OPTION_RE.match(word["text"]))
        ]
        hits.append({
            "page": page.page_number,
            "top": annot["top"],
            "answer": markers[-1] if markers else None,
        })
    return hits


def parse(pdf_path):
    questions = []
    section = "Хууль зүйн сорил"
    current = None
    active_option = None
    page_markers = {}
    option_locations = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_markers[page.page_number] = highlighted_markers(page)
            lines = page.extract_text_lines(x_tolerance=2, y_tolerance=3)
            for line in lines:
                value = clean(line["text"])
                if not value:
                    continue
                if HEADING_RE.match(value) and len(value) > 8:
                    section = value
                    continue
                question_match = QUESTION_RE.match(value)
                if question_match:
                    if current:
                        questions.append(current)
                    current = {
                        "section": section,
                        "number": int(question_match.group(1)),
                        "prompt": question_match.group(2),
                        "options": {},
                        "page": page.page_number,
                    }
                    active_option = None
                    continue
                option_match = OPTION_RE.match(value)
                if option_match and current:
                    active_option = option_match.group(1).lower()
                    current["options"][active_option] = option_match.group(2)
                    option_locations.append({
                        "question": current,
                        "answer": active_option,
                        "page": page.page_number,
                        "top": line["top"],
                    })
                    continue
                if current:
                    if active_option:
                        current["options"][active_option] += " " + value
                    else:
                        current["prompt"] += " " + value
        if current:
            questions.append(current)

    # Match the top edge of every highlight to the closest option-start line. This
    # remains reliable when the highlighted text wraps or omits the option letter.
    flat_markers = [marker for page in page_markers.values() for marker in page]
    for question in questions:
        question["answer"] = None
    for marker in flat_markers:
        candidates = [item for item in option_locations if item["page"] == marker["page"]]
        if not candidates:
            continue
        chosen = min(candidates, key=lambda item: abs(item["top"] - marker["top"]))
        if abs(chosen["top"] - marker["top"]) <= 22:
            chosen["question"]["answer"] = chosen["answer"]

    for question in questions:
        question.pop("page", None)

    # This answer is highlighted only on a wrapped continuation line, so the
    # automatic option-line matcher cannot see its letter. Visual QA confirms C.
    for question in questions:
        if question["section"] == "ТӨРИЙН ТУСГАЙ ХАМГААЛАЛТЫН ТУХАЙ ХУУЛЬ" and question["number"] == 96:
            question["answer"] = "c"

    return questions, flat_markers


if __name__ == "__main__":
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    questions, markers = parse(source)
    output.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
    invalid = [q for q in questions if len(q["options"]) < 2 or not q["answer"]]
    print(json.dumps({
        "questions": len(questions),
        "markers": len(markers),
        "invalid": len(invalid),
        "sections": sorted({q["section"] for q in questions}),
        "invalid_samples": invalid[:10],
    }, ensure_ascii=False, indent=2))
