"""Check your team's tools before the AI model uses them.

    python check_tools.py                  every check, with hints
    python check_tools.py --role pilot     only one file's checks
    python check_tools.py --schema         exactly what the AI reads about each tool

Each tool is run against a pretend robot in made-up situations (a gap ahead, spikes
before a gap, a stage that runs right-to-left, a broken robot...) and every check
prints PASS or FAIL with a hint. No game, no AI and no network are needed.

Options:
    --role scout       only check one file (scout, pilot, jumper or coach)
    --schema           print each tool's name, description and input schema, then stop
    --tools FOLDER     check the tools in another folder (default: team_tools)
    --scenarios FILE   use different situations (the instructor's hidden checks)
    --json             print the results as JSON (for the instructor's grading)
"""

import argparse
import asyncio
import copy
import inspect
import json
import sys
import traceback
import typing
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Literal

import robot as robot_module
from mcp.server import MCPServer
from toolbox import TeamToolbox, load_team_tools

MAX_OUTPUT_LENGTH = 300
SCRIPT_DIRECTORY = Path(__file__).resolve().parent
TOOLS_FOLDER_NAME = "team_tools"
MIN_DESCRIPTION_LENGTH = 40
WORLD_WIDTH = 1000
ROLE_FILES = {
    "scout": "tools_scout.py",
    "pilot": "tools_pilot.py",
    "jumper": "tools_jumper.py",
    "coach": "tools_coach.py",
}
SAMPLE_TEXT_ARGUMENTS = {
    "direction": "right",
    "note": "stage 1: gap at x=400 is 100 px wide",
    "reason": "walked into the gap",
}
CLEAR_PATH_WORDS = ("clear", "no hazard", "nothing", "no gap", "no obstacle")

# Each situation: where the robot is, the flag, the terrain (deliberately NOT sorted), and
# under "expect" the answers a correct tool should give.
DEFAULT_SCENARIOS: dict[str, dict[str, Any]] = {
    "gap_ahead": {
        "x": 60,
        "goal": [880, 920],
        "expect": {
            "direction": "right",
            "front_edge": 90,
            "nearest_kind": "gap",
            "nearest_distance": 310,
            "nearest_width": 100,
            "edge_x_range": [365, 370],
        },
        "terrain": [
            {"kind": "ground", "left": 0, "right": 400},
            {"kind": "ground", "left": 500, "right": 1000},
            {"kind": "gap", "left": 400, "right": 500},
        ],
    },
    "at_gap_edge": {
        "x": 370,
        "goal": [880, 920],
        "terrain": [
            {"kind": "ground", "left": 0, "right": 400},
            {"kind": "ground", "left": 500, "right": 1000},
            {"kind": "gap", "left": 400, "right": 500},
        ],
    },
    "spikes_before_gap": {
        "x": 60,
        "goal": [880, 920],
        "expect": {
            "nearest_kind": "spikes",
            "nearest_distance": 130,
            "farther_kind": "gap",
            "edge_x_range": [185, 190],
        },
        "terrain": [
            {"kind": "ground", "left": 0, "right": 450},
            {"kind": "ground", "left": 580, "right": 1000},
            {"kind": "gap", "left": 450, "right": 580},
            {"kind": "spikes", "left": 220, "right": 300},
        ],
    },
    "at_spikes_edge": {
        "x": 270,
        "goal": [880, 920],
        "terrain": [
            {"kind": "ground", "left": 0, "right": 1000},
            {"kind": "spikes", "left": 300, "right": 380},
        ],
    },
    "leftward": {
        "x": 910,
        "goal": [40, 80],
        "expect": {
            "direction": "left",
            "front_edge": 910,
            "nearest_kind": "spikes",
            "nearest_distance": 210,
            "edge_x_range": [700, 705],
        },
        "terrain": [
            {"kind": "ground", "left": 0, "right": 330},
            {"kind": "ground", "left": 460, "right": 1000},
            {"kind": "gap", "left": 330, "right": 460},
            {"kind": "spikes", "left": 620, "right": 700},
        ],
    },
    "leftward_at_spikes_edge": {
        "x": 700,
        "goal": [40, 80],
        "terrain": [
            {"kind": "ground", "left": 0, "right": 330},
            {"kind": "ground", "left": 460, "right": 1000},
            {"kind": "gap", "left": 330, "right": 460},
            {"kind": "spikes", "left": 620, "right": 700},
        ],
    },
    "clear_path": {
        "x": 500,
        "goal": [880, 920],
        "terrain": [{"kind": "ground", "left": 0, "right": 1000}],
    },
    "too_wide": {
        "x": 370,
        "goal": [880, 920],
        "expect": {"nearest_width": 200},
        "terrain": [
            {"kind": "ground", "left": 0, "right": 400},
            {"kind": "ground", "left": 600, "right": 1000},
            {"kind": "gap", "left": 400, "right": 600},
        ],
    },
    "broken": {
        "x": 400,
        "y": 620,
        "alive": False,
        "on_ground": False,
        "death_reason": "fell_into_gap",
        "deaths": 1,
        "goal": [880, 920],
        "terrain": [
            {"kind": "ground", "left": 0, "right": 400},
            {"kind": "ground", "left": 500, "right": 1000},
            {"kind": "gap", "left": 400, "right": 500},
        ],
    },
    "in_air": {
        "x": 200,
        "y": 300,
        "on_ground": False,
        "goal": [880, 920],
        "terrain": [{"kind": "ground", "left": 0, "right": 1000}],
    },
    "busy_run": {
        "x": 60,
        "stage": 2,
        "stages_total": 3,
        "deaths": 2,
        "energy_left": 37,
        "energy_max": 50,
        "goal": [880, 920],
        "terrain": [{"kind": "ground", "left": 0, "right": 1000}],
    },
}


class FakeRobot:
    """A pretend robot with the same methods as the real one, for quick and safe checks.

    Its physics is simplified (a walk moves 5 px per step; a jump moves the robot exactly
    JUMP_DISTANCE px and only the landing spot matters), but the rules match the game.
    """

    WALK_SPEED = robot_module.Robot.WALK_SPEED
    PLAYER_WIDTH = robot_module.Robot.PLAYER_WIDTH
    JUMP_DISTANCE = robot_module.Robot.JUMP_DISTANCE
    MAX_STEPS = robot_module.Robot.MAX_STEPS

    def __init__(self, scenario: dict[str, Any]) -> None:
        """Set the robot up in ``scenario``."""
        self.start_x = scenario["x"]
        self.x = scenario["x"]
        self.y = scenario.get("y", 410)
        self.terrain = copy.deepcopy(scenario["terrain"])
        self.goal = tuple(scenario["goal"])
        self.is_alive = scenario.get("alive", True)
        self.on_ground = scenario.get("on_ground", True)
        self.death_reason = scenario.get("death_reason")
        self.stage = scenario.get("stage", 1)
        self.stages_total = scenario.get("stages_total", 1)
        self.deaths = scenario.get("deaths", 0)
        self.energy_left = scenario.get("energy_left", 50)
        self.energy_max = scenario.get("energy_max", 50)
        self.motor_calls: list[tuple[Any, ...]] = []
        self.events: list[str] = []
        self.said: list[str] = []

    # Sensors ------------------------------------------------------------
    def get_position(self) -> tuple[int, int]:
        """Return (x, y)."""
        position = (self.x, self.y)
        return position

    def is_on_ground(self) -> bool:
        """Return True when standing."""
        on_ground: bool = self.on_ground
        return on_ground

    def get_status(self) -> dict[str, Any]:
        """Return the status dictionary, shaped like the real robot's."""
        status = {
            "stage": self.stage,
            "stages_total": self.stages_total,
            "x": self.x,
            "y": self.y,
            "on_ground": self.on_ground,
            "alive": self.is_alive,
            "death_reason": self.death_reason,
            "level_complete": False,
            "deaths": self.deaths,
            "energy_left": self.energy_left,
            "energy_max": self.energy_max,
        }
        return status

    def scan_terrain(self) -> list[dict[str, Any]]:
        """Return a copy of the terrain (so a tool cannot change the scenario)."""
        terrain: list[dict[str, Any]] = copy.deepcopy(self.terrain)
        return terrain

    def get_goal(self) -> tuple[int, int]:
        """Return the flag's (left, right)."""
        goal = (self.goal[0], self.goal[1])
        return goal

    # Motors -------------------------------------------------------------
    def walk(self, direction: str, steps: int) -> dict[str, Any]:
        """Walk step by step, stopping on a death, the flag or the world edge."""
        sign = self._check_motor(direction)
        if (
            not isinstance(steps, int)
            or isinstance(steps, bool)
            or not 0 <= steps <= self.MAX_STEPS
        ):
            raise robot_module.RobotError(
                f"steps must be a whole number from 0 to {self.MAX_STEPS}."
            )
        self.motor_calls.append(("walk", direction, steps))
        start_x = self.x
        event = "moved"
        for _ in range(steps):
            next_x = self.x + sign * self.WALK_SPEED
            if not 0 <= next_x <= WORLD_WIDTH - self.PLAYER_WIDTH:
                event = "blocked"
                break
            self.x = next_x
            event = self._check_position(default_event="moved")
            if event != "moved":
                break
        motion_result = self._motion_result(event, abs(self.x - start_x))
        return motion_result

    def jump(self, direction: str) -> dict[str, Any]:
        """Jump exactly JUMP_DISTANCE px; only the landing spot (and the flag) matter."""
        sign = self._check_motor(direction)
        if not self.on_ground:
            raise robot_module.RobotError("Cannot jump while in the air.")
        self.motor_calls.append(("jump", direction))
        start_x = self.x
        landing_x = max(0, min(WORLD_WIDTH - self.PLAYER_WIDTH, self.x + sign * self.JUMP_DISTANCE))
        passes_flag = (
            min(start_x, landing_x) <= self.goal[1]
            and self.goal[0] <= max(start_x, landing_x) + self.PLAYER_WIDTH
        )
        self.x = landing_x
        event = "stage_clear" if passes_flag else self._check_position(default_event="landed")
        if event == "stage_clear":
            self.events.append(event)
        motion_result = self._motion_result(event, abs(self.x - start_x))
        return motion_result

    def restart_stage(self) -> dict[str, Any]:
        """Bring the robot back to life at its starting x."""
        self.motor_calls.append(("restart_stage",))
        self.is_alive = True
        self.on_ground = True
        self.death_reason = None
        self.x = self.start_x
        restart_result = {"event": "stage_restart", "stage": self.stage, "x": self.x}
        return restart_result

    def say(self, text: str) -> None:
        """Remember what the robot said."""
        self.said.append(str(text))

    # Helpers ------------------------------------------------------------
    def _check_motor(self, direction: Any) -> int:
        """Refuse a motor command like the real robot does; return +1 or -1."""
        if direction not in ("left", "right"):
            raise robot_module.RobotError(
                f"Invalid direction {direction!r}. Only 'left' and 'right' are valid."
            )
        if not self.is_alive:
            raise robot_module.RobotError(
                f"The robot is broken ({self.death_reason}). Call restart_stage() first."
            )
        sign = 1 if direction == "right" else -1
        return sign

    def _check_position(self, default_event: str) -> str:
        """Work out what happens at the robot's current x: fall, spikes, flag, or nothing."""
        body_left = self.x
        body_right = self.x + self.PLAYER_WIDTH
        is_supported = any(
            piece["kind"] == "ground" and body_left < piece["right"] and piece["left"] < body_right
            for piece in self.terrain
        )
        touches_spikes = any(
            piece["kind"] == "spikes" and body_left < piece["right"] and piece["left"] < body_right
            for piece in self.terrain
        )
        if not is_supported:
            event = self._die("fell_into_gap")
        elif touches_spikes:
            event = self._die("hit_spikes")
        elif body_right >= self.goal[0] and body_left <= self.goal[1]:
            event = "stage_clear"
            self.events.append(event)
        else:
            event = default_event
        return event

    def _die(self, reason: str) -> str:
        """Break the robot."""
        self.is_alive = False
        self.on_ground = False
        self.death_reason = reason
        self.deaths += 1
        self.events.append("died")
        event = "died"
        return event

    def _motion_result(self, event: str, moved_px: int) -> dict[str, Any]:
        """Build a motor result shaped like the real robot's."""
        motion_result = {
            "event": event,
            "moved_px": moved_px,
            "x": self.x,
            "y": self.y,
            "on_ground": self.on_ground,
            "alive": self.is_alive,
            "death_reason": self.death_reason,
            "stage": self.stage + (1 if event == "stage_clear" else 0),
        }
        return motion_result


@dataclass
class ToolRun:
    """What happened when a tool was called in a situation."""

    output: Any
    crash: str
    robot: FakeRobot


@dataclass
class CheckResult:
    """One PASS/FAIL line."""

    role: str
    description: str
    passed: bool
    hint: str = ""


@dataclass
class Checker:
    """Runs the checks for one team and collects the results."""

    toolbox: TeamToolbox
    scenarios: dict[str, dict[str, Any]]
    results: list[CheckResult] = field(default_factory=list)

    def tool(self, role: str, tool_name: str) -> Callable[..., Any] | None:
        """Find a tool by name in a role's file (None, plus a FAIL line, if it is missing)."""
        for team_tool in self.toolbox.tools:
            if team_tool.name == tool_name and team_tool.file_name == ROLE_FILES[role]:
                return team_tool.function
        self.record(role, f"{tool_name} is listed in TOOLS", False, f"Add {tool_name} to TOOLS.")
        return None

    def expected(self, scenario_name: str) -> dict[str, Any]:
        """Return the answers a correct tool should give in ``scenario_name``."""
        expected_answers: dict[str, Any] = self.scenarios[scenario_name].get("expect", {})
        return expected_answers

    def situation(self, scenario_name: str) -> str:
        """Describe a scenario in one line for hints: robot x, flag and hazards."""
        scenario = self.scenarios[scenario_name]
        hazards = [
            f"{piece['kind']} {piece['left']}..{piece['right']}"
            for piece in scenario["terrain"]
            if piece["kind"] in ("gap", "spikes")
        ]
        hazards_text = ", ".join(hazards) if hazards else "no hazards"
        flag_left, flag_right = scenario["goal"]
        description = (
            f"Robot x={scenario['x']} (30 px wide), flag {flag_left}..{flag_right}, {hazards_text}."
        )
        return description

    def helper(self, role: str, helper_name: str) -> Callable[..., Any] | None:
        """Find a helper function (not a tool) in a role's module, or None."""
        module = self.toolbox.modules.get(Path(ROLE_FILES[role]).stem)
        helper_function = getattr(module, helper_name, None) if module is not None else None
        return helper_function

    def run(self, function: Callable[..., Any], scenario_name: str, *arguments: Any) -> ToolRun:
        """Call ``function`` with a fresh pretend robot in ``scenario_name``; never raises."""
        fake_robot = FakeRobot(self.scenarios[scenario_name])
        robot_module.use_robot(fake_robot)
        try:
            output = function(*arguments)
            crash = ""
        except Exception as error:  # a crash is exactly what we want to report
            output = None
            crash = f"{type(error).__name__}: {error}"
        tool_run = ToolRun(output, crash, fake_robot)
        return tool_run

    def record(self, role: str, description: str, passed: bool, hint: str = "") -> None:
        """Store one result."""
        self.results.append(CheckResult(role, description, passed, "" if passed else hint))

    def expect(
        self, role: str, description: str, tool_run: ToolRun, condition: bool, hint: str
    ) -> None:
        """Record a check that also fails if the tool crashed or did not return text."""
        if tool_run.crash:
            self.record(role, description, False, f"It crashed: {tool_run.crash}")
            return
        if not isinstance(tool_run.output, str):
            self.record(role, description, False, "It must return a string (text).")
            return
        self.record(role, description, condition, f"{hint} It returned: {tool_run.output!r}")


def text_of(tool_run: ToolRun) -> str:
    """Return the tool's output in lower case (empty if it was not text)."""
    output_text = tool_run.output.lower() if isinstance(tool_run.output, str) else ""
    return output_text


def sample_value(parameter_name: str, annotation: Any) -> Any:
    """Make up one sensible input from a parameter's name and type hint.

    Understands plain types, Literal[...] (uses the first allowed value) and
    Annotated[...] (uses the inner type). Example: Literal["left", "right"] -> "left";
    Annotated[int, Field(ge=0)] -> 50; a parameter called "direction" -> "right".
    """
    if typing.get_origin(annotation) is Annotated:
        inner_type = typing.get_args(annotation)[0]
        inner_value = sample_value(parameter_name, inner_type)
        return inner_value
    if typing.get_origin(annotation) is Literal:
        first_allowed_value = typing.get_args(annotation)[0]
        return first_allowed_value
    if annotation is int:
        return 50
    if annotation is float:
        return 50.0
    if annotation is bool:
        return True
    text_value = SAMPLE_TEXT_ARGUMENTS.get(parameter_name, "test")
    return text_value


def sample_arguments(function: Callable[..., Any]) -> list[Any]:
    """Make up sensible inputs for a tool from its parameter names and type hints."""
    try:
        hints = typing.get_type_hints(function, include_extras=True)
    except Exception:  # a broken hint is reported by its own check; still try the tool
        hints = {}
    arguments = [
        sample_value(parameter.name, hints.get(parameter.name, parameter.annotation))
        for parameter in inspect.signature(function).parameters.values()
    ]
    return arguments


def check_every_tool(checker: Checker) -> None:
    """Run the checks that apply to every tool: description, hints, length, no crashes."""
    file_to_role = {file_name: role for role, file_name in ROLE_FILES.items()}
    for team_tool in checker.toolbox.tools:
        role = file_to_role.get(team_tool.file_name, team_tool.file_name)
        name = team_tool.name
        description = inspect.getdoc(team_tool.function) or ""
        has_description = len(description) >= MIN_DESCRIPTION_LENGTH and "TODO" not in description
        checker.record(
            role,
            f"{name}: has a real description for the model",
            has_description,
            f"Write a docstring of at least {MIN_DESCRIPTION_LENGTH} characters (no TODO) "
            "that says what the tool does and when to use it.",
        )
        parameters = inspect.signature(team_tool.function).parameters.values()
        has_hints = all(
            parameter.annotation is not inspect.Parameter.empty for parameter in parameters
        )
        checker.record(
            role,
            f"{name}: every input has a type hint",
            has_hints,
            "Add type hints (e.g. direction: str, distance: int): they become the tool's schema.",
        )
        arguments = sample_arguments(team_tool.function)
        normal_run = checker.run(team_tool.function, "gap_ahead", *arguments)
        is_short = (
            isinstance(normal_run.output, str) and len(normal_run.output) <= MAX_OUTPUT_LENGTH
        )
        checker.expect(
            role,
            f"{name}: returns text of at most {MAX_OUTPUT_LENGTH} characters",
            normal_run,
            is_short,
            "Keep answers short: the model pays attention to short, clear facts.",
        )
        broken_run = checker.run(team_tool.function, "broken", *arguments)
        checker.expect(
            role,
            f"{name}: does not crash when the robot is broken",
            broken_run,
            True,
            "Catch RobotError and explain the problem in the returned text.",
        )


def check_scout(checker: Checker) -> None:
    """Run the checks for the Scout's survey helper, look_ahead and where_am_i."""
    survey = checker.helper("scout", "survey")
    if survey is not None:
        survey_cases = [
            ("gap_ahead", "survey(): finds the hazard ahead, measured from the front edge"),
            ("spikes_before_gap", "survey(): lists the NEAREST obstacle first"),
            ("leftward", "survey(): works on a stage that runs right-to-left"),
        ]
        for scenario_name, description in survey_cases:
            expected = checker.expected(scenario_name)
            survey_run = checker.run(survey, scenario_name)
            surroundings = survey_run.output if isinstance(survey_run.output, dict) else {}
            first_obstacle = (surroundings.get("obstacles") or [{}])[0]
            is_correct = (
                not survey_run.crash
                and surroundings.get("direction", "right") == expected.get("direction", "right")
                and surroundings.get("front_edge")
                == expected.get("front_edge", surroundings.get("front_edge"))
                and first_obstacle.get("kind") == expected["nearest_kind"]
                and first_obstacle.get("distance") == expected["nearest_distance"]
            )
            checker.record(
                "scout",
                description,
                is_correct,
                f"{checker.situation(scenario_name)} Expected the nearest obstacle to be "
                f"{expected['nearest_kind']} {expected['nearest_distance']} px ahead. "
                "The front edge faces the flag; scan_terrain() is not sorted. "
                f"Got: {survey_run.output!r}",
            )

    look_ahead = checker.tool("scout", "look_ahead")
    if look_ahead is not None:
        gap_expected = checker.expected("gap_ahead")
        gap_run = checker.run(look_ahead, "gap_ahead")
        checker.expect(
            "scout",
            "look_ahead: names the hazard ahead and its distance",
            gap_run,
            gap_expected["nearest_kind"][:3] in text_of(gap_run)
            and str(gap_expected["nearest_distance"]) in text_of(gap_run),
            f"{checker.situation('gap_ahead')} The {gap_expected['nearest_kind']} is "
            f"{gap_expected['nearest_distance']} px from the front edge.",
        )
        order_expected = checker.expected("spikes_before_gap")
        order_run = checker.run(look_ahead, "spikes_before_gap")
        order_text = text_of(order_run)
        nearest_position = order_text.find(order_expected["nearest_kind"][:3])
        farther_position = order_text.find(order_expected["farther_kind"][:3])
        checker.expect(
            "scout",
            "look_ahead: names the nearest hazard first",
            order_run,
            str(order_expected["nearest_distance"]) in order_text
            and 0 <= nearest_position < farther_position,
            f"{checker.situation('spikes_before_gap')} Nearest first: the "
            f"{order_expected['nearest_kind']} ({order_expected['nearest_distance']} px).",
        )
        left_expected = checker.expected("leftward")
        left_run = checker.run(look_ahead, "leftward")
        checker.expect(
            "scout",
            "look_ahead: works when the flag is to the left",
            left_run,
            str(left_expected["nearest_distance"]) in text_of(left_run)
            and "left" in text_of(left_run),
            f"{checker.situation('leftward')} The {left_expected['nearest_kind']} is "
            f"{left_expected['nearest_distance']} px to the left.",
        )
        clear_run = checker.run(look_ahead, "clear_path")
        checker.expect(
            "scout",
            "look_ahead: says when the path to the flag is clear",
            clear_run,
            any(word in text_of(clear_run) for word in CLEAR_PATH_WORDS),
            'With no hazards ahead, say so (e.g. "clear path").',
        )

    where_am_i = checker.tool("scout", "where_am_i")
    if where_am_i is not None:
        busy_scenario = checker.scenarios["busy_run"]
        where_run = checker.run(where_am_i, "busy_run")
        checker.expect(
            "scout",
            "where_am_i: reports the stage, x and progress in %",
            where_run,
            str(busy_scenario["stage"]) in text_of(where_run)
            and str(busy_scenario["x"]) in text_of(where_run)
            and "%" in text_of(where_run),
            f"Include the stage ({busy_scenario['stage']}), the x position ({busy_scenario['x']}) "
            "and a progress percentage.",
        )
        broken_run = checker.run(where_am_i, "broken")
        broken_text = text_of(broken_run)
        checker.expect(
            "scout",
            "where_am_i: says when the robot is broken",
            broken_run,
            any(word in broken_text for word in ("broke", "fell", "dead", "died")),
            "A broken robot must be restarted; the model needs to know.",
        )


def check_pilot(checker: Checker) -> None:
    """Run the checks for the Pilot's helper, walk, walk_to_next_edge and walk_to_flag."""
    clean_direction = checker.helper("pilot", "clean_direction")
    if clean_direction is not None:
        cleaned = [clean_direction(" Right"), clean_direction("L"), clean_direction("up")]
        checker.record(
            "pilot",
            'clean_direction(): " Right" -> "right", "L" -> "left", "up" -> None',
            cleaned == ["right", "left", None],
            f"Strip spaces, use lower case, accept short forms. Got: {cleaned!r}",
        )

    walk = checker.tool("pilot", "walk")
    if walk is not None:
        right_run = checker.run(walk, "gap_ahead", " Right", 50)
        checker.expect(
            "pilot",
            'walk(" Right", 50): walks 10 steps right',
            right_run,
            right_run.robot.motor_calls == [("walk", "right", 10)],
            f"50 px is 10 steps of 5 px. Robot calls: {right_run.robot.motor_calls!r}.",
        )
        up_run = checker.run(walk, "gap_ahead", "up", 50)
        checker.expect(
            "pilot",
            'walk("up", 50): refuses without moving and names the valid directions',
            up_run,
            not up_run.robot.motor_calls
            and "left" in text_of(up_run)
            and "right" in text_of(up_run),
            "Do not call the robot with a bad direction; explain the valid ones.",
        )
        too_far_run = checker.run(walk, "gap_ahead", "right", 5000)
        negative_run = checker.run(walk, "gap_ahead", "right", -5)
        checker.expect(
            "pilot",
            "walk: refuses distances below 0 or above 1000 without moving",
            too_far_run,
            not too_far_run.robot.motor_calls and not negative_run.robot.motor_calls,
            "Check the distance before moving.",
        )

    walk_to_next_edge = checker.tool("pilot", "walk_to_next_edge")
    if walk_to_next_edge is not None:
        edge_cases = [
            ("gap_ahead", "the nearest hazard"),
            ("spikes_before_gap", "the nearest of two hazards"),
            ("leftward", "the nearest hazard on a right-to-left stage"),
        ]
        for scenario_name, hazard_text in edge_cases:
            lowest_x, highest_x = checker.expected(scenario_name)["edge_x_range"]
            edge_run = checker.run(walk_to_next_edge, scenario_name)
            fake_robot = edge_run.robot
            checker.expect(
                "pilot",
                f"walk_to_next_edge: stops 0-5 px before {hazard_text}",
                edge_run,
                fake_robot.is_alive and lowest_x <= fake_robot.x <= highest_x,
                f"{checker.situation(scenario_name)} Expected the robot's x to end between "
                f"{lowest_x} and {highest_x}; it ended at x={fake_robot.x}"
                f"{'' if fake_robot.is_alive else ' (broken!)'}. The robot is 30 px wide.",
            )

    walk_to_flag = checker.tool("pilot", "walk_to_flag")
    if walk_to_flag is not None:
        blocked_run = checker.run(walk_to_flag, "gap_ahead")
        checker.expect(
            "pilot",
            "walk_to_flag: refuses (without moving) when a gap is in the way, and names it",
            blocked_run,
            not blocked_run.robot.motor_calls and "gap" in text_of(blocked_run),
            "Check survey() for obstacles before walking.",
        )
        clear_run = checker.run(walk_to_flag, "clear_path")
        checker.expect(
            "pilot",
            "walk_to_flag: reaches the flag when the path is clear",
            clear_run,
            "stage_clear" in clear_run.robot.events,
            "Walk far enough for the front edge to TOUCH the flag (round the steps up).",
        )


def check_jumper(checker: Checker) -> None:
    """Run the checks for the Jumper's jump and jump_over_next_obstacle."""
    jump = checker.tool("jumper", "jump")
    if jump is not None:
        jump_run = checker.run(jump, "at_gap_edge", " RIGHT")
        checker.expect(
            "jumper",
            'jump(" RIGHT"): cleans up the direction and jumps',
            jump_run,
            jump_run.robot.motor_calls == [("jump", "right")],
            f"Robot calls: {jump_run.robot.motor_calls!r}.",
        )
        air_run = checker.run(jump, "in_air", "right")
        checker.expect(
            "jumper",
            "jump: explains (without crashing) that it cannot jump in the air",
            air_run,
            not air_run.robot.motor_calls and "air" in text_of(air_run),
            "Check robot.get_status()['on_ground'] first, or catch RobotError.",
        )

    jump_over = checker.tool("jumper", "jump_over_next_obstacle")
    if jump_over is not None:
        safe_cases = [
            ("at_gap_edge", "a gap at its edge"),
            ("at_spikes_edge", "spikes at their edge"),
            ("leftward_at_spikes_edge", "spikes on a right-to-left stage"),
        ]
        for scenario_name, hazard_text in safe_cases:
            safe_run = checker.run(jump_over, scenario_name)
            checker.expect(
                "jumper",
                f"jump_over_next_obstacle: clears {hazard_text}",
                safe_run,
                len(safe_run.robot.motor_calls) == 1
                and safe_run.robot.motor_calls[0][0] == "jump"
                and safe_run.robot.is_alive,
                f"Robot calls: {safe_run.robot.motor_calls!r}, alive: {safe_run.robot.is_alive}.",
            )
        refuse_cases = [
            ("gap_ahead", "the hazard is still far away"),
            ("too_wide", "the gap is too wide to clear"),
            ("clear_path", "there is nothing to jump over"),
        ]
        for scenario_name, reason_text in refuse_cases:
            refuse_run = checker.run(jump_over, scenario_name)
            checker.expect(
                "jumper",
                f"jump_over_next_obstacle: refuses when {reason_text}",
                refuse_run,
                not refuse_run.robot.motor_calls,
                f"Robot calls: {refuse_run.robot.motor_calls!r}. Explain instead of jumping.",
            )


def check_coach(checker: Checker) -> None:
    """Run the checks for the Coach's remember, recall, restart_stage and get_status."""
    remember = checker.tool("coach", "remember")
    recall = checker.tool("coach", "recall")
    if remember is not None and recall is not None:
        checker.run(remember, "gap_ahead", "gap at 400 is 100 px wide")
        recall_run = checker.run(recall, "gap_ahead")
        checker.expect(
            "coach",
            "remember + recall: a saved note comes back",
            recall_run,
            "gap at 400 is 100 px wide" in text_of(recall_run),
            "recall() should show the latest notes.",
        )
        for note_number in range(25):
            checker.run(remember, "gap_ahead", f"note number {note_number} " + "x" * 120)
        long_recall_run = checker.run(recall, "gap_ahead")
        checker.expect(
            "coach",
            "recall: stays within 300 characters even with many long notes",
            long_recall_run,
            isinstance(long_recall_run.output, str)
            and len(long_recall_run.output) <= MAX_OUTPUT_LENGTH,
            "Limit how many notes you show and how long each one is.",
        )

    restart_stage = checker.tool("coach", "restart_stage")
    if restart_stage is not None:
        alive_run = checker.run(restart_stage, "gap_ahead", "testing")
        checker.expect(
            "coach",
            "restart_stage: does not restart a robot that is fine",
            alive_run,
            ("restart_stage",) not in alive_run.robot.motor_calls,
            "Check robot.get_status()['alive'] first: restarting throws away progress.",
        )
        broken_run = checker.run(restart_stage, "broken", "walked into the gap")
        checker.expect(
            "coach",
            "restart_stage: restarts a broken robot",
            broken_run,
            ("restart_stage",) in broken_run.robot.motor_calls and broken_run.robot.is_alive,
            f"Robot calls: {broken_run.robot.motor_calls!r}.",
        )

    get_status = checker.tool("coach", "get_status")
    if get_status is not None:
        busy_scenario = checker.scenarios["busy_run"]
        status_run = checker.run(get_status, "busy_run")
        checker.expect(
            "coach",
            "get_status: shows the deaths and the energy left",
            status_run,
            str(busy_scenario["deaths"]) in text_of(status_run)
            and str(busy_scenario["energy_left"]) in text_of(status_run),
            f"Include the number of deaths ({busy_scenario['deaths']}) and the energy left "
            f"({busy_scenario['energy_left']}).",
        )


ROLE_CHECKS = {
    "scout": check_scout,
    "pilot": check_pilot,
    "jumper": check_jumper,
    "coach": check_coach,
}


def run_checks(toolbox: TeamToolbox, scenarios: dict[str, Any], role: str | None) -> Checker:
    """Run every check (or one role's checks) and return the checker with its results."""
    checker = Checker(toolbox, scenarios)
    for problem in toolbox.problems:
        checker.record("loading", problem, False, "Fix this so the file loads.")
    check_every_tool(checker)
    for role_name, role_check in ROLE_CHECKS.items():
        if role is None or role == role_name:
            role_check(checker)
    if role is not None:
        checker.results = [result for result in checker.results if result.role == role]
    return checker


def print_report(checker: Checker) -> None:
    """Print the results grouped by role, with a summary line per role."""
    roles = list(dict.fromkeys(result.role for result in checker.results))
    for role in roles:
        role_results = [result for result in checker.results if result.role == role]
        passed_count = sum(result.passed for result in role_results)
        print(f"\n== {role.upper()}  ({passed_count}/{len(role_results)} passed)")
        for result in role_results:
            mark = "PASS" if result.passed else "FAIL"
            print(f"  {mark}  {result.description}")
            if not result.passed and result.hint:
                print(f"        hint: {result.hint}")
    total_passed = sum(result.passed for result in checker.results)
    print(f"\nTOTAL: {total_passed}/{len(checker.results)} checks passed.")


def results_as_json(checker: Checker) -> str:
    """Return the results as JSON: per-role passed/total counts plus every check."""
    roles: dict[str, dict[str, int]] = {}
    for result in checker.results:
        role_counts = roles.setdefault(result.role, {"passed": 0, "total": 0})
        role_counts["total"] += 1
        role_counts["passed"] += int(result.passed)
    report = {
        "roles": roles,
        "checks": [result.__dict__ for result in checker.results],
    }
    report_text = json.dumps(report, indent=2)
    return report_text


def default_tools_directory() -> Path:
    """Find team_tools/: next to this file (student kit) or one folder up (instructor kit)."""
    for folder in (SCRIPT_DIRECTORY, SCRIPT_DIRECTORY.parent):
        candidate = folder / TOOLS_FOLDER_NAME
        if candidate.is_dir():
            return candidate
    fallback_directory = SCRIPT_DIRECTORY / TOOLS_FOLDER_NAME
    return fallback_directory


async def print_schemas(toolbox: TeamToolbox) -> None:
    """Print each tool exactly as an MCP server describes it to the AI."""
    for team_tool in toolbox.tools:
        # A fresh server per tool, so one broken annotation cannot hide the others.
        server = MCPServer("schema-preview")
        try:
            server.tool()(team_tool.function)
            listed_tool = (await server.list_tools())[0]
        except Exception as error:
            print(f"\nTOOL {team_tool.name}: cannot be turned into an MCP tool: {error}")
            continue
        print(f"\nTOOL {listed_tool.name}   ({team_tool.file_name})")
        print(f"  inputs: {json.dumps(listed_tool.input_schema)}")
        for line in (listed_tool.description or "(no description!)").splitlines():
            print(f"  | {line}")


def main() -> None:
    """Read the options, load the tools and run the checks."""
    parser = argparse.ArgumentParser(description="Check your team's tools.")
    parser.add_argument("--role", choices=sorted(ROLE_FILES), default=None)
    parser.add_argument("--schema", action="store_true", help="show what the AI reads, then stop")
    parser.add_argument("--tools", type=Path, default=default_tools_directory())
    parser.add_argument("--scenarios", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()

    if arguments.schema:
        schema_toolbox = load_team_tools(arguments.tools)
        for problem in schema_toolbox.problems:
            print(f"WARNING: {problem}")
        asyncio.run(print_schemas(schema_toolbox))
        return
    scenarios = DEFAULT_SCENARIOS
    if arguments.scenarios is not None:
        scenarios = json.loads(arguments.scenarios.read_text(encoding="utf-8"))
    toolbox = load_team_tools(arguments.tools)
    try:
        checker = run_checks(toolbox, scenarios, arguments.role)
    except Exception:
        traceback.print_exc()
        sys.exit("check_tools.py itself crashed; tell your instructor.")
    if arguments.json:
        print(results_as_json(checker))
    else:
        print_report(checker)


if __name__ == "__main__":
    main()
