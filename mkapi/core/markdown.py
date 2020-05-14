from markdown import Markdown

converter = Markdown()


def convert(text, inline):
    html = converter.convert(text).strip()
    if inline:
        html = html.replace("<p>", "")
        html = html.replace("</p>", "<br>")
        if html.endswith('<br>'):
            html = html[:-4]
    return html
