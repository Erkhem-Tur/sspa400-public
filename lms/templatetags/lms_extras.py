from urllib.parse import parse_qs, urlparse

from django import template


register = template.Library()


@register.filter
def get_item(mapping, key):
    if not mapping:
        return None
    return mapping.get(str(key), mapping.get(key))


@register.filter
def youtube_embed(url):
    if not url:
        return ''
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix('www.')
    video_id = ''
    if host == 'youtu.be':
        video_id = parsed.path.strip('/').split('/')[0]
    elif host in {'youtube.com', 'm.youtube.com'}:
        if parsed.path == '/watch':
            video_id = parse_qs(parsed.query).get('v', [''])[0]
        elif parsed.path.startswith(('/embed/', '/shorts/')):
            video_id = parsed.path.strip('/').split('/')[1]
    if video_id and all(character.isalnum() or character in '_-' for character in video_id):
        return f'https://www.youtube-nocookie.com/embed/{video_id}?rel=0&modestbranding=1'
    return url


@register.filter
def display_name(user):
    if not user:
        return ''
    return user.get_full_name() or user.username
