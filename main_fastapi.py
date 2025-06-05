import asyncio
import logging
import os
import sys

import uvicorn

from contextlib import asynccontextmanager
from datetime import datetime, date
from typing import List, Sequence, Annotated

from fastapi import FastAPI, HTTPException, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse, JSONResponse
from loguru import logger
from sqlmodel import select
from sqlalchemy.orm import selectinload
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from pyngrok import ngrok
from dotenv import load_dotenv

from jinja_custom_filters.object_type_filter import type_name
from utils.appointment_reminder import appointment_reminder
from utils.work_time_generator import generate_time_slots

load_dotenv()

from SQLmodel.database import create_db_and_tables, SessionDep
from SQLmodel.models import Specialist, SpecialistCreate, SpecialistUpdate, SpecialistDayOff, AppointmentTime, User, \
    UserCreate, UserUpdate, UserRead

from bot import bot


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    ngrok.set_auth_token(os.getenv('NGROK_AUTH_TOKEN'))
    connection = ngrok.connect(addr='8000', domain=os.getenv('NGROK_DOMAIN_NAME'))
    asyncio.create_task(appointment_reminder())
    logger.info(connection.public_url)
    logger.info('Приложение стартовало ✅')
    yield
    ngrok.disconnect(connection.public_url)
    logger.info('Приложение остановлено ❌')


app = FastAPI(lifespan=lifespan)

app.mount("/statics", StaticFiles(directory="statics"), name="statics")

templates = Jinja2Templates(directory="templates")
templates.env.filters['type_name'] = type_name

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket('/ws/reload')
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post('/set-cookies/')
async def set_cookies(request: Request):
    data = await request.json()
    response = JSONResponse(content={'message': 'Cookies set'})
    response.set_cookie(key='user_tg_id', value=data['data']['id'])
    response.set_cookie(key='firstname', value=data['data']['first_name'])
    return response

@app.get('/', response_class=HTMLResponse)
async def main_page(request: Request, session: SessionDep):
    firstname = request.cookies.get("firstname")
    logger.info(firstname)
    specialists_ids = session.scalars(select(Specialist.id)).all()
    return templates.TemplateResponse(
        request=request,
        name='index.html',
        context={
            'today': date.today(),
            'specialists_ids': list(map(str, specialists_ids))
        }
    )

@app.get('/choose-datetime/{specialist_id}/')
async def choose_datetime(request: Request, session: SessionDep, specialist_id: int, choose_date: date = date.today()):
    specialist_exists = session.get(Specialist, specialist_id)
    logger.info(specialist_exists)

    if not specialist_exists:
        return RedirectResponse(url='/?error=true', status_code=302)

    user_appointment = session.scalar(select(AppointmentTime).where(AppointmentTime.user_id == request.cookies.get('user_tg_id')))
    logger.info(user_appointment)
    specialist = session.get(Specialist, specialist_id)
    work_time_start = specialist.work_start
    work_time_end = specialist.work_end
    lunch_time_start = specialist.lunch_start
    lunch_time_end = specialist.lunch_end

    today = date.today()

    specialist_daysoff = session.scalars(
        select(SpecialistDayOff)
        .where(SpecialistDayOff.specialist_id == specialist_id)
    )

    if choose_date < today:
        raise HTTPException(status_code=409, detail='Вы не можете выбрать прошедшую дату!')

    for dayoff in specialist_daysoff:
        if choose_date.weekday() == dayoff.weekday:
            raise HTTPException(status_code=409, detail='Это выходной!')

    appointments = session.scalars(
        select(AppointmentTime.datetime)
        .where(AppointmentTime.specialist_id == specialist_id)
    ).all()

    time_slots = generate_time_slots(
        work_time_start,
        work_time_end,
        lunch_time_start,
        lunch_time_end,
        excluded_slots=appointments,
        choose_date=choose_date
    )
    logger.info(time_slots)

    return templates.TemplateResponse(
        request=request,
        name='choose_datetime/choose_datetime.html',
        context={
            'time_slots': time_slots,
            'current_date': choose_date,
            'user_appointment': user_appointment
        }
    )

@app.post('/get-date/{specialist_id}')
async def get_date(
        request: Request,
        session: SessionDep,
        appointment_date: Annotated[datetime, Form()],
        specialist_id: int,
        user_id: Annotated[int, Form()],
        choose_date: date
):

    user_has_appointment = session.get(AppointmentTime, user_id)

    if user_has_appointment:
        raise HTTPException(status_code=409, detail="User already has an appointment")

    appointment_exists = session.scalar(
        select(AppointmentTime)
        .where(AppointmentTime.specialist_id == specialist_id)
        .where(AppointmentTime.datetime == appointment_date)
    )

    if appointment_exists:
        raise HTTPException(status_code=409, detail="This appointment already taken!")

    appointment = AppointmentTime(
        user_id=user_id,
        specialist_id=specialist_id,
        datetime=appointment_date
    )

    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    await manager.broadcast("reload")
    return RedirectResponse(
        url=f'{request.url_for("choose_datetime", specialist_id=specialist_id)}?choose_date={choose_date}',
        status_code=303
    )

@app.get('/specialist-profile/{specialist_id}')
async def specialist_profile(request: Request, specialist_id: int, session: SessionDep):
    specialist = session.get(Specialist, specialist_id)
    logger.info(specialist)
    return templates.TemplateResponse(
        request=request,
        name='specialist_profile/specialist_profile.html',
        context={'specialist': specialist}
    )

@app.get('/edit-specialist-page/{specialist_id}')
async def edit_specialist_page(request: Request, specialist_id: int, session: SessionDep):
    specialist = session.get(Specialist, specialist_id)
    return templates.TemplateResponse(
        request=request,
        name='specialist_profile/edit_profile.html',
        context={'specialist': specialist}
    )

@app.get('/appointment-details/{appointment_id}')
async def appointment_details(request: Request, appointment_id: int, session: SessionDep):
    appointment = session.get(AppointmentTime, appointment_id)
    return templates.TemplateResponse(
        request=request,
        name='specialist_profile/appointment_details.html',
        context={'appointment': appointment}
    )

# --- Specialist ---

@app.post('/specialist-create/', response_model=Specialist)
async def specialist_create(specialist_data: SpecialistCreate, session: SessionDep) -> Specialist:
    specialist_exists = session.get(Specialist, specialist_data.id)
    logger.info(specialist_data)
    if specialist_exists:
        raise HTTPException(status_code=409, detail='Специалист с таким id уже существует!')

    specialist = Specialist(**specialist_data.dict())
    session.add(specialist)
    session.commit()
    session.refresh(specialist)
    return specialist


@app.put('/specialist-update/{specialist_id}', response_model=Specialist)
async def specialist_update(specialist_id: int, specialist_new_data: SpecialistUpdate, session: SessionDep) -> Specialist:
    specialist = session.get(Specialist, specialist_id)

    if not specialist:
        raise HTTPException(404, 'This user does not exists!')
    for key, value in specialist_new_data.dict(exclude_unset=True).items():
        setattr(specialist, key, value)

    session.commit()
    session.refresh(specialist)
    return specialist


@app.delete('/specialist-delete/{specialist_id}')
async def specialist_delete(specialist_id: int, session: SessionDep):
    specialist = session.get(Specialist, specialist_id)
    if not specialist:
        raise HTTPException(404, 'This user does not exists!')
    session.delete(specialist)
    session.commit()
    return {'success': 'Specialist was successfully deleted!'}


@app.get('/specialist/{specialist_id}', response_model=Specialist)
async def get_specialist(specialist_id: int, session: SessionDep) -> Specialist:
    specialist = session.get(Specialist, specialist_id)
    if not specialist:
        raise HTTPException(404, 'This user does not exists!')
    return specialist


@app.get('/specialists/', response_model=List[Specialist])
async def get_specialists(session: SessionDep) -> Sequence[Specialist]:
    specialists = session.scalars(select(Specialist))
    return specialists


# --- User ---

@app.post('/user-create/', response_model=User)
async def user_create(user_data: UserCreate, session: SessionDep) -> User:
    user_exists = session.get(User, user_data.id)
    if user_exists:
        raise HTTPException(409, 'User already exists!')
    user = User(**user_data.dict())
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.put('/user-update/{user_id}', response_model=User)
async def user_update(user_id: int, user_new_data: UserUpdate, session: SessionDep) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, 'User not found')
    for key, value in user_new_data.dict(exclude_unset=True).items():
        setattr(user, key, value)
    session.commit()
    session.refresh(user)
    return user


@app.delete('/user-delete/{user_id}')
async def user_delete(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, 'User not found')
    session.delete(user)
    session.commit()
    return {'success': 'User deleted successfully'}


@app.get('/user/{user_id}', response_model=UserRead)
async def get_user(user_id: int, session: SessionDep) -> User:
    user = session.scalar(
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.appointment)
        )
    )
    if not user:
        raise HTTPException(404, 'User not found')
    return user


@app.get('/users/', response_model=List[User])
async def get_users(session: SessionDep) -> Sequence[User]:
    users = session.scalars(select(User)).all()
    if not users:
        raise HTTPException(404, 'No users found')
    return users


# --- AppointmentTime ---

@app.post('/appointment-create/', response_model=AppointmentTime)
async def appointment_create(appointment_data: AppointmentTime, session: SessionDep) -> AppointmentTime:
    appointment = AppointmentTime(
        user_id=appointment_data.user_id,
        datetime=datetime.fromisoformat(appointment_data.datetime),
    )
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return appointment


@app.put('/appointment-update/{appointment_id}', response_model=AppointmentTime)
async def appointment_update(appointment_id: int, appointment_new_data: AppointmentTime, session: SessionDep) -> AppointmentTime:
    appointment = session.get(AppointmentTime, appointment_id)
    if not appointment:
        raise HTTPException(404, 'Appointment not found')
    for key, value in appointment_new_data.dict(exclude_unset=True).items():
        if key == 'datetime':
            setattr(appointment, key, datetime.fromisoformat(value))
        else:
            setattr(appointment, key, value)
    session.commit()
    session.refresh(appointment)
    return appointment


@app.delete('/appointment-delete/{appointment_id}')
async def appointment_delete(appointment_id: int, session: SessionDep):
    appointment = session.get(AppointmentTime, appointment_id)
    user = session.get(User, appointment.user_id)
    if not appointment:
        raise HTTPException(404, 'Appointment not found')
    session.delete(appointment)
    session.commit()
    await bot.send_message(chat_id=appointment.specialist_id, text=f'{user.name} отменил запись в {appointment.datetime}')
    await manager.broadcast("reload")
    return {'success': 'Appointment deleted successfully'}


@app.get('/appointment/{appointment_id}', response_model=AppointmentTime)
async def get_appointment(appointment_id: int, session: SessionDep) -> AppointmentTime:
    appointment = session.get(AppointmentTime, appointment_id)
    if not appointment:
        raise HTTPException(404, 'Appointment not found')
    return appointment


@app.get('/appointments/', response_model=List[AppointmentTime])
async def get_appointments(session: SessionDep) -> Sequence[AppointmentTime]:
    appointments = session.scalars(select(AppointmentTime)).all()
    if not appointments:
        raise HTTPException(404, 'No appointments found')
    return appointments


# --- SpecialistDayOff ---

@app.post('/specialistdayoff-create/', response_model=SpecialistDayOff)
async def specialistdayoff_create(dayoff_data: SpecialistDayOff, session: SessionDep) -> SpecialistDayOff:
    dayoff = SpecialistDayOff(**dayoff_data.dict())
    session.add(dayoff)
    session.commit()
    session.refresh(dayoff)
    return dayoff


@app.put('/specialistdayoff-update/{dayoff_id}', response_model=SpecialistDayOff)
async def specialistdayoff_update(dayoff_id: int, dayoff_new_data: SpecialistDayOff, session: SessionDep) -> SpecialistDayOff:
    dayoff = session.get(SpecialistDayOff, dayoff_id)
    if not dayoff:
        raise HTTPException(404, 'SpecialistDayOff not found')
    for key, value in dayoff_new_data.dict(exclude_unset=True).items():
        setattr(dayoff, key, value)
    session.commit()
    session.refresh(dayoff)
    return dayoff


@app.delete('/specialistdayoff-delete/{dayoff_id}')
async def specialistdayoff_delete(dayoff_id: int, session: SessionDep):
    dayoff = session.get(SpecialistDayOff, dayoff_id)
    if not dayoff:
        raise HTTPException(404, 'SpecialistDayOff not found')
    session.delete(dayoff)
    session.commit()
    return {'success': 'SpecialistDayOff deleted successfully'}


@app.get('/specialistdayoff/{dayoff_id}', response_model=SpecialistDayOff)
async def get_specialistdayoff(dayoff_id: int, session: SessionDep) -> SpecialistDayOff:
    dayoff = session.get(SpecialistDayOff, dayoff_id)
    if not dayoff:
        raise HTTPException(404, 'SpecialistDayOff not found')
    return dayoff


@app.get('/specialistdayoffs/', response_model=List[SpecialistDayOff])
async def get_specialistdayoffs(session: SessionDep) -> Sequence[SpecialistDayOff]:
    dayoffs = session.scalars(select(SpecialistDayOff)).all()
    if not dayoffs:
        raise HTTPException(404, 'No SpecialistDayOff found')
    return dayoffs

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)