import asyncio
from datetime import datetime, timedelta

from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from loguru import logger

from SQLmodel.database import engine, create_db_and_tables
from SQLmodel.models import User, AppointmentTime


async def appointment_reminder(session: Session = Session(engine)):
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
                        logger.info(f'{user.name} у вас запись {user.appointment.datetime}')
                    elif user.appointment.datetime <= datetime_now_1h_plus and user.reminder_1h == False:
                        user.reminder_1h = True
                        logger.info(f'{user.name} у вас запись {user.appointment.datetime}')
                    elif user.appointment.datetime <= datetime_now:
                        appointment = ss.get(AppointmentTime, user.appointment.id)
                        logger.info(appointment)
                        ss.delete(appointment)
                        user.reminder_3h = False
                        user.reminder_1h = False
            ss.commit()

        await asyncio.sleep(30)
