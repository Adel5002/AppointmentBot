import asyncio
from datetime import datetime, timedelta

from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from loguru import logger

from SQLmodel.database import engine
from SQLmodel.models import User, AppointmentTime

from bot import bot


async def appointment_reminder(session: Session = Session(engine)) -> None:
    """
    Эта функция напоминалка, которая срабатывает за 3 и 1 час до записи и шлет напоминание как юзеру
    так и специалисту.

    :param session:
    :return:
    """
    while True:
        with session as ss:
            users = ss.scalars(
                select(User)
                .options(selectinload(User.appointment))
            ).all()
            datetime_now = datetime.now()
            datetime_now_1h_plus = datetime_now + timedelta(hours=1)
            datetime_now_3h_plus = datetime_now + timedelta(hours=3)
            for user in users:
                if user.appointment:
                    if user.appointment.datetime <= datetime_now_3h_plus and user.reminder_3h == False:
                        user.reminder_3h = True
                        logger.info(user.id)
                        logger.info(user.appointment.specialist_id)
                        await bot.send_message(
                            chat_id=user.id,
                            text=f'{user.name} у вас запись {user.appointment.datetime}'
                        )
                        await bot.send_message(
                            chat_id=user.appointment.specialist_id,
                            text=f'У вас сегодня есть запись в {user.appointment.datetime} с юзером {user.name}'
                        )
                        logger.info(f'{user.name} у вас запись {user.appointment.datetime}')
                    elif user.appointment.datetime <= datetime_now_1h_plus and user.reminder_1h == False:
                        user.reminder_1h = True

                        await bot.send_message(
                            chat_id=user.id,
                            text=f'{user.name} у вас запись {user.appointment.datetime}'
                        )
                        await bot.send_message(
                            chat_id=user.appointment.specialist_id,
                            text=f'У вас сегодня есть запись в {user.appointment.datetime} с юзером {user.name}'
                        )
                        logger.info(f'{user.name} у вас запись {user.appointment.datetime}')
                    if user.appointment.datetime <= datetime_now:
                        appointment = ss.get(AppointmentTime, user.appointment.id)
                        logger.info(appointment)
                        ss.delete(appointment)
                        user.reminder_3h = False
                        user.reminder_1h = False
            ss.commit()

        await asyncio.sleep(30)
