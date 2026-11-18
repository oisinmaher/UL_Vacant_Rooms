# UL Vacant Rooms Display

This program lets you choose a building in UL (currently only the CS building), a day and a start time. It then shows which rooms are vacant over the following 3 hours — handy if you want to find a room to study or work on a project with your mates.

## Features

- **Clean Qt GUI** (PySide6): labelled pickers for building, day and start time
- **Results table** with the vacant rooms for each of the next three hours
- **Highlighted summary** of rooms that are free for the *entire* period
- **Refresh Data** button to re-scrape the timetable from the website
- Status-bar messages for errors and busy states

## How it works

- Gathers info from the [UL Timetable Website](https://www.timetable.ul.ie/) using **Selenium** (only needed on first run / refresh)
- Caches the scraped schedule in a `.pkl` file via **Pickle** so subsequent runs are instant
- `scrape_info.py` produces a plain structured report; `ui_display.py` renders it, so the logic is testable without a display

## Setup & usage

```bash
pip install -r requirements.txt
python main.py
```

1. Choose a **Building**, **Day** and **Start time**
2. Press **Show Vacant Rooms**
3. Read the table (per-hour vacancies) and the summary (rooms free the whole period)
4. Use **Refresh Data** if the timetable has changed (re-scrapes the website)
