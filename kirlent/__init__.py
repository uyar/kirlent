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

__version__ = "0.3"

import json
from pathlib import Path

from invoke import Collection, Program

from . import tasks


config: Path = Path("kirlent.json")
if not config.exists():
    config = Path(__file__).parent / "kirlent.json"

namespace: Collection = Collection.from_module(tasks)
namespace.configure(json.loads(config.read_text()))

program: Program = Program(namespace=namespace, version=__version__)
