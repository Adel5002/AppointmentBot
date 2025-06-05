from aiogram import Dispatcher

from bot_structure.routes import verify

def setup_routers() -> Dispatcher:
    """
    В этой функции я просто объединяю пути всех команд

    :return:
    """

    dp = Dispatcher()

    dp.include_routers(
        verify.rt
    )

    return dp