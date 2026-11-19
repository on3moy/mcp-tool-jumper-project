"""Coach tools: the robot's MEMORY and recovery.

Owner: <your name here>   (in a team of 3, the Scout also owns restart_stage and get_status)

In this file:
    class Notebook       the robot's memory; you build its three methods (TODO 1)
    remember()           TOOL   you build it (TODO 2)
    recall()             TOOL   you build it (TODO 3)
    restart_stage()      TOOL   worked example; you finish TODO 4
    get_status()         TOOL   you build it (TODO 5)

The AI forgets details as a run gets long. A notebook it can write to and read back helps
it avoid making the same mistake twice.

Check your work with:
    python check_tools.py --role coach      (does it work?)
    python check_tools.py --schema          (what does the AI read?)
"""

from typing import Annotated, Any

from pydantic import Field
from robot import RobotError, get_robot


class Notebook:
    """The robot's memory: short notes plus a log of every death.

    One Notebook lives for the whole run (the ``notebook`` object below), so every tool
    call sees the notes written by earlier calls.
    """

    MAX_NOTES = 20
    MAX_NOTE_LENGTH = 100
    NOTES_IN_SUMMARY = 5
    DEATHS_IN_SUMMARY = 3

    def __init__(self) -> None:
        """Start with an empty notebook."""
        self.notes: list[str] = []
        self.death_log: list[dict[str, Any]] = []

    def add_note(self, text: str) -> str:
        """Store one note and return it exactly as it was saved.

        Example: add_note("  gap at x=400  ") -> "gap at x=400"
        """
        # SPEC
        #   Inputs:  text (str): the note
        #   Returns: the note as saved: spaces stripped, cut to MAX_NOTE_LENGTH characters
        #   Also:    when there are more than MAX_NOTES notes, the OLDEST one is forgotten
        # TODO (Coach) 1a: build it to the spec.
        # Hint: text[:self.MAX_NOTE_LENGTH] cuts a string; self.notes.pop(0) drops the oldest.
        saved_text = text
        return saved_text

    def add_death(self, stage: int, x: int, cause: str, reason: str) -> None:
        """Record one death: where it happened, what broke the robot, and the AI's reason.

        Example: add_death(1, 400, "fell_into_gap", "walked too far") stores
            {"stage": 1, "x": 400, "cause": "fell_into_gap", "reason": "walked too far"}
        """
        # SPEC
        #   Inputs:  stage (int), x (int), cause (str, e.g. "hit_spikes"), reason (str)
        #   Returns: nothing; appends one dictionary like the example to self.death_log
        # TODO (Coach) 1b: build it to the spec.

    def summary(self) -> str:
        """Return the last few notes and deaths as ONE short string (at most 300 characters).

        Example: "Notes: gap at x=400; spikes after the gap. Deaths: stage 1 x=400 (fell_into_gap)."
        """
        # SPEC
        #   Inputs:  none
        #   Returns: the last NOTES_IN_SUMMARY notes and last DEATHS_IN_SUMMARY deaths as one
        #            string of at most 300 characters (even with 20 long notes!);
        #            "The notebook is empty." when nothing is saved yet
        # TODO (Coach) 1c: build it to the spec.
        # Hint: "; ".join(list_of_strings) glues strings together; text[:300] cuts.
        summary_text = "The notebook is empty."
        return summary_text


notebook = Notebook()


def remember(note: str) -> str:
    """TODO (Coach): replace this line with the description the AI will read."""
    # SPEC
    #   What it does: saves a short note in the notebook for later.
    #   Inputs:       note: text, 1 to 100 characters
    #   Returns:      e.g. 'Saved note: "stage 1: gap at x=400 is 100 px wide".'
    #   Uses:         notebook.add_note()
    #
    # TODO (Coach) 2a: build it to the spec.
    # TODO (Coach) 2b: annotate `note` so the AI knows its limits, for example
    #     note: Annotated[str, Field(min_length=1, max_length=100, description="...")]
    # TODO (Coach) 2c: write the docstring the AI reads (what is worth remembering).
    message = "TODO: remember is not built yet."
    return message


def recall() -> str:
    """TODO (Coach): replace this line with the description the AI will read."""
    # SPEC
    #   What it does: reads back the notebook.
    #   Inputs:       none
    #   Returns:      notebook.summary() (at most 300 characters)
    #
    # TODO (Coach) 3a: build it to the spec.
    # TODO (Coach) 3b: write the docstring the AI reads (when is reading notes useful?).
    message = "TODO: recall is not built yet."
    return message


def restart_stage(reason: str) -> str:
    """Bring a broken robot back to life at the start of the current stage.

    Use it after the robot falls into a gap or hits spikes. `reason` is a short note on
    what went wrong.
    """
    # SPEC
    #   What it does: restarts the current stage after the robot broke.
    #   Inputs:       reason: a short note on what went wrong
    #   Returns:      e.g. "Restarted stage 1 at x=60. Deaths so far: 2."
    #   Refuses when: the robot is NOT broken ("Not restarting: the robot is fine; a restart
    #                 would throw away progress.")   (does not restart)
    #   Also:         logs the death in the notebook before restarting
    #
    # WORKED EXAMPLE (minimal): it works, but it could be smarter.
    try:
        result = get_robot().restart_stage()
    except RobotError as error:
        message = f"Could not restart: {error}"
        return message
    message = f"Restarted stage {result['stage']} at x={result['x']}."
    # TODO (Coach) 4: refuse when the robot is fine, and log the death before restarting.
    # Hint: get_robot().get_status() has "alive", "stage", "x", "death_reason" and "deaths".
    # Hint: notebook.add_death(stage, x, death_reason, reason)
    return message


def get_status() -> str:
    """TODO (Coach): replace this line with the description the AI will read."""
    # SPEC
    #   What it does: one line about the run so far.
    #   Inputs:       none
    #   Returns:      e.g. "Stage 2/3, alive, deaths: 2, energy left: 37 of 50."
    #                      "Stage 1/3, BROKEN (hit_spikes), deaths: 1, energy left: 44 of 50."
    #   Uses:         get_robot().get_status()
    #
    # TODO (Coach) 5a: build it to the spec.
    # TODO (Coach) 5b: write the docstring the AI reads.
    # Hint: the AI spends 1 energy per tool call (2 if it errors). Telling it how much is
    #       left helps it stop wasting calls.
    message = "TODO: get_status is not built yet."
    return message


TOOLS = [remember, recall, restart_stage, get_status]
