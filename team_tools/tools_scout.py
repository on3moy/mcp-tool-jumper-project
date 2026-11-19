"""Scout tools: the robot's EYES. Turn raw terrain numbers into short, useful facts.

Owner: <your name here>

The AI cannot see the screen. It only knows what your tools tell it. If look_ahead forgets
to mention the spikes, the AI walks straight into them.

In this file:
    survey()        helper (not a tool)  works in a simple form; you finish TODO 1-2
    hazard_name()   helper (not a tool)  done
    look_ahead()    TOOL                 you build it (TODO 3)
    where_am_i()    TOOL                 worked example; you finish TODO 4

For every TOOL you also write the docstring the AI reads, and annotate any inputs
(see learn_annotations.ipynb). Check your work with:
    python check_tools.py --role scout      (does it work?)
    python check_tools.py --schema          (what does the AI read?)
"""

from typing import Any

from robot import Robot, RobotError, get_robot

HAZARD_NAMES = {"gap": "gap", "spikes": "spike strip"}
# Only these kinds of terrain break the robot. scan_terrain() can return other kinds too
# (for example "platform"), so never treat "not ground" as "dangerous".
HAZARD_KINDS = ("gap", "spikes")


def survey() -> dict[str, Any]:
    """Work out what lies between the robot and the flag (a helper for the team, not a tool).

    Returns a dictionary:
        "direction":     "right" or "left" (the way to the flag)
        "front_edge":    x of the robot's edge that faces the flag
        "obstacles":     hazards still ahead, nearest first, each
                         {"kind": "gap" or "spikes", "distance": px, "width": px}
        "flag_distance": px from the front edge to the flag (0 when touching it)

    Example: robot at x=60, a gap at 400..500, flag at 880..920 ->
        {"direction": "right", "front_edge": 90,
         "obstacles": [{"kind": "gap", "distance": 310, "width": 100}],
         "flag_distance": 790}
    """
    # SPEC
    #   Inputs:  none (reads robot.get_position(), robot.get_goal(), robot.scan_terrain())
    #   Returns: the dictionary above. Your teammates rely on its exact shape: never rename
    #            its keys without telling them.
    robot = get_robot()
    robot_x, _ = robot.get_position()
    flag_left, flag_right = robot.get_goal()

    # TODO (Scout) 1: this version always assumes the flag is to the RIGHT.
    # Some stages run right-to-left! Work out the real direction from the flag's position.
    # Hint: compare the middle of the robot (robot_x + Robot.PLAYER_WIDTH // 2) with the
    #       middle of the flag ((flag_left + flag_right) // 2).
    # Hint: facing left, the front edge is robot_x, the flag distance is
    #       front_edge - flag_right, and a hazard's distance is front_edge - its "right".
    direction = "right"
    front_edge = robot_x + Robot.PLAYER_WIDTH
    flag_distance = max(0, flag_left - front_edge)

    obstacles = []
    for piece in robot.scan_terrain():
        if piece["kind"] not in HAZARD_KINDS:
            continue
        # A hazard counts while its far side is still ahead and it is not beyond the flag.
        is_ahead = piece["right"] > front_edge and piece["left"] < flag_left
        if is_ahead:
            distance = max(0, piece["left"] - front_edge)
            width = piece["right"] - piece["left"]
            obstacles.append({"kind": piece["kind"], "distance": distance, "width": width})

    # TODO (Scout) 2: scan_terrain() is NOT sorted by distance, so obstacles[0] is not
    # always the nearest one. Sort the list, nearest first.
    # Hint: obstacles.sort(key=...) with a small function (or lambda) that returns "distance".

    surroundings = {
        "direction": direction,
        "front_edge": front_edge,
        "obstacles": obstacles,
        "flag_distance": flag_distance,
    }
    return surroundings


def hazard_name(kind: str) -> str:
    """Return a readable name for a terrain kind: "spikes" -> "spike strip" (a team helper)."""
    name = HAZARD_NAMES.get(kind, kind)
    return name


def look_ahead() -> str:
    """TODO (Scout): replace this line with the description the AI will read."""
    # SPEC
    #   What it does: tells the AI what lies between the robot and the flag, nearest first.
    #                 It never moves the robot.
    #   Inputs:       none
    #   Returns:      ONE sentence, at most 300 characters, for example
    #                   "Flag: 790 px (158 steps) to the right. Ahead, nearest first: gap 100 px
    #                    wide, 260 px (52 steps) ahead; spike strip 60 px wide, 510 px (102 steps)
    #                    ahead."
    #                   "Path clear: no gaps or spikes before the flag, 790 px to the right."
    #                   "Gap 100 px wide right at your front edge (0 px). Flag: 525 px to the
    #                    right."
    #   If the robot cannot be read (RobotError): return "Cannot look right now: <reason>".
    #   Uses:         survey(), hazard_name(), Robot.WALK_SPEED
    #
    # TODO (Scout) 3a: build the sentence. List up to 3 hazards (kind, width, distance) and
    # the flag's distance and direction. When nothing is in the way, say the path is clear.
    # TODO (Scout) 3b: write the docstring the AI reads: what the tool reports, in which units,
    # that it changes nothing, and when to use it (before moving).
    # Hint: give each distance in pixels AND steps: steps = distance // Robot.WALK_SPEED.
    #       Small models are bad at dividing; do the arithmetic for them.
    # Hint: the FIRST hazard's distance is also how far the robot can safely walk on the
    #       ground it stands on.
    # Hint: a distance of 0 means the robot is right at the edge. Say that in words.
    message = "TODO: look_ahead is not built yet."
    return message


def where_am_i() -> str:
    """Report the stage number, the robot's x position, and whether it stands or is in the air.

    If the robot is broken, it says what broke it. Changes nothing.
    """
    # SPEC
    #   What it does: tells the AI where the robot is and how far it has come.
    #   Inputs:       none
    #   Returns:      ONE sentence, at most 300 characters, for example
    #                   "Stage 2/3, x=60, standing on the ground, 7% of the way to the flag
    #                    (790 px to go, to the right)."
    #                   "BROKEN (fell_into_gap) on stage 1 at x=400. Restart the stage first."
    #   Uses:         robot.get_status(), survey()
    #
    # WORKED EXAMPLE: read the sensors, build the answer step by step, catch RobotError.
    robot = get_robot()
    try:
        status = robot.get_status()
    except RobotError as error:
        message = f"Cannot check the position right now: {error}"
        return message
    if not status["alive"]:
        report = f"BROKEN ({status['death_reason']}) on stage {status['stage']} at x={status['x']}."
        return report
    footing = "standing on the ground" if status["on_ground"] else "in the air"
    report = f"Stage {status['stage']}/{status['stages_total']}, x={status['x']}, {footing}."
    # TODO (Scout) 4: also report how far the flag is (use survey()), and the progress
    # as a percentage from 0 to 100.
    # Hint: progress = how far the front edge has come / the whole distance to the flag.
    #       Facing right, the whole distance is front_edge + flag_distance (from x = 0).
    #       Facing left, it is (1000 - front_edge) + flag_distance. Keep it between 0 and 100.
    return report


# STRETCH (Scout) 5: some stages may have a floating PLATFORM over a wide gap:
# scan_terrain() then also returns {"kind": "platform", "left": ..., "right": ..., "top": ...}
# where "top" is the y of its upper surface (the ground's surface is y = 450; smaller is higher).
# A gap too wide for one jump can only be crossed by jumping onto the platform, then off it.
# How would you describe that to the AI so it does not try to jump the whole gap at once?

TOOLS = [look_ahead, where_am_i]
