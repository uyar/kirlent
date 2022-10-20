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

from pathlib import Path

from invoke import Context, task

from .utils import (
    MKDIR,
    collect_assets,
    relative_path,
    relativize_paths,
    up_to_date
)


BUILD_SLIDES: str = "%(builder)s %(options)s %(in)s %(out)s"


def slides(c: Context, unit: str, *, framework: str, lang: str = "*") -> None:
    unit_path = Path(unit)
    slug = relative_path(unit_path, Path(c.contents))
    output_path = Path(c.output, slug)

    for src in unit_path.glob(f"slides.{lang}.rst"):
        language = src.name.split(".")[1]
        target_name = f"slides-{framework}.{language}.html"
        target = output_path / target_name
        raw_target = output_path / f".{target_name}"
        if not up_to_date(raw_target, [src]):
            if not raw_target.parent.exists():
                c.run(MKDIR % {"dir": relative_path(raw_target.parent)})
            options = c.slides.options.base + c.slides.options.get(framework, [])  # noqa: E501
            cli_options = " ".join(options) % {
                "lang": language,
                "size": c.slides.size,
            }
            format = "slides" if framework == "simple" else framework
            c.run(BUILD_SLIDES % {
                "builder": f"kirlent2{format}",
                "options": cli_options,
                "in": relative_path(src),
                "out": relative_path(raw_target),
            })
            relativize_paths(raw_target, src.parent)

        collect_assets(c, raw_target, target)


@task
def simple(c, unit, lang="*"):
    slides(c, unit, lang=lang, framework="simple")


@task
def impressjs(c, unit, lang="*"):
    slides(c, unit, lang=lang, framework="impressjs")


@task
def revealjs(c, unit, lang="*"):
    slides(c, unit, lang=lang, framework="revealjs")
