# The assignment

Your team writes the **tools of an MCP server**: Python functions an AI model (Qwen, a small
open model) uses to play a platformer it cannot see. Your instructor plugs your `team_tools/`
folder into the game; the AI then plays **using only your tools**, on a level you have never seen.

Contents: [1. How a run works](#1-how-a-run-works) ·
[2. Rules for every tool](#2-rules-for-every-tool) ·
[3. Every function: inputs and outputs](#3-every-function-inputs-and-outputs) ·
[4. Working as a team](#4-working-as-a-team) · [5. Testing](#5-testing) ·
[6. Timeline](#6-timeline) · [7. Handing in](#7-handing-in) · [8. Stretch goals](#8-stretch-goals)

---

## 1. How a run works

1. The AI gets a short instruction ("reach the flag; each tool call costs energy") and an
   **energy** budget.
2. Before each move it reads your tools' **names, descriptions (docstrings) and input schemas
   (type hints)**, picks one tool, and sends inputs.
3. Your function runs and returns **text**. That text is all the AI learns.
4. **Every tool call costs 1 energy, or 2 if your tool crashes.** When energy runs out, the run ends.
5. Falling into a gap or touching spikes **breaks** the robot; it must be restarted
   (`restart_stage`) before it can move again.
6. A tool may move the robot **at most twice** per call. It cannot play the level by itself.

The graded level is **hidden**. It has the same kinds of terrain as the practice level, plus
surprises: at least one stage runs **right-to-left**, and there may be terrain kinds you have
not met yet (read `scan_terrain` in `robot.py`). **Never hard-code numbers**: compute
everything from the robot's sensors.

## 2. Rules for every tool

`python check_tools.py` tests most of these automatically.

1. **Do the job in the SPEC.** Each function's SPEC block says what it does, its inputs, what it
   returns (with examples) and when it refuses.
2. **Return a string** of at most **300 characters**. Short facts work best.
3. **Never crash.** Wrap robot calls in `try/except RobotError` and explain the problem in the
   returned text. A crash costs the AI **double energy** and teaches it nothing.
4. **Facts, not orders.** Write "a gap 100 px wide is 260 px (52 steps) ahead", not "JUMP NOW!!!".
5. **Units always.** Distances from the robot's **front edge** (the side facing the flag), in
   pixels, and also in steps where it helps (1 step = `Robot.WALK_SPEED` = 5 px).
6. **Write the docstring the AI reads**: what the tool does, when to use it, what it returns,
   when it refuses. (Replace every `TODO (Role): replace this line ...` docstring.)
7. **Annotate every input** (see `learn_annotations.ipynb`): `Literal["left", "right"]` for
   choices; `Annotated[int, Field(ge=0, le=200, description=...)]` for numbers with limits.
8. **Only these imports**: `robot`, your own `tools_*` files, `typing`, `pydantic`, `dataclasses`,
   `math`, `re`, `json`, `string`, `textwrap`, `collections`, `statistics`, `itertools`,
   `functools`, `random`. No `os`, `subprocess`, `open()`. The grader refuses other code.
9. **Use the Robot constants** (`Robot.WALK_SPEED`, `Robot.PLAYER_WIDTH`, `Robot.JUMP_DISTANCE`,
   `Robot.MAX_STEPS`) instead of typing the numbers.

## 3. Every function: inputs and outputs

The full SPEC (with example outputs and refusals) is above each function in its file. This is
the overview. **Tool** = the AI can call it (it is in the file's `TOOLS` list).
**Helper** = your teammates call it from their code.

### Scout: the eyes (`team_tools/tools_scout.py`)
| Function | Kind | Inputs | Returns | Your work |
|---|---|---|---|---|
| `survey()` | helper | none | dict: `direction`, `front_edge`, `obstacles` (nearest first), `flag_distance` | TODO 1: right-to-left stages; TODO 2: sort nearest first |
| `hazard_name(kind)` | helper | `kind: str` | `"spikes"` -> `"spike strip"` | done |
| `look_ahead()` | tool | none | the nearest hazards (kind, width, distance in px and steps) and the flag, or "path clear" | TODO 3: build it, write its docstring |
| `where_am_i()` | tool | none | stage, x, standing/in the air, flag distance, progress % | worked example; TODO 4: add flag distance and % |

### Pilot: the legs (`team_tools/tools_pilot.py`)
| Function | Kind | Inputs | Returns | Your work |
|---|---|---|---|---|
| `clean_direction(direction)` | helper | `direction: str` | `"left"`, `"right"` or `None` | TODO 1: accept " Right", "L", ... |
| `describe_motion(result, verb)` | helper | robot result `dict`, `verb: str` | one sentence about what a move did | TODO 2: "blocked" and "restart needed" |
| `walk(direction, distance)` | tool | `Literal["left", "right"]`, `int` 0-1000 px | where the robot ended up | **worked example of annotations** |
| `walk_to_next_edge()` | tool | none | walks to 0-5 px before the nearest hazard, says where it stopped | TODO 3 |
| `walk_to_flag()` | tool | none | walks to the flag, or refuses and names the hazard in the way | TODO 4 |

### Jumper (`team_tools/tools_jumper.py`)
| Function | Kind | Inputs | Returns | Your work |
|---|---|---|---|---|
| `jump(direction)` | tool | `direction` (annotate it!) | where the robot landed, or why it refused | worked example; TODO 1: annotate, refuse when broken or in the air |
| `jump_over_next_obstacle()` | tool | none | jumps the nearest hazard if it is close and clearable, or explains what to do instead | TODO 2 |

### Coach: memory and recovery (`team_tools/tools_coach.py`)
| Function | Kind | Inputs | Returns | Your work |
|---|---|---|---|---|
| `Notebook.add_note(text)` | method | `text: str` | the note as saved (stripped, max 100 chars; keeps the last 20) | TODO 1a |
| `Notebook.add_death(stage, x, cause, reason)` | method | `int, int, str, str` | nothing; logs one death | TODO 1b |
| `Notebook.summary()` | method | none | last notes and deaths, max 300 chars | TODO 1c |
| `remember(note)` | tool | `note`: text 1-100 chars (annotate it!) | confirms what was saved | TODO 2 |
| `recall()` | tool | none | the notebook's summary | TODO 3 |
| `restart_stage(reason)` | tool | `reason: str` | restarts a broken robot; refuses when it is fine | worked example; TODO 4: refuse when fine, log the death |
| `get_status()` | tool | none | stage, alive/broken, deaths, energy left | TODO 5 |

### The team contract (shared helpers)
They already work in a simple form, so nobody is blocked on day one. Their owners make them
better, but **never change what they return** without telling the team.

| Helper | Owner | Used by |
|---|---|---|
| `survey()` | Scout | everyone |
| `hazard_name(kind)` | Scout | Pilot, Jumper |
| `clean_direction(text)` | Pilot | Jumper |
| `describe_motion(result, verb)` | Pilot | Jumper |

## 4. Working as a team

**One file per person.** Each role edits only its own file, so you can all work at once
without overwriting each other. Agree on the team contract (above) first.

| Team size | Split |
|---|---|
| **3** | Scout, Pilot, Jumper. The **Scout also owns** `restart_stage` and `get_status` (move them into `tools_scout.py` and its `TOOLS` list). `remember`, `recall` and the `Notebook` class become optional. |
| **4** | Scout, Pilot, Jumper, Coach. |
| **5** | The four roles plus an **Integrator / QA**: owns no tool file, runs `check_tools.py` after every change, reviews every docstring and annotation, reads the AI transcripts your instructor shares, keeps `TEAM.md` up to date and leads the reflection. |

**Rotating duties** (swap each lab so everyone learns each part):
- **Docstring buddy:** review the next person's docstrings and annotations with the checklist at
  the end of `learn_annotations.ipynb`, and with `python check_tools.py --schema`. Would a small
  model understand them?
- **Transcript reader:** when your instructor shares a log of the AI playing with your tools,
  find one thing the AI got wrong, decide which tool was to blame, and write it in `TEAM.md`.

**A good rhythm:**
1. Read your SPECs and `robot.py`. Decide the wording style of your answers together.
2. Everyone works until `python check_tools.py --role <yours>` is green.
3. Read your descriptions as if you were the AI: `python check_tools.py --schema`.
4. After an AI run, fix the tool it misunderstood. Usually the problem is the **description**
   or the **answer text**, not the code.

**Sharing code:** a shared Git repository (one branch per person, merge often) works best, or one
shared copy of `team_tools/` where each person only edits their own file.

## 5. Testing

| Step | Command | Tells you |
|---|---|---|
| 1 | `python check_tools.py` | does each function do its job? (with hints) |
| 2 | `python check_tools.py --schema` | what the AI reads: are your descriptions and annotations clear? |
| 3 | your instructor's run | the AI plays with your tools; you get the transcript |

`check_tools.py` uses a **pretend robot**: you cannot see a game, but every check says what
situation it set up and what it expected. The grader also runs **hidden checks**: the same kinds
of situations with different numbers. Passing by hard-coding the numbers will fail them.

## 6. Timeline

| When | Goal |
|---|---|
| **Lab 1, start** | Walkthrough: what MCP is; the annotations notebook; your instructor builds two tools live. |
| **Lab 1, rest** | Your role's TODOs. **Checkpoint (graded):** at the end of the lab your instructor plugs your `team_tools/` into the game on the projector. |
| **Between labs** | Your instructor runs the AI on your tools and shares the transcript; fill in `TEAM.md`. |
| **Lab 2, first part** | Fix what confused the AI; improve docstrings and annotations. |
| **Lab 2, end** | **Final run:** the AI plays the hidden level with your tools. |

## 7. Handing in

Hand in **your `team_tools/` folder and `TEAM.md`** (zip them, or share your repository, as
your instructor asks). Your instructor's program uses your folder as it is, so:

- keep the four file names (`tools_scout.py`, ...) and the `TOOLS = [...]` list in each;
- keep tool and helper names as they are (the checks look for them);
- do not change `robot.py`, `check_tools.py` or `toolbox.py`: the grader uses its own copies;
- run `python check_tools.py` one last time: a file that does not load scores zero.

## 8. Stretch goals

- Handle a **floating platform** over a wide gap (see the STRETCH notes in the Scout and Jumper files).
- Give the robot a personality with `robot.say("...")` (one line per tool call, shown on screen).
- A `plan_crossing` tool that explains how to get over the next hazard, with the numbers worked out.
- **Discussion:** your server has about 11 tools. Real MCP servers can have hundreds. How could
  an AI find the right one without reading every description?
