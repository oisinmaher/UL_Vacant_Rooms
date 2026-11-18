"""Command-line fallback: print the result as plain text.

Usage:  python cli.py [building] [day] [time]
        python cli.py "Computer Science Building" Monday 09:00
"""
import sys

from scrape_info import DAYS, TIMES, ScrapeInfo


def main():
    args = sys.argv[1:]
    info = ScrapeInfo()

    if not args:
        building = next(iter(info.building_rooms))
        print(info.run(building, DAYS[0], TIMES[0]))
        return

    if len(args) != 3:
        print(f"Usage: python cli.py <building> <{ '/'.join(DAYS) }> <{ '/'.join(TIMES) }>")
        sys.exit(1)

    building, day, time = args
    if building not in info.building_rooms:
        print(f"Unknown building: {building!r}. Choices: {', '.join(info.building_rooms)}")
        sys.exit(1)
    if day not in DAYS:
        print(f"Unknown day: {day!r}. Choices: {', '.join(DAYS)}")
        sys.exit(1)
    if time not in TIMES:
        print(f"Unknown time: {time!r}. Choices: {', '.join(TIMES)}")
        sys.exit(1)

    print(info.run(building, day, time))


if __name__ == "__main__":
    main()
