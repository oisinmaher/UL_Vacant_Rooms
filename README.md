# UL Vacant Rooms Display

Pick a building (currently CS building), a day and a time — the app shows
which rooms are vacant over the following 3 hours. Handy when you need a room
to study or work on a project with your mates.

Info is gathered from the [UL Timetable Website](https://www.timetable.ul.ie/)
using **Selenium**, then cached in a `.pkl` file with **Pickle** so there is no
need to scrape on every use.

## GUI

Built with **Qt / PySide6**. A clean, single-window layout:

- **Header form** — building, day and time pickers plus a
  *Check availability* button.
- **Summary banner** — highlights the rooms free for the *entire* chosen
  window (green) or warns that none are (red).
- **Availability table** — one row per room, one column per hour, with each
  cell marked **Free** (green) or **Booked** (red). Rooms free for the whole
  window get a ★ and a highlighted row.

Run it with:

```sh
python main.py
```

## CLI

The same data layer can be used without the GUI:

```sh
python cli.py "Computer Science Building" Monday 10:00
```

## Project layout

| File              | Purpose                                              |
|-------------------|------------------------------------------------------|
| `main.py`         | GUI entry point (`python main.py`)                   |
| `ui_display.py`   | PySide6 window, form, banner and results table       |
| `scrape_info.py`  | Selenium scraping + cached pickle + `query()` data   |
| `cli.py`          | Text-only fallback for the same data                 |
| `tests/`          | pytest coverage of the data layer (no Qt needed)     |
| `cs_building_schedule.pkl` | Cached CS building timetable         |

## Setup

```sh
pip install -r requirements.txt   # selenium + PySide6
python main.py
```

## Tests

```sh
python -m pytest tests/ -q
```
