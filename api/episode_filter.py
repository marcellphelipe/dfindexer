"""Filter explicit episode mismatches without discarding ambiguous releases."""
import re

_MARKER = re.compile(r'(?i)(?<!\w)s(\d{1,3})[ ._-]*e(\d{1,3})((?:[ ._-]*(?:e|[-–][ ._]*e?)\d{1,3})*)|(?<!\w)(\d{1,3})x(\d{1,3})((?:[ ._-]*(?:x|[-–][ ._]*)(?:\d{1,3}x)?\d{1,3})*)')
_PACK = re.compile(r'(?i)(?<!\w)s(\d{1,3})(?![\w]|[ ._-]*e\d)|\b(?:season|temporada)[ ._-]*(\d{1,3})\b|\b(\d{1,3})\s*[ªºa]?\s*temporada\b')


def _numbers(first, tail):
    numbers = [int(first)]
    for marker, number in re.findall(r'(?i)(e|x|[-–][ ._]*e?)(\d{1,3})', tail):
        end = int(number)
        if marker.startswith(('-', '–')) and numbers[-1] <= end <= numbers[-1] + 100:
            numbers.extend(range(numbers[-1] + 1, end + 1))
        else:
            numbers.append(end)
    return numbers


def matches_episode(title, season, episode):
    """Keep exact matches, matching season packs, and unidentifiable titles."""
    markers = list(_MARKER.finditer(title or ''))
    if markers:
        for m in markers:
            s, first, tail = (m.group(1), m.group(2), m.group(3)) if m.group(1) else (m.group(4), m.group(5), m.group(6))
            if int(s) == season and episode in _numbers(first, tail or ''):
                return True
        return False
    packs = list(_PACK.finditer(title or ''))
    if packs:
        return any(int(next(g for g in m.groups() if g is not None)) == season for m in packs)
    return True


def episode_request(season, episode, keywords):
    """Only activate for unambiguous numeric TV episode queries."""
    if season and episode and str(season).isdigit() and str(episode).isdigit():
        return int(season), int(episode)
    # Some clients provide SxxExx in q instead of structured TV parameters.
    if not season and not episode:
        match = _MARKER.search(keywords or '')
        if match and not (match.group(3) or match.group(6)):
            return (int(match.group(1)), int(match.group(2))) if match.group(1) else (int(match.group(4)), int(match.group(5)))
    return None
