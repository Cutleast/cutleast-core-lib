# Cutleast Core Lib

A core library used by my projects. Because of being quite specialized to my own needs, I doubt that this is useful for others.

However, given that it is under the MIT license, you are free to use it as you see fit.

## Basic Usage

```py
from cutleast_core_lib.core.utilities.scale import scale_value

print(scale_value(1253656678)) # '1.17 GB'
```

## How to use the `builder`-package for building standalone executables

An example build script in the using project could look like this:
`<project root>/scripts/build.py`
```py
import logging
import re
from pathlib import Path
from typing import override

from cutleast_core_lib.builder.backends.nuitka_backend import NuitkaBackend
from cutleast_core_lib.builder.build_config import BuildConfig
from cutleast_core_lib.builder.build_metadata import BuildMetadata
from cutleast_core_lib.builder.builder import Builder

logging.basicConfig(level=logging.DEBUG)


class MyBackend(NuitkaBackend):
    """
    My custom backend implementation, injecting the version into the app module before
    building.
    """

    # this injects the version at, e.g. `APP_VERSION: str = "development"`
    VERSION_PATTERN: re.Pattern[str] = re.compile(
        r'(?<=APP_VERSION: str = ")[^"]+(?=")'
    )

    @override
    def preprocess_source(self, source_folder: Path, metadata: BuildMetadata) -> None:
        app_module: Path = source_folder / "app.py"
        app_module.write_text(
            MyBackend.VERSION_PATTERN.sub(
                str(metadata.project_version), app_module.read_text(encoding="utf8")
            ),
            encoding="utf8",
        )
        self.log.info(
            f"Injected version '{metadata.project_version}' into '{app_module}'."
        )


if __name__ == "__main__":
    config = BuildConfig(
        exe_stem="example",
        icon_path=Path("res") / "icons" / "example.ico",
        ext_resources_json=Path("res") / "ext_resources.json",
    )
    backend = MyBackend()
    builder = Builder(config, backend)

    builder.run()
```

with `<project root>/pyproject.toml` being
```toml
[project]
name = "example-project"
version = "1.0.0-alpha-1"
description = "My example project"
license = { file = "LICENSE" }
authors = [{ name = "Jon Doe", email = "jon.doe@gmail.com" }]
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "cutleast_core_lib",
]

[dependency-groups]
dev = [
    "nuitka",
    "pyfakefs",
    "pyright",
    "pytest",
    "pytest-cov",
    "pytest-mock",
    "pytest-qt",
    "ruff",
]
```

then run `uv run scripts/build.py` from the project's root folder to build the standalone executable in `<project root>/dist`.
