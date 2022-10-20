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

from invoke import task

from . import slides
from .config import CONTENTS_DIR, MKDIR, OUTPUT_DIR
from .utils import relative_path, up_to_date


PDF_BUILDER = "decktape reveal --size %(size)s %(in)s %(out)s"


@task
def decktape(c, unit, lang="*"):
    slides.slides(c, unit=unit, lang=lang, framework="revealjs")

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
                "size": slides.SLIDE_SIZE,
                "in": relative_path(src),
                "out": relative_path(target),
            })
