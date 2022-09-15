from itertools import dropwhile, zip_longest
from pathlib import Path
from xml.etree import ElementTree

from invoke import task


PROJECT_DIR = Path()
CONTENTS_DIR = Path(PROJECT_DIR, "contents")
OUTPUT_DIR = Path(PROJECT_DIR, "_build")

MKDIR = "mkdir -p %(dir)s"
COPY = "cp %(src)s %(dst)s"
BUNDLE = "zip -q -r %(archive)s.zip %(src)s"

SLIDE_SIZE = "1125x795"  # A4
SLIDES_OPTIONS = [
    "--stylesheet-path=itucs.css,kirlent_%(framework)s.css",
    "--link-stylesheet",
    "--lang=%(lang)s",
    "--slide-size=%(size)s",
]

SLIDE_BUILDER = "kirlent2%(framework)s %(options)s %(in)s %(out)s"

PDF_BUILDER = "decktape reveal --size %(size)s %(in)s %(out)s"


def relative_path(path, wrt=None):
    start = wrt if wrt is not None else Path()
    parts = zip_longest(start.resolve().parts, path.resolve().parts)
    path_diff = dropwhile(lambda ps: ps[0] == ps[1], parts)
    up_parts, down_parts = zip(*path_diff)
    up_path = Path(*[".." for p in up_parts if p is not None])
    down_path = Path(*[p for p in down_parts if p is not None])
    return Path(up_path, down_path)


def _refs(content):
    content = content.replace('script defer', 'script')
    root = ElementTree.fromstring(content)
    return [
        ref.get(attr)
        for tag, attr in (("link", "href"), ("script", "src"), ("img", "src"))
        for ref in root.findall(f".//{tag}")
    ]


def relativize_paths(doc, wrt):
    content = doc.read_text()
    content_ = content
    for ref in _refs(content):
        if (ref is None) or (ref.startswith(("http://", "https://"))):
            continue
        ref_ = ref.split("file://")[-1]
        asset = Path(wrt, ref_)
        target = relative_path(asset, doc.parent)
        content_ = content_.replace(ref, str(target))
    if content_ != content:
        doc.write_text(content_)


def newer(x, y):
    return x.stat().st_mtime_ns > y.stat().st_mtime_ns


def up_to_date(target, deps):
    return target.exists() and all(newer(target, dep) for dep in deps)


def collect_files(c, doc):
    doc = Path(doc)
    suffixes = "".join(doc.suffixes)
    artifact = doc.name[:doc.name.rindex(suffixes)]
    target = Path(doc.parent, f"{artifact}-full{suffixes}")

    content = doc.read_text()
    content_ = content
    for ref in _refs(content):
        if (ref is None) or (ref.startswith(("http://", "https://"))):
            continue
        asset_src = Path(doc.parent, ref).resolve()
        asset_dst = Path(target.parent, asset_src.name)
        if not up_to_date(asset_dst, [asset_src]):
            c.run(COPY % {
                "src": relative_path(asset_src),
                "dst": relative_path(asset_dst),
            })
        pos = ref.rfind(asset_dst.name)
        content_ = content_.replace(ref, ref[pos:])

    if not up_to_date(target, [doc]):
        target.write_text(content_)


@task
def setup(c):
    c.run("python -m pip --require-virtualenv install kirlent_docutils")
    c.run("npm install decktape")

    env = Path(__file__).parent / "env"
    c.run(f"cp {env} .env")


@task
def slides(c, unit, lang="*", framework="slides", collect=False, bundle=False):
    unit_path = Path(unit)
    slug = relative_path(unit_path, CONTENTS_DIR)
    out_path = Path(OUTPUT_DIR, slug)

    for src in unit_path.glob(f"slides.{lang}.rst"):
        artifact, language, _ = src.name.split(".")
        target = Path(out_path, f"{artifact}-{framework}.{language}.html")
        if not up_to_date(target, [src]):
            if not target.parent.exists():
                c.run(MKDIR % {"dir": relative_path(target.parent)})
            cli_options = " ".join(SLIDES_OPTIONS) % {
                "lang": language,
                "size": SLIDE_SIZE,
                "framework": framework,
            }
            c.run(SLIDE_BUILDER % {
                "framework": framework,
                "options": cli_options,
                "in": relative_path(src),
                "out": relative_path(target),
            })
            relativize_paths(target, src.parent)

        if collect or bundle:
            collect_files(c, target)

    if bundle:
        with c.cd(out_path.parent):
            c.run(BUNDLE % {"archive": slug.name, "src": slug.name})


@task
def pdf(c, unit, lang="*", framework="decktape"):
    slides(c, unit=unit, lang=lang, framework="revealjs", collect=True)

    unit_path = Path(unit)
    slug = relative_path(unit_path, CONTENTS_DIR)
    out_path = Path(OUTPUT_DIR, slug)

    for src in out_path.glob(f"slides-revealjs-full.{lang}.html"):
        artifact, language, _ = src.name.split(".")
        src = Path(out_path, f"slides-revealjs-full.{lang}.html")
        target = Path(out_path, f"slides.{language}.pdf")
        c.run(PDF_BUILDER % {
            "size": SLIDE_SIZE,
            "in": relative_path(src),
            "out": relative_path(target),
        })
