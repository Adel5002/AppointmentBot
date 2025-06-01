from datetime import time, datetime
from email.policy import default
from typing import List, Optional

from sqlmodel import Field, SQLModel, Relationship

class SpecialistCreate(SQLModel):
    id: int = Field(primary_key=True)
    name: str = Field(index=True, max_length=64)
    lastname: str = Field(max_length=64)
    email: str
    work_start: time
    work_end: time
    lunch_start: time
    lunch_end: time


class SpecialistUpdate(SQLModel):
    name: str | None = Field(default=None, index=True, max_length=64)
    lastname: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None)
    work_start: time | None = Field(default=None)
    work_end: time | None = Field(default=None)
    lunch_start: time | None = Field(default=None)
    lunch_end: time | None = Field(default=None)


class Specialist(SpecialistCreate, table=True):
    days_off: Optional[List['SpecialistDayOff']] = Relationship(back_populates='specialist')
    appointment: Optional[List['AppointmentTime']] = Relationship(back_populates='specialist')


class SpecialistDayOff(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    weekday: int

    specialist_id: int = Field(foreign_key='specialist.id')
    specialist: Optional[Specialist] = Relationship(back_populates='days_off')


class UserCreate(SQLModel):
    id: int = Field(primary_key=True)
    name: str = Field(max_length=64)
    lastname: str = Field(max_length=64)
    reminder_3h: bool = Field(default=False)
    reminder_1h: bool = Field(default=False)


class UserUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=64)
    lastname: str | None = Field(default=None, max_length=64)
    reminder_3h: bool | None = Field(default=False)
    reminder_1h: bool | None = Field(default=False)


class UserRead(SQLModel):
    id: int
    name: str
    lastname: str
    reminder_3h: bool = Field(default=False)
    reminder_1h: bool = Field(default=False)
    appointment: Optional['AppointmentTimeRead'] = None


class User(UserCreate, table=True):
    appointment: 'AppointmentTime' = Relationship(back_populates='user')


class AppointmentTimeRead(SQLModel):
    id: int
    datetime: datetime
    specialist_id: int

class AppointmentTime(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    datetime: datetime

    user_id: int = Field(foreign_key='user.id', unique=True)
    user: User = Relationship(back_populates='appointment')

    specialist_id: int = Field(foreign_key='specialist.id')
    specialist: Specialist = Relationship(back_populates='appointment')

