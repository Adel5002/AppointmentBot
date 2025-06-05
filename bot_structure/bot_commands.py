from aiogram.types.bot_command import BotCommand

commands = [
    BotCommand(command='/verify', description='Для регистрации и верификации специалиста'),
    BotCommand(command='/specialist_delete', description='Удаление учетной записи'),
]