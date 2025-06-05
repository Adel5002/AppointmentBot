import os
import re
from datetime import datetime

import requests

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from dotenv import load_dotenv

load_dotenv()

rt = Router()

class Form(StatesGroup):
    lastname_firstname = State()
    work_hours = State()
    lunch_time = State()
    days_off = State()

@rt.message(Command('verify'))
async def verify(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.lastname_firstname)
    await message.answer(
        f'хотите ли вы использовать эти фамилию-имя? {message.from_user.full_name}',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='Да'),
                    KeyboardButton(text='Нет'),
                ]
            ],
            resize_keyboard=True
        )
    )

@rt.message(Form.lastname_firstname, F.text.casefold() == 'да')
async def default_name(message: Message, state: FSMContext) -> None:
    await state.update_data(lastname_firstname=message.from_user.full_name)
    await state.set_state(Form.work_hours)
    await message.answer('Введите желаемые часы работы в формате: 8:00-17:00', reply_markup=ReplyKeyboardRemove())

@rt.message(F.text.casefold() == 'нет')
async def lastname_firstname_by_specialist(message: Message) -> None:
    await message.answer('Введите ваши фамилию-имя в таком формате: Иванов Иван', reply_markup=ReplyKeyboardRemove())

@rt.message(Form.lastname_firstname)
async def set_lastname_firstname_provided_by_specialist(message: Message, state: FSMContext) -> None:
    await state.update_data(lastname_firstname=message.text)
    await state.set_state(Form.work_hours)
    await message.answer('Введите желаемые часы работы в формате: 8:00-17:00')

time_range_pattern = re.compile(r"^\d{1,2}:\d{2}-\d{1,2}:\d{2}$")

@rt.message(Form.work_hours)
async def work_hours_set(message: Message, state: FSMContext):
    text = message.text.strip()

    if not time_range_pattern.match(text):
        await message.answer("❗ Пожалуйста, введите время в формате: *8:00-17:00*", parse_mode="Markdown")
        return

    await state.update_data(work_hours=text)
    await state.set_state(Form.lunch_time)
    await message.answer('Введите желаемое время обеденного перерыва в формате: 12:00-13:00')


@rt.message(Form.lunch_time)
async def lunch_time_set(message: Message, state: FSMContext):
    text = message.text.strip()

    if not time_range_pattern.match(text):
        await message.answer("❗ Пожалуйста, введите время в формате: *12:00-13:00*", parse_mode="Markdown")
        return

    await state.update_data(lunch_time=message.text)
    await state.set_state(Form.days_off)
    await message.answer('Введите выходные дни таким образом: суббота, воскресенье')

days_off_typing_checker = re.compile(r'^\s*\w+(?:\s*,\s*\w+)*\s*$')

@rt.message(Form.days_off)
async def days_off_set(message: Message, state: FSMContext):
    if not days_off_typing_checker.match(message.text):
        await message.answer('Дни недели обязательно надо вводить через запятую!')
        return

    await state.update_data(days_off=message.text)
    data = await state.get_data()
    await state.clear()
    await show_summary(message, data)

def to_iso_time(s):
    return datetime.strptime(s, '%H:%M').strftime('%H:%M:%S')

async def show_summary(message: Message, data: dict):
    specialist_create_data = {
        'id': message.from_user.id,
        'name': data['lastname_firstname'].split()[1],
        'lastname': data['lastname_firstname'].split()[0],
        'work_start': to_iso_time(data['work_hours'].split('-')[0]),
        'work_end': to_iso_time(data['work_hours'].split('-')[1]),
        'lunch_start': to_iso_time(data['lunch_time'].split('-')[0]),
        'lunch_end': to_iso_time(data['lunch_time'].split('-')[1]),
        'appointment_link': f'https://t.me/PleaseMakeAppointment_bot?startapp={message.from_user.id}'
    }

    create_specialist = requests.post(f'{os.getenv("NGROK_DOMAIN")}/specialist-create/', json=specialist_create_data)

    if create_specialist.status_code == 409:
        await message.answer(create_specialist.json()['detail'])
        return

    formatted_text = (f'Фамилия-Имя: {data["lastname_firstname"]}\n'
                      f'Рабочие часы: {data["work_hours"]}\n'
                      f'Обеденный перерыв: {data["lunch_time"]}\n'
                      f'Выходные дни: {data["days_off"]}\n'
                      f'Ваша ссылка которую вы будете выдавать вашим клиентам:\n'
                      f'https://t.me/PleaseMakeAppointment_bot?startapp={message.from_user.id}')

    russian_weekdays = {
        'понедельник': 0,
        'вторник': 1,
        'среда': 2,
        'четверг': 3,
        'пятница': 4,
        'суббота': 5,
        'воскресенье': 6,
    }


    for weekday in data['days_off'].split(', '):
        for k, v in russian_weekdays.items():
            if weekday.lower() == k:
                days_off_data = {
                    'specialist_id': message.from_user.id,
                    'weekday': v
                }
                requests.post(f'{os.getenv("NGROK_DOMAIN")}/specialistdayoff-create/', json=days_off_data)

    await message.answer('Ваш профиль настроен, осталась оплата')
    await message.answer(formatted_text)