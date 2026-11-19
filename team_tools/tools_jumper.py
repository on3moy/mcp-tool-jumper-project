"""Jumper tools: getting over gaps and spikes safely.

Owner: <your name here>

In this file:
    jump()                     TOOL   worked example; you finish TODO 1 (annotation + safety)
    jump_over_next_obstacle()  TOOL   you build it (TODO 2)

Jump facts:
* one jump carries the robot Robot.JUMP_DISTANCE (165) pixels sideways;
* a GAP is cleared if the robot's front edge lands past the far side of the gap;
* SPIKES are cleared only if the robot's WHOLE body (Robot.PLAYER_WIDTH = 30 px)
  lands past the spikes, so spikes need more room than a gap of the same width;
* the robot can only jump while standing on the ground (robot.get_status()["on_ground"]).

Check your work with:
    python check_tools.py --role jumper     (does it work?)
    python check_tools.py --schema          (what does the AI read?)
"""

from typing import Annotated, Literal

from pydantic import Field
from robot import Robot, RobotError, get_robot
from tools_pilot import clean_direction, describe_motion
from tools_scout import hazard_name, survey

EDGE_TOLERANCE = 10  # how close (px) to a hazard's edge the robot should be before jumping
SAFETY_MARGIN = 5  # land a little past the far edge, not exactly on it


def jump(direction: str) -> str:
    """Make the robot do one whole jump toward "left" or "right" (about 165 px sideways).

    Only works while the robot stands on the ground.
    """
    # SPEC
    #   What it does: one jump in the given direction.
    #   Inputs:       direction: "left" or "right"
    #   Returns:      e.g. "Jumped right 165 px. Now at x=485."
    #   Refuses when: the direction is invalid, the robot is broken, or it is in the air
    #                 ("Not jumping: the robot is in the air.")   (does not jump)
    #
    # WORKED EXAMPLE: check the input, then act, then describe the result.
    # TODO (Jumper) 1a: annotate `direction` so the AI can only send "left" or "right".
    # Hint: from typing import Literal  ->  direction: Literal["left", "right"]
    clean = clean_direction(direction)
    if clean is None:
        message = f'Not jumping: direction {direction!r} is not valid. Use "left" or "right".'
        return message
    try:
        result = get_robot().jump(clean)
    except RobotError as error:
        message = f"Could not jump: {error}"
        return message
    sentence = describe_motion(result, f"Jumped {clean}")
    # TODO (Jumper) 1b: check the robot is alive and on the ground BEFORE jumping, and
    # explain clearly when it is not (without jumping).
    # Hint: status = get_robot().get_status(); look at status["alive"] and status["on_ground"].
    return sentence


def jump_over_next_obstacle() -> str:
    """TODO (Jumper): replace this line with the description the AI will read."""
    # SPEC
    #   What it does: jumps over the nearest gap or spike strip toward the flag, but only
    #                 when that is safe.
    #   Inputs:       none
    #   Returns:      e.g. "Jumped right over the gap: 165 px. Now at x=485."
    #   Refuses when (returns why, and what to do instead; does NOT jump):
    #     * the robot is broken or in the air;
    #     * nothing is ahead ("Not jumping: nothing to jump over. The path is clear.");
    #     * the hazard is more than EDGE_TOLERANCE px away
    #       ("Not jumping yet: the gap is 260 px away. Use walk_to_next_edge first.");
    #     * the hazard is too wide to clear from here.
    #   Uses:         survey(), hazard_name(), get_robot().get_status(), get_robot().jump(),
    #                 describe_motion()
    #
    # TODO (Jumper) 2a: build it to the spec.
    # TODO (Jumper) 2b: write the docstring the AI reads (what it jumps, when it refuses).
    # Hint: room needed for a gap    = distance + width + SAFETY_MARGIN
    #       room needed for spikes   = distance + width + Robot.PLAYER_WIDTH
    #       it is safe when the room needed <= Robot.JUMP_DISTANCE.
    # Hint: jump toward the flag: survey()["direction"].
    message = "TODO: jump_over_next_obstacle is not built yet."
    return message


# STRETCH (Jumper) 3: a gap wider than one jump may have a floating platform in the middle
# (see the STRETCH note in tools_scout.py). Jumping from the gap's edge lands on the
# platform; then walk to the platform's far edge and jump again. Can a tool tell the AI
# (or do) that, one jump per call?

TOOLS = [jump, jump_over_next_obstacle]
