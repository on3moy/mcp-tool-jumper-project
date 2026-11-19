# How the project is graded

The project is graded **out of 100**. If your course uses a different total, your instructor
scales it: **your points = score / 100 x the project's total** (for example 80/100 on a
40-point project is 32 points).

| Part | Points | How it is measured |
|---|---|---|
| **Agent performance** | **35** | The class AI (Qwen) plays the **hidden level** with your tools, **3 times**. Each run gets a score out of 100; your points are 35 x the **middle (median)** score / 100. |
| **Tool correctness** | **25** | **Hidden checks**: the same kinds of situations as `python check_tools.py`, with different numbers. Per role: Scout 7, Pilot 7, Jumper 7, Coach 4 (team of 3: Scout 9, Pilot 8, Jumper 8). |
| **Tool design** | **15** | Read by your instructor (helped by an automatic report): descriptions written for the AI, annotated inputs, short factual answers, helpful refusals and error messages. |
| **Python quality** | **10** | Descriptive names, Robot constants instead of magic numbers, functions that do one thing, the `Notebook` class, `try/except RobotError`. |
| **Reflection** (`TEAM.md`) | **10** | One moment the AI misread one of your tools (quote the log), what you changed, and what happened next; who did what. |
| **Lab 1 checkpoint** | **5** | At the end of Lab 1 your instructor plugs your `team_tools/` into the game on the projector; see part 6. |

## 1. Agent performance (35)

Each run is scored by the game itself, never from what your tools say:

```
70 x (stages cleared + progress on the current stage) / stages      how far the AI got
+ 10 if the whole level is completed                                finishing bonus
+ 20 x energy left / energy at the start, if completed              efficiency bonus
-  4 per death
-  2 per tool call that crashed or errored
   (kept between 0 and 100)
```

So: clear stages, avoid deaths, never crash, and do not waste energy on useless calls.
The hidden level has a stage that runs **right-to-left**, and may contain terrain you have not
met in practice. Tools that compute from the sensors handle it; tools with copied numbers do not.

## 2. Tool correctness (25)

The hidden checks test **what your tools do** in made-up situations: does `walk_to_next_edge`
stop 0-5 px before the hazard, does `jump_over_next_obstacle` refuse when it is too far away,
does `survey()` work right-to-left, and so on. They are the same kinds of checks as
`python check_tools.py`, with different numbers. Each role's points are its weight x the share of
its checks passed. (The checks every tool gets, such as "has a real description" and "does not
crash", count toward tool design instead.)

## 3. Tool design (15)

Your instructor reads what the AI reads (`python check_tools.py --schema`) and checks:

- [ ] every tool's docstring says what it does, when to use it, what it returns and when it refuses;
- [ ] every input is annotated: `Literal` for choices, ranges and lengths with `Field`,
      `Field(description=...)` where the meaning is not obvious;
- [ ] answers are short facts with units (px and steps), not orders and not raw JSON;
- [ ] refusals and errors say what is wrong **and what would work instead**.

## 4. Python quality (10)

Readable code: descriptive names (`flag_distance`, not `fd`), the Robot constants, small
functions, a working `Notebook` class, errors caught where the robot is used.

## 5. Reflection (10)

In `TEAM.md`: one real moment from a log where the AI misunderstood a tool (quote it), the
change you made (description, answer text, or behaviour), and what happened in the next run.
Plus a short "who did what". Honest and specific beats long.

## 6. Lab 1 checkpoint (5)

At the end of Lab 1, your instructor plugs your `team_tools/` folder into the game on the
projector and runs the **autopilot**: a fixed strategy (no AI) that only calls your
`walk_to_next_edge`, `jump_over_next_obstacle`, `walk_to_flag` and `restart_stage`.
**5 points if it clears practice stage 1.** If it does not, your instructor may give part of the
points for clear progress (for example, most of your checks passing). Those four tools come from
three different roles, so the checkpoint is a team effort.

## Individual grades

Each role's hidden-check results come from that person's own file, and `TEAM.md` says who did
what. Your instructor may adjust individual grades when the work was clearly uneven.
