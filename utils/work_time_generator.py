from datetime import datetime, time, timedelta, date

from loguru import logger


def generate_time_slots(
        start: time,
        end: time,
        lunch_start: time,
        lunch_end: time,
        choose_date: date,
        slot_minutes: int = 30,
        excluded_slots: list[datetime] | None = None,
) -> list[datetime]:

    """
    Эта функция генерирует временные слоты в которые можно взять запись, также она учитывает
    время обеда и помечает уже занятые слоты

    :param start:
    :param end:
    :param lunch_start:
    :param lunch_end:
    :param choose_date:
    :param slot_minutes:
    :param excluded_slots:
    :return:
    """

    start_dt = datetime.combine(choose_date, start)
    end_dt = datetime.combine(choose_date, end)
    lunch_start_dt = datetime.combine(choose_date, lunch_start)
    lunch_end_dt = datetime.combine(choose_date, lunch_end)

    # Где то хранить slots чтобы нельзя было переиспользовать слоты
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