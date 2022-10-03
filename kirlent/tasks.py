from contextlib import redirect_stdout
from html import escape as html_escape
from html.parser import HTMLParser
from io import StringIO
from itertools import dropwhile, zip_longest
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree

from invoke import task


PROJECT_DIR = Path()
CONTENTS_DIR = Path(PROJECT_DIR, "contents")
OUTPUT_DIR = Path(PROJECT_DIR, "_build")

MKDIR = "mkdir -p %(dir)s"
COPY = "cp %(src)s %(dst)s"

SLIDE_SIZE = "1125x795"  # A4
SLIDES_OPTIONS = [
    "--link-stylesheet",
    "--lang=%(lang)s",
    "--slide-size=%(size)s",
]

SLIDE_BUILDER = "kirlent2%(framework)s %(options)s %(in)s %(out)s"

PDF_BUILDER = "decktape reveal --size %(size)s %(in)s %(out)s"


def newer(x, y):
    return x.stat().st_mtime_ns > y.stat().st_mtime_ns


def up_to_date(target, deps):
    return target.exists() and all(newer(target, dep) for dep in deps)


def relative_path(path, wrt=None):
    start = wrt if wrt is not None else Path()
    parts = zip_longest(start.resolve().parts, path.resolve().parts)
    path_diff = dropwhile(lambda ps: ps[0] == ps[1], parts)
    up_parts, down_parts = zip(*path_diff)
    up_path = Path(*[".." for p in up_parts if p is not None])
    down_path = Path(*[p for p in down_parts if p is not None])
    return Path(up_path, down_path)


class HTMLNormalizer(HTMLParser):
    VOID_ELEMENTS = frozenset({"br", "col", "hr", "img", "link", "meta"})

    def handle_starttag(self, tag, attrs):
        attribs = []
        for attr_name, attr_value in attrs:
            if attr_value is None:
                attr_value = ""
            markup = '%(name)s="%(value)s"' % {
                "name": attr_name,
                "value": html_escape(attr_value, quote=True),
            }
            attribs.append(markup)
        line = "<%(tag)s%(attrs)s%(slash)s>" % {
            "tag": tag,
            "attrs": (" " + " ".join(attribs)) if len(attribs) > 0 else "",
            "slash": "/" if tag in HTMLNormalizer.VOID_ELEMENTS else "",
        }
        print(line, end="")

    def handle_endtag(self, tag):
        print(f"</{tag}>", end="")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        print(html_escape(data), end="")

    def error(self, message):
        """Ignore errors."""


def html_to_xhtml(document):
    out = StringIO()
    normalizer = HTMLNormalizer()
    with redirect_stdout(out):
        normalizer.feed(document)
    return out.getvalue()


def refs(content):
    root = ElementTree.fromstring(html_to_xhtml(content))
    return [
        ref.get(attr)
        for tag, attr in (("link", "href"), ("script", "src"), ("img", "src"))
        for ref in root.findall(f".//{tag}[@{attr}]")
    ]


def relativize_paths(doc, wrt):
    content = doc.read_text()
    content_ = content
    for ref in refs(content):
        parsed = urlparse(ref)
        if parsed.scheme not in {"", "file"}:
            continue
        asset = Path(wrt, parsed.path).resolve()
        asset_relative = relative_path(asset, doc.parent)
        content_ = content_.replace(ref, str(asset_relative))
    if content_ != content:
        doc.write_text(content_)


def collect_assets(c, doc, target):
    content = doc.read_text()
    content_ = content
    for ref in refs(content):
        parsed = urlparse(ref)
        if parsed.scheme not in {"", "file"}:
            continue
        asset_src = Path(doc.parent, parsed.path).resolve()
        asset_dst = Path(target.parent, asset_src.name)
        if not up_to_date(asset_dst, [asset_src]):
            c.run(COPY % {
                "src": relative_path(asset_src),
                "dst": relative_path(asset_dst),
            })
        pos = ref.rfind(asset_dst.name)
        content_ = content_.replace(ref, ref[pos:])

    if not up_to_date(target, [doc]):
        if not target.parent.exists():
            c.run(MKDIR % {"dir": relative_path(target.parent)})
        target.write_text(content_)


@task
def setup(c):
    c.run("python -m pip --require-virtualenv install -U kirlent_docutils")
    c.run("npm install decktape")

    env = Path(__file__).parent / "env"
    c.run(f"cp {env} .env")


@task
def slides(c, unit, lang="*", framework="slides"):
    unit_path = Path(unit)
    slug = relative_path(unit_path, CONTENTS_DIR)
    output_path = Path(OUTPUT_DIR, slug)

    for src in unit_path.glob(f"slides.{lang}.rst"):
        language = src.name.split(".")[1]
        target_name = f"slides-{framework}.{language}.html"
        target = Path(output_path, target_name)
        raw_target = Path(output_path, f".{target_name}")
        if not up_to_date(raw_target, [src]):
            if not raw_target.parent.exists():
                c.run(MKDIR % {"dir": relative_path(raw_target.parent)})
            cli_options = " ".join(SLIDES_OPTIONS) % {
                "lang": language,
                "size": SLIDE_SIZE,
            }
            c.run(SLIDE_BUILDER % {
                "framework": framework,
                "options": cli_options,
                "in": relative_path(src),
                "out": relative_path(raw_target),
            })
            relativize_paths(raw_target, src.parent)

        collect_assets(c, raw_target, target)


@task
def pdf(c, unit, lang="*", framework="decktape"):
    slides(c, unit=unit, lang=lang, framework="revealjs")

    unit_path = Path(unit)
    slug = relative_path(unit_path, CONTENTS_DIR)
    output_path = Path(OUTPUT_DIR, slug)

    for src in output_path.glob(f"slides-revealjs.{lang}.html"):
        language = src.name.split(".")[1]
        target = Path(output_path, f"slides-decktape.{language}.pdf")
        if not up_to_date(target, [src]):
            if not target.parent.exists():
                c.run(MKDIR % {"dir": relative_path(target.parent)})
            c.run(PDF_BUILDER % {
                "size": SLIDE_SIZE,
                "in": relative_path(src),
                "out": relative_path(target),
            })
