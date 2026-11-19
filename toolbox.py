"""Find a folder's tools: every function listed in ``TOOLS`` inside each ``tools_*.py`` file.

``server.py`` and the harness's ``--list`` both load tools through here, so they always agree
on what a folder offers. A file that crashes while loading is skipped and reported, so one
broken file never takes down the whole server.
"""

import importlib
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TOOL_FILE_PATTERN = "tools_*.py"
TOOLS_LIST_NAME = "TOOLS"


@dataclass
class TeamTool:
    """One tool: its function and the file (role) it came from."""

    function: Callable[..., Any]
    file_name: str

    @property
    def name(self) -> str:
        """The tool's name, which is the function's name."""
        tool_name = self.function.__name__
        return tool_name


@dataclass
class TeamToolbox:
    """All the tools that loaded, the modules they came from, and any loading problems."""

    tools: list[TeamTool] = field(default_factory=list)
    modules: dict[str, Any] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)


def load_team_tools(tools_directory: Path) -> TeamToolbox:
    """Import every ``tools_*.py`` file in ``tools_directory`` and collect its ``TOOLS`` list."""
    toolbox = TeamToolbox()
    directory_text = str(tools_directory.resolve())
    if directory_text not in sys.path:
        sys.path.insert(0, directory_text)
    tool_files = sorted(tools_directory.glob(TOOL_FILE_PATTERN))
    seen_names: set[str] = set()
    for tool_file in tool_files:
        module_name = tool_file.stem
        try:
            module = importlib.import_module(module_name)
        except Exception as error:  # a tool file can fail in any way while loading
            toolbox.problems.append(
                f"{tool_file.name} did not load: {type(error).__name__}: {error}"
            )
            continue
        toolbox.modules[module_name] = module
        tools_list = getattr(module, TOOLS_LIST_NAME, None)
        if not isinstance(tools_list, list):
            toolbox.problems.append(f"{tool_file.name} has no {TOOLS_LIST_NAME} = [...] list.")
            continue
        for tool_function in tools_list:
            if not callable(tool_function):
                toolbox.problems.append(f"{tool_file.name}: {tool_function!r} is not a function.")
                continue
            tool = TeamTool(tool_function, tool_file.name)
            if tool.name in seen_names:
                toolbox.problems.append(
                    f"{tool_file.name}: a tool named {tool.name} already exists."
                )
                continue
            seen_names.add(tool.name)
            toolbox.tools.append(tool)
    return toolbox
