# Copyright (C) 2022-2023 H. Turgut Uyar <uyar@tekir.org>
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

from io import StringIO
from pathlib import Path
from typing import Mapping, Union

from invoke import Context, task

from .templates import INDEX_TEMPLATE, ITEM_TEMPLATE
from .utils import MKDIR, collect_assets, relative_path, up_to_date


DOCUTILS_BUILDERS: Mapping[str, str] = {
    "simple": "kirlent2slides",
    "impressjs": "kirlent2impressjs",
    "revealjs": "kirlent2revealjs",
}

DOCUTILS = '%(builder)s %(options)s "%(in)s"'
DECKTAPE = 'decktape reveal --size %(size)s "%(in)s" "%(out)s"'
PDFNUP = 'pdfjam --quiet --nup %(nup)s %(extras)s -o "%(out)s" "%(in)s"'


def update_index(c: Context, framework: str) -> None:
    output = Path(c.config[f"{framework}:output"])
    index = output.parent / "index.html"
    if not index.exists():
        width, height = c.config["slides"]["size"].split("x")
        item = ITEM_TEMPLATE % {
            "file": output.name,
            "framework": framework,
        }
        content = INDEX_TEMPLATE % {
            "size": f"width={width}, height={height}",
            "items": item,
        }
        index.write_text(content)
    else:
        content = index.read_text()
        item = ITEM_TEMPLATE % {
            "file": output.name,
            "framework": framework,
        }
        if item not in content:
            content = content.replace('  </ul>\n', f'{item}\n  </ul>\n')
            index.write_text(content)


def slides(c: Context, src: Path, output: Path, *, framework: str,
           recreate: bool = False) -> None:
    suffixes = "".join(src.suffixes)
    dst_name = src.name.replace(suffixes, f"-{framework}{suffixes}")
    dst = Path(output, dst_name).with_suffix(".html")
    c.config[f"{framework}:output"] = str(dst)
    if recreate or (not up_to_date(dst, [src])):
        if not dst.parent.exists():
            c.run(MKDIR % {"dir": relative_path(dst.parent)})
        lang = src.name.split(".")[1]
        options = c.slides.options.base + c.slides.options.get(framework, [])
        cli_options = " ".join(options) % {
            "lang": lang,
            "size": c.slides.size,
        }
        out = StringIO()
        c.run(
            DOCUTILS % {
                "builder": DOCUTILS_BUILDERS[framework],
                "options": cli_options,
                "in": relative_path(src),
            },
            out_stream=out,
        )
        text = collect_assets(c, out.getvalue(), base=output, wrt=src.parent)
        dst.write_text(text)
        update_index(c, framework)


@task
def simple(c: Context, src: str, output: str, recreate: bool = False) -> None:
    slides(c, Path(src), Path(output), framework="simple", recreate=recreate)


@task
def impressjs(c: Context, src: str, output: str,
              recreate: bool = False) -> None:
    slides(c, Path(src), Path(output), framework="impressjs",
           recreate=recreate)


@task
def revealjs(c: Context, src: str, output: str,
             recreate: bool = False) -> None:
    slides(c, Path(src), Path(output), framework="revealjs", recreate=recreate)


@task
def decktape(c: Context, src: str, output: str, recreate: bool = False,
             nup: Union[str, None] = None) -> None:
    src_path, output_path = Path(src), Path(output)
    slides(c, src=src_path, output=output_path, framework="revealjs",
           recreate=recreate)
    slides_path = Path(c.config["revealjs:output"])
    dst_name = slides_path.name.replace("revealjs", "decktape")
    dst_path = Path(output, dst_name).with_suffix(".pdf")
    if recreate or (not up_to_date(dst_path, [slides_path])):
        if not dst_path.parent.exists():
            c.run(MKDIR % {"dir": relative_path(dst_path.parent)})
        c.run(DECKTAPE % {
            "size": c.slides.size,
            "in": relative_path(slides_path),
            "out": relative_path(dst_path),
        })

    if nup is not None:
        nup_path = dst_path.with_suffix(f".{nup}.pdf")
        if not up_to_date(nup_path, [dst_path]):
            extras = []
            cols, rows = nup.split("x")
            if cols >= rows:
                extras.append("--landscape")
            c.run(PDFNUP % {
                "nup": nup,
                "extras": " ".join(extras),
                "in": dst_path,
                "out": nup_path,
            })
