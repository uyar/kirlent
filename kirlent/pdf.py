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
from .utils import MKDIR, relative_path, up_to_date


BUILD_PDF: str = "decktape reveal --size %(size)s %(in)s %(out)s"


@task
def decktape(c, src, output):
    src_path, output_path = Path(src), Path(output)
    slides.slides(c, src=src_path, output=output_path, framework="revealjs")
    slides_path = Path(c.config["revealjs:output"])
    dst_name = slides_path.name.replace("revealjs", "decktape")
    dst_path = Path(output, dst_name).with_suffix(".pdf")
    if not up_to_date(dst_path, [slides_path]):
        if not dst_path.parent.exists():
            c.run(MKDIR % {"dir": relative_path(dst_path.parent)})
        c.run(BUILD_PDF % {
            "size": c.slides.size,
            "in": relative_path(slides_path),
            "out": relative_path(dst_path),
        })
