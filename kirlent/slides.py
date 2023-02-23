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
from typing import Mapping

from invoke import Context, task

from .utils import MKDIR, collect_assets, relative_path, up_to_date


BUILDERS: Mapping[str, str] = {
    "simple": "kirlent2slides",
    "impressjs": "kirlent2impressjs",
    "revealjs": "kirlent2revealjs",
}

BUILD_DOCUTILS = '%(builder)s %(options)s "%(in)s"'
BUILD_DECKTAPE = 'decktape reveal --size %(size)s "%(in)s" "%(out)s"'


def slides(c: Context, src: Path, output: Path, *, framework: str) -> None:
    suffixes = "".join(src.suffixes)
    dst_name = src.name.replace(suffixes, f"-{framework}{suffixes}")
    dst = Path(output, dst_name).with_suffix(".html")
    if not up_to_date(dst, [src]):
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
            BUILD_DOCUTILS % {
                "builder": BUILDERS[framework],
                "options": cli_options,
                "in": relative_path(src),
            },
            out_stream=out,
        )
        text = collect_assets(c, out.getvalue(), base=output, wrt=src.parent)
        dst.write_text(text)
    c.config[f"{framework}:output"] = str(dst)


@task
def simple(c: Context, src: str, output: str) -> None:
    slides(c, Path(src), Path(output), framework="simple")


@task
def impressjs(c: Context, src: str, output: str) -> None:
    slides(c, Path(src), Path(output), framework="impressjs")


@task
def revealjs(c: Context, src: str, output: str) -> None:
    slides(c, Path(src), Path(output), framework="revealjs")


@task
def decktape(c: Context, src: str, output: str) -> None:
    src_path, output_path = Path(src), Path(output)
    slides(c, src=src_path, output=output_path, framework="revealjs")
    slides_path = Path(c.config["revealjs:output"])
    dst_name = slides_path.name.replace("revealjs", "decktape")
    dst_path = Path(output, dst_name).with_suffix(".pdf")
    if not up_to_date(dst_path, [slides_path]):
        if not dst_path.parent.exists():
            c.run(MKDIR % {"dir": relative_path(dst_path.parent)})
        c.run(BUILD_DECKTAPE % {
            "size": c.slides.size,
            "in": relative_path(slides_path),
            "out": relative_path(dst_path),
        })
