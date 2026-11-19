"""Pilot tools: the robot's LEGS. Safe, precise walking.

Owner: <your name here>

In this file:
    clean_direction()    helper (not a tool)  works in a simple form; you finish TODO 1
    describe_motion()    helper (not a tool)  works in a simple form; you finish TODO 2
    walk()               TOOL                 WORKED EXAMPLE: read it first (annotations!)
    walk_to_next_edge()  TOOL                 you build it (TODO 3)
    walk_to_flag()       TOOL                 you build it (TODO 4)

Useful facts: one walking step is Robot.WALK_SPEED (5) pixels, the robot is
Robot.PLAYER_WIDTH (30) pixels wide, a walk can take at most Robot.MAX_STEPS (200) steps,
and survey() from tools_scout tells you the direction to the flag and the obstacles ahead.

Check your work with:
    python check_tools.py --role pilot      (does it work?)
    python check_tools.py --schema          (what does the AI read?)
"""

import math
from typing import Annotated, Any, Literal

from pydantic import Field
from robot import Robot, RobotError, get_robot
from tools_scout import hazard_name, survey

MAX_WALK_DISTANCE = 1000  # the world is 1000 px wide, so a longer walk is never useful


def clean_direction(direction: str) -> str | None:
    """Turn what was typed into "left" or "right", or None if it makes no sense.

    A helper for the team, not a tool. Example: " Right" -> "right", "L" -> "left", "up" -> None.
    """
    # SPEC
    #   Inputs:  direction (str): whatever was typed, e.g. " Right", "RIGHT", "r", "up"
    #   Returns: "left", "right", or None when it is not a direction
    # TODO (Pilot) 1: clean up the text and accept a few short forms.
    # Hint: direction.strip().lower() removes spaces and capitals.
    # Hint: a dictionary of aliases works nicely: {"r": "right", "l": "left", ...}.
    if direction in ("left", "right"):
        return direction
    return None


def describe_motion(result: dict[str, Any], verb: str) -> str:
    """Turn a robot motor result into one sentence (a helper for the team, not a tool).

    Example: {"event": "moved", "moved_px": 50, "x": 110, ...}, "Walked right" ->
        "Walked right 50 px. Now at x=110."
    """
    # SPEC
    #   Inputs:  result (dict): what robot.walk/jump returned (see robot.py)
    #            verb (str):    the start of the sentence, e.g. "Walked right"
    #   Returns: one sentence describing what happened, for each event:
    #              moved / landed:  "Walked right 50 px. Now at x=110."
    #              blocked:         "Walked left 20 px and bumped into the edge of the world."
    #              died:            "Walked right 290 px, then the robot broke (fell_into_gap).
    #                                It must be restarted with restart_stage."
    #              stage_clear:     "... reached the flag! Now on stage 2."
    #              level_complete:  "... reached the final flag. LEVEL COMPLETE!"
    event = result["event"]
    moved_px = result["moved_px"]
    if event == "died":
        sentence = f"{verb} {moved_px} px, then the robot broke ({result['death_reason']})."
    elif event == "stage_clear":
        sentence = f"{verb} {moved_px} px and reached the flag! Now on stage {result['stage']}."
    elif event == "level_complete":
        sentence = f"{verb} {moved_px} px and reached the final flag. LEVEL COMPLETE!"
    else:
        sentence = f"{verb} {moved_px} px. Now at x={result['x']}."
    # TODO (Pilot) 2: give the "blocked" event its own sentence, and after a death tell the
    # AI the robot must be restarted (name the tool that does it, so the AI knows what to call).
    return sentence


def walk(
    direction: Literal["left", "right"],
    distance: Annotated[
        int, Field(ge=0, le=MAX_WALK_DISTANCE, description="How far to walk, in pixels.")
    ],
) -> str:
    """Walk the robot "left" or "right" by `distance` pixels (a whole number from 0 to 1000).

    The walk stops early if the robot reaches the flag, hits the edge of the world, or falls.
    Walking into a gap or onto spikes breaks the robot. Example: walk("right", 120).
    """
    # SPEC
    #   What it does: walks a given number of pixels in one direction.
    #   Inputs:       direction: "left" or "right"   (Literal: the AI can send nothing else)
    #                 distance:  whole number of pixels, 0 to 1000   (Annotated + Field)
    #   Returns:      e.g. "Walked right 120 px. Now at x=180."
    #   Refuses when: the direction or distance is invalid (returns why; does not move)
    #
    # WORKED EXAMPLE: annotated inputs, check the input anyway, move, describe what happened.
    # (The MCP server already rejects bad values, but check_tools.py calls this function
    # directly, and a careful tool never trusts its inputs.)
    clean = clean_direction(direction)
    if clean is None:
        message = f'Not moving: direction {direction!r} is not valid. Use "left" or "right".'
        return message
    if not isinstance(distance, int) or not 0 <= distance <= MAX_WALK_DISTANCE:
        message = f"Not moving: distance must be a whole number from 0 to {MAX_WALK_DISTANCE}."
        return message
    steps = distance // Robot.WALK_SPEED
    try:
        result = get_robot().walk(clean, steps)
    except RobotError as error:
        message = f"Could not walk: {error}"
        return message
    sentence = describe_motion(result, f"Walked {clean}")
    return sentence


def walk_to_next_edge() -> str:
    """TODO (Pilot): replace this line with the description the AI will read."""
    # SPEC
    #   What it does: walks toward the flag and stops 0-5 px before the nearest gap or spike
    #                 strip, so the robot is ready to jump.
    #   Inputs:       none
    #   Returns:      e.g. "Walked right 260 px. Now at x=320. Stopped 0 px before a gap
    #                       100 px wide."
    #   Refuses when: nothing is in the way: "Not moving: no gaps or spikes ahead. The path
    #                 to the flag is clear."   (does not move)
    #   Uses:         survey(), hazard_name(), get_robot().walk(), describe_motion()
    #
    # TODO (Pilot) 3a: build it to the spec.
    # TODO (Pilot) 3b: write the docstring the AI reads (where it stops, why, and when it refuses).
    # Hint: survey()["obstacles"][0]["distance"] is the pixels to the nearest hazard.
    # Hint: steps = distance // Robot.WALK_SPEED never overshoots (it rounds DOWN).
    # Hint: a walk takes at most Robot.MAX_STEPS steps; for longer distances use two walks
    #       (a tool may move the robot at most twice per call).
    # Hint: walking left works the same way; survey()["direction"] tells you which way.
    message = "TODO: walk_to_next_edge is not built yet."
    return message


def walk_to_flag() -> str:
    """TODO (Pilot): replace this line with the description the AI will read."""
    # SPEC
    #   What it does: walks all the way to the flag when nothing dangerous is in the way.
    #   Inputs:       none
    #   Returns:      e.g. "Walked right 315 px and reached the flag! Now on stage 2."
    #   Refuses when: a hazard is between the robot and the flag:
    #                 "Not moving: a gap 100 px wide is 260 px ahead, before the flag."
    #                 (does not move)
    #   Uses:         survey(), hazard_name(), get_robot().walk(), describe_motion(), math.ceil
    #
    # TODO (Pilot) 4a: build it to the spec.
    # TODO (Pilot) 4b: write the docstring the AI reads.
    # Hint: round the steps UP so the front edge reaches the flag:
    #       math.ceil(flag_distance / Robot.WALK_SPEED).
    message = "TODO: walk_to_flag is not built yet."
    return message


TOOLS = [walk, walk_to_next_edge, walk_to_flag]
