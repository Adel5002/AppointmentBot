from datetime import datetime, time, timedelta

from loguru import logger


def generate_time_slots(
        start: time,
        end: time,
        lunch_start: time,
        lunch_end: time,
        slot_minutes: int = 30,
        excluded_slots: list[datetime] | None = None,
) -> list[datetime]:

    today = datetime.now().date()
    start_dt = datetime.combine(today, start)
    end_dt = datetime.combine(today, end)
    lunch_start_dt = datetime.combine(today, lunch_start)
    lunch_end_dt = datetime.combine(today, lunch_end)

    slots = []
    current = start_dt

    while current + timedelta(minutes=slot_minutes) <= end_dt:
        next_slot = current + timedelta(minutes=slot_minutes)

        if not (lunch_start_dt < current < lunch_end_dt or lunch_start_dt < next_slot <= lunch_end_dt):
            slots.append(current)

        current = next_slot

    logger.info(excluded_slots)

    for excluded_slot in excluded_slots:
        if excluded_slot in slots:
            slots[slots.index(excluded_slot)] = (excluded_slot, 'disabled')

    return slots