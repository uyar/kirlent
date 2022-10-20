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

from invoke import Collection, task

from . import pdf, slides
from .utils import COPY


@task
def setup(c):
    c.run("python -m pip --require-virtualenv install -U kirlent_docutils")
    c.run("npm install decktape")

    c.run(COPY % {
        "src": Path(__file__).parent / "env",
        "dst": Path(".env"),
    })

    c.run(COPY % {
        "src": Path(__file__).parent / "kirlent.json",
        "dst": Path("kirlent.json"),
    })


namespace: Collection = Collection(setup, slides, pdf)
