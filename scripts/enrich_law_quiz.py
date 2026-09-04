"""Attach best-matching Legalinfo.mn provisions to the extracted quiz bank."""

import html
import json
import re
import sys
from pathlib import Path


SOURCES = {
    'ТӨРИЙН ТУСГАЙ ХАМГААЛАЛТЫН ТУХАЙ ХУУЛЬ': ('special-protection.html', 'https://legalinfo.mn/mn/detail?lawId=17140718521551'),
    'ҮНДЭСНИЙ АЮУЛГҮЙ БАЙДЛЫН ТУХАЙ': ('national-security.html', 'https://legalinfo.mn/mn/detail?lawId=18'),
    'МОНГОЛ УЛСЫН ТӨРИЙН ОРДНЫ ТУХАЙ ХУУЛЬ': ('state-palace.html', 'https://legalinfo.mn/mn/detail?lawId=100644'),
    'ТӨРИЙН БОЛОН АЛБАНЫ НУУЦЫН ТУХАЙ ХУУЛИЙН ТЕСТ': ('secrets.html', 'https://legalinfo.mn/mn/detail?lawId=12408'),
    'МОНГОЛ УЛСЫН ҮНДСЭН ХУУЛЬ': ('constitution.html', 'https://legalinfo.mn/mn/detail?lawId=367'),
    'ТӨРИЙН АЛБАНЫ ТУХАЙ ХУУЛЬ': ('civil-service.html', 'https://legalinfo.mn/mn/detail?lawId=13025'),
    'ЗӨРЧЛИЙН ТУХАЙ ХУУЛЬ': ('violations.html', 'https://legalinfo.mn/mn/detail?lawId=12695'),
    'ЗӨРЧИЛ ШАЛГАН ШИЙДВЭРЛЭХ ТУХАЙ ХУУЛЬ': ('violation-procedure.html', 'https://legalinfo.mn/mn/detail?lawId=12696'),
    'ЭРҮҮГИЙН ХУУЛЬ': ('criminal.html', 'https://legalinfo.mn/mn/detail?lawId=11634'),
    'ЖАГСААЛ ЦУГЛААН ХИЙХ ЖУРМЫН ТУХАЙ ХУУЛЬ': ('assembly.html', 'https://legalinfo.mn/mn/detail?lawId=252'),
    'ХҮНИЙ ХУВИЙН МЭДЭЭЛЭЛ ХАМГААЛАХ ТУХАЙ ХУУЛЬ': ('personal-data.html', 'https://legalinfo.mn/mn/detail?lawId=16390288615991'),
}

STOP = {'гэж', 'болон', 'буюу', 'тухай', 'хууль', 'заасан', 'дараах', 'аль', 'олно', 'уу', 'вэ', 'нь', 'энэ', 'тус', 'нэг', 'хамаарахгүйг', 'илүүцийг', 'буруу', 'зөв', 'хувилбарыг'}


def plain(value):
    value = re.sub(r'<[^>]+>', ' ', value)
    return re.sub(r'\s+', ' ', html.unescape(value)).strip()


def normalize(value):
    return re.sub(r'[^0-9a-zа-яөүё]+', ' ', value.casefold()).strip()


def tokens(value):
    return {word for word in normalize(value).split() if len(word) > 2 and word not in STOP}


def provisions(path):
    source = path.read_text(encoding='utf-8', errors='ignore')
    blocks = re.findall(r'<div\b([^>]*data-pp="[01]"[^>]*)>\s*<p[^>]*>(.*?)</p>\s*</div>', source, re.I | re.S)
    article = ''
    result = []
    for attrs, body in blocks:
        text = plain(body)
        marker = re.search(r'data-pp="([01])"', attrs)
        if not marker or not text:
            continue
        if marker.group(1) == '1':
            article = text
            continue
        reference = re.match(r'^((?:\d+\.)+\d+|\d+)\.?', text)
        result.append({'article': article, 'reference': reference.group(1) if reference else '', 'text': text})
    return result


def score(question, provision):
    answer = question['options'][question['answer']]
    answer_tokens = tokens(answer)
    prompt_tokens = tokens(question['prompt'])
    clause_tokens = tokens(provision['text'])
    title_tokens = tokens(provision['article'])
    overlap = len(answer_tokens & clause_tokens)
    precision = overlap / max(1, len(answer_tokens))
    recall = overlap / max(1, len(clause_tokens))
    answer_coverage = (2 * precision * recall / (precision + recall)) if precision + recall else 0
    prompt_coverage = len(prompt_tokens & (clause_tokens | title_tokens)) / max(1, len(prompt_tokens))
    exact_bonus = .12 if normalize(answer) in normalize(provision['text']) else 0
    cited = re.findall(r'(?<!\d)(\d+(?:\.\d+)+)(?!\d)', question['prompt'])
    citation_bonus = .45 if cited and any(provision['reference'].startswith(value) for value in cited) else 0
    return answer_coverage * .65 + prompt_coverage * .35 + exact_bonus + citation_bonus


def enrich(bank_path, legal_dir):
    bank = json.loads(bank_path.read_text(encoding='utf-8'))
    cache = {section: provisions(legal_dir / filename) for section, (filename, _) in SOURCES.items()}
    scores = []
    changed = []
    for question in bank:
        if question.get('source_answer_changed'):
            question['answer'] = question.pop('source_answer_changed')
        if not question.get('answer'):
            continue
        candidates = cache[question['section']]
        negative = any(word in question['prompt'].casefold() for word in ('хамаарахгүй', 'хамааралгүй', 'үл хамаарах', 'тохирохгүй', 'илүүц', 'буруу', 'үл тохирох'))
        if not negative:
            option_rankings = []
            original_answer = question['answer']
            for option_key in question['options']:
                probe = dict(question, answer=option_key)
                option_rankings.append((max(score(probe, item) for item in candidates), option_key))
            option_rankings.sort(reverse=True)
            original_score = next(value for value, key in option_rankings if key == original_answer)
            best_score, best_key = option_rankings[0]
            if best_key != original_answer and best_score >= .60 and best_score - original_score >= .04:
                question['answer'] = best_key
                question['source_answer_changed'] = original_answer
                changed.append((question['section'], question['number'], original_answer, best_key))
        ranked = sorted(((score(question, item), item) for item in candidates), key=lambda item: item[0], reverse=True)
        confidence, match = ranked[0]
        _, url = SOURCES[question['section']]
        correct = question['options'][question['answer']]
        ref = match['reference'] or match['article'].split(' ')[0]
        if negative:
            reasoning = f'{ref}-д хамаарах нөхцөл, бүрэлдэхүүнийг тогтоосон байна. Сонгосон бусад хувилбарууд уг зохицуулалтад нийцэх боловч “{correct}” нь жагсаалт, шаардлагад ороогүй тул зөв хариу болно.'
        else:
            reasoning = f'{ref}-д “{correct}” гэсэн агуулгыг шууд тогтоосон тул энэ хувилбар зөв.'
        question.update({
            'legal_reference': ref,
            'legal_article': match['article'],
            'legal_url': url,
            'legal_excerpt': match['text'][:420],
            'reasoning': reasoning,
            'match_confidence': round(confidence, 3),
            'reference_status': 'verified' if confidence >= .55 else 'related',
        })
        scores.append(confidence)
    return bank, scores


if __name__ == '__main__':
    bank_path = Path(sys.argv[1])
    bank, scores = enrich(bank_path, Path(sys.argv[2]))
    bank_path.write_text(json.dumps(bank, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({
        'enriched': len(scores),
        'mean_confidence': round(sum(scores) / len(scores), 3),
        'below_0_35': sum(value < .35 for value in scores),
        'below_0_25': sum(value < .25 for value in scores),
    }, ensure_ascii=False))
