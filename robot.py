"""The robot: your tools' ONLY way to sense and move in the game. Read this file first.

There is no game in this kit. When the AI plays, your instructor's program plugs in the real
robot; when you run ``python check_tools.py``, a pretend robot is plugged in. Either way your
tools do the same thing: ``robot = get_robot()``, then call the methods below.

Sensors (look without moving, free to use):
    robot.get_position()  -> (x, y)          x is the robot's LEFT edge, in pixels
    robot.is_on_ground()  -> True / False
    robot.get_status()    -> dict            stage, stages_total, x, y, alive, on_ground,
                                              death_reason, deaths, energy_left, energy_max
    robot.scan_terrain()  -> list of dicts   {"kind": "ground" | "gap" | "spikes",
                                              "left": int, "right": int}  (NOT sorted!)
                                             A "platform" also has "top": the y of its
                                             upper surface (a smaller y is higher up).
    robot.get_goal()      -> (left, right)   the flag's left and right edges

Motors (at most 2 per tool call):
    robot.walk(direction, steps)  -> dict    direction is "left" or "right";
                                             one step is Robot.WALK_SPEED (5) pixels
    robot.jump(direction)         -> dict    one whole jump, about JUMP_DISTANCE px long
    robot.restart_stage()         -> dict    back to the start of this stage after a death

Voice (once per tool call):
    robot.say(text)                          shows your robot's line on the big screen

Motor results look like {"event": "moved" | "landed" | "blocked" | "died" |
"stage_clear" | "level_complete", "moved_px": 50, "x": 110, "y": 410, "on_ground": True,
"alive": True, "death_reason": None, "stage": 1}.

The world: 1000 px wide; x grows to the right; the ground's surface is at y = 450. Facing
right, the robot's FRONT edge is x + 30; facing left, it is x. Some stages run right-to-left.

Anything impossible (a bad direction, moving while broken, no energy left) raises
``RobotError`` with a readable message. Catch it with try/except and turn it into a helpful
sentence for the AI: an uncaught error costs DOUBLE energy.
"""

from typing import Any

NOT_CONNECTED_MESSAGE = (
    "No robot is connected. There is no game in this kit: run your tools with "
    "`python check_tools.py` (pretend robot) or ask your instructor to plug them into the game."
)

active_robot: Any = None


class RobotError(Exception):
    """The robot cannot do what you asked. The message says why, in plain English."""


class Robot:
    """What every robot can do. The real one (and check_tools' pretend one) work like this."""

    WALK_SPEED = 5  # pixels per walking step
    PLAYER_WIDTH = 30  # the robot's body is 30 px wide; its front edge is x + 30 facing right
    JUMP_DISTANCE = 165  # how far one jump carries the robot sideways, in pixels
    MAX_STEPS = 200  # the most steps one walk() can take (200 x 5 = 1000 px)

    # Sensors -----------------------------------------------------------
    def get_position(self) -> tuple[int, int]:
        """Return (x, y): x is the robot's left edge; y grows downward."""
        raise RobotError(NOT_CONNECTED_MESSAGE)

    def is_on_ground(self) -> bool:
        """Return True if the robot is standing on something (not in the air)."""
        raise RobotError(NOT_CONNECTED_MESSAGE)

    def get_status(self) -> dict[str, Any]:
        """Return everything the robot knows about itself as a dictionary (see above)."""
        raise RobotError(NOT_CONNECTED_MESSAGE)

    def scan_terrain(self) -> list[dict[str, Any]]:
        """Return every ground segment, gap, spike strip and platform (absolute pixels)."""
        raise RobotError(NOT_CONNECTED_MESSAGE)

    def get_goal(self) -> tuple[int, int]:
        """Return the flag's (left edge, right edge). Touching the flag clears the stage."""
        raise RobotError(NOT_CONNECTED_MESSAGE)

    # Motors ------------------------------------------------------------
    def walk(self, direction: str, steps: int) -> dict[str, Any]:
        """Walk ``steps`` steps (5 px each) "left" or "right". Stops early on a fall or flag."""
        raise RobotError(NOT_CONNECTED_MESSAGE)

    def jump(self, direction: str) -> dict[str, Any]:
        """Do one whole jump toward "left" or "right"; returns when the robot lands (or dies)."""
        raise RobotError(NOT_CONNECTED_MESSAGE)

    def restart_stage(self) -> dict[str, Any]:
        """Put the robot back at the start of the current stage (use it after a death)."""
        raise RobotError(NOT_CONNECTED_MESSAGE)

    # Voice -------------------------------------------------------------
    def say(self, text: str) -> None:
        """Show a short line (up to 120 characters) from your robot on the big screen."""
        raise RobotError(NOT_CONNECTED_MESSAGE)


def get_robot() -> Robot:
    """Return the robot that is plugged in (the same one every time)."""
    if active_robot is None:
        raise RobotError(NOT_CONNECTED_MESSAGE)
    connected_robot: Robot = active_robot
    return connected_robot


def use_robot(robot: Any) -> None:
    """Plug in a robot: ``get_robot()`` returns it from now on (check_tools.py uses this)."""
    global active_robot
    active_robot = robot
