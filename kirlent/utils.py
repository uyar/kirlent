# Copyright (C) 2022 H. Turgut Uyar <uyar@tekir.org>
#
# Kırlent is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kırlent is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kırlent.  If not, see <http://www.gnu.org/licenses/>.

from contextlib import redirect_stdout
from html import escape as html_escape
from html.parser import HTMLParser
from io import StringIO
from itertools import dropwhile, zip_longest
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree

from .config import COPY, MKDIR


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
