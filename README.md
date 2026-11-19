# MCP Tool Jumper: team project

An AI model has to guide a little robot across gaps and spikes to a flag. The catch: the AI
**cannot see the game**. Everything it knows and everything it does goes through **tools**
that **your team writes**: ordinary Python functions that an MCP server offers to the AI.

```
AI model (Qwen, a small open model)
   │  reads each tool's NAME, DESCRIPTION (your docstring) and INPUTS (your type hints)
   │  "call look_ahead()"
   ▼
YOUR tool, e.g. look_ahead() in team_tools/tools_scout.py
   │  uses the robot: robot.scan_terrain(), robot.walk(...)
   ▼
the game (run by your instructor)
```

If `look_ahead` forgets to mention the spikes, the robot walks into them. A small model only
plays well with tools that **do their job**, are **described clearly**, and have **annotated
inputs**. That is the whole project.

This kit has **no game in it**. You write the functions; your instructor plugs your
`team_tools/` folder into the game and lets the AI play with it.

## Start here: set up with conda

You need **Anaconda** or **Miniconda** (Miniconda is the small version; either works).
If you do not have one yet, install Miniconda:
<https://www.anaconda.com/docs/getting-started/miniconda/install>

**1. Open a terminal in this folder.**
- **Windows:** open the **Anaconda Prompt** from the Start menu, then `cd` to this folder
  (for example `cd C:\Users\you\Downloads\mcp_tool_jumper_project`).
- **macOS / Linux:** open a terminal, then `cd` to this folder.

**2. Create the project's environment (once).** It installs Python 3.12, the MCP library
(which brings pydantic) and Jupyter, from the file `environment.yml`:

```bash
conda env create -f environment.yml
```

**3. Activate it (every time you open a new terminal).** Your prompt then starts with
`(tool-jumper)`:

```bash
conda activate tool-jumper
```

**4. Check that everything works:**

```bash
python check_tools.py                   # test your functions (many FAIL at first: that is normal)
jupyter lab learn_annotations.ipynb     # how to describe and annotate tools for an AI
```

**5. Read** **[INSTRUCTIONS.md](INSTRUCTIONS.md)** (the assignment) and
**[GRADING.md](GRADING.md)** (how it is graded).

**Using VS Code?** Open this folder, then `Ctrl+Shift+P` -> **Python: Select Interpreter** ->
pick the one named **tool-jumper**. For the notebook, pick the **tool-jumper** kernel
(top right of the notebook). Run commands in VS Code's terminal after `conda activate tool-jumper`.

## Commands

Always run them from this folder, with the environment active (`conda activate tool-jumper`).

| Command | What it does |
|---|---|
| `python check_tools.py` | Runs every function against a pretend robot in made-up situations: PASS/FAIL with a hint. |
| `python check_tools.py --role pilot` | Only one file's checks (`scout`, `pilot`, `jumper` or `coach`). |
| `python check_tools.py --schema` | Shows exactly what the AI reads about each of your tools. |
| `jupyter lab learn_annotations.ipynb` | The annotations reference and exercises. |

## What is in this folder

| File / folder | Who edits it | What it is |
|---|---|---|
| `team_tools/` | **your team** | four tool files, one per role: the only code you hand in |
| `TEAM.md` | **your team** | who did what, what you learned from the AI's runs, your reflection |
| `learn_annotations.ipynb` | you (to practise) | every way to annotate an input, and what the AI sees |
| `robot.py` | nobody | **read it**: everything the robot can sense and do |
| `check_tools.py`, `toolbox.py` | nobody | the offline checks |
| `environment.yml` | nobody | the conda environment (Python version and libraries) |
| `pyproject.toml` | nobody | settings for your instructor's tools; you can ignore it |

## Your team

| Role | File | Builds |
|---|---|---|
| **Scout** (eyes) | `team_tools/tools_scout.py` | `survey()`, `look_ahead`, `where_am_i` |
| **Pilot** (legs) | `team_tools/tools_pilot.py` | `clean_direction()`, `describe_motion()`, `walk_to_next_edge`, `walk_to_flag` |
| **Jumper** | `team_tools/tools_jumper.py` | `jump`, `jump_over_next_obstacle` |
| **Coach** (memory) | `team_tools/tools_coach.py` | the `Notebook` class, `remember`, `recall`, `restart_stage`, `get_status` |

Every function has a **SPEC** block (what it does, inputs, what it returns, when it refuses),
**TODO** steps and **Hint** lines. Teams of 3 or 5: see
[INSTRUCTIONS.md, part 4](INSTRUCTIONS.md#4-working-as-a-team).

## Problems?

| You see | Fix |
|---|---|
| `conda: command not found` (or "not recognized") | Install Miniconda (link above). On Windows, use the **Anaconda Prompt**, not the plain Command Prompt. |
| `ModuleNotFoundError: No module named 'mcp'` (or `pydantic`) | The environment is not active: run `conda activate tool-jumper`. In VS Code, pick the **tool-jumper** interpreter / kernel. |
| `ModuleNotFoundError: No module named 'robot'` | You are not in the project folder: `cd` into it first. |
| `CondaValueError: prefix already exists` | The environment already exists: just `conda activate tool-jumper`. |
| Something is broken in the environment | Start over: `conda env remove -n tool-jumper`, then `conda env create -f environment.yml`. |
| `environment.yml` changed (your instructor says so) | `conda env update -f environment.yml --prune` |
