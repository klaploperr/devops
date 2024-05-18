from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
import logging
import re
import paramiko
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

client = paramiko.SSHClient()

TOKEN = os.getenv('TOKEN')
DB_HOST = os.getenv('DB_HOST')
RM_HOST = os.getenv('RM_HOST')
RM_USER = os.getenv('RM_USER')
RM_PORT = os.getenv('RM_PORT')
RM_PASSWORD = os.getenv('RM_PASSWORD')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT')
SSH_PORT = os.getenv('SSH_PORT')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_USER = os.getenv('DB_USER')

(FIND_NUMBERS, FIND_EMAILS, CHECK_PASSWORD, CONNECT, COMMAND_HANDLER,
 GET_APT_LIST, INSERT_PHONES, INSERT_EMAILS) = range(8)
phoneNumberToInsert = []
emailList = []


# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')
    update.message.reply_text(f'Используй /help для получения справки...')


def help_command(update: Update, context):
    update.message.reply_text('Список разрешенных команд:\n\
    /verify_password - Проверка сложности пароля\n\
    /find_email - Поиск в тексте email-адоресов\n\
    /find_phone_numbers - Поиск в тексте номеров телефонов\n\
    /connect - Подключение к SSH серверу\n\
    /get_repl_logs - Вывести логи о репликации баз данных\n\
    /get_emails - Вывести данные об обнаруженных email-адресах\n\
    /get_phone_numbers - Вывести данные об обнаруженных номерах телефона')


def help_ssh(update: Update, context):
    update.message.reply_text('Список команд получения информации о системе:\n\
    /get_release - о релизе\n\
    /get_uname - об архитектуры процессора, имени хоста системы и версии ядра\n\
    /get_uptime - о времени работы\n\
    /get_df - о состоянии файловой системы\n\
    /get_free - о состоянии оперативной памяти\n\
    /get_mpstat - о производительности системы\n\
    /get_w - о работающих в данной системе пользователях\n\
    /get_auths - последние 10 входов в систему\n\
    /get_critical - последние 5 критических события\n\
    /get_ps - о запущенных процессах\n\
    /get_ss - об используемых портах\n\
    /get_apt_list - об установленных пакетах\n\
    /get_services - о запущенных сервисах\n')


def ssh_connect(host: str, user: str, passwd: str, port: int):
    global client
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=user, password=passwd, port=port)


def stop(update: Update, context):
    update.message.reply_text("Функция остановлена")
    return ConversationHandler.END


def disconnect(update: Update, context):
    global client
    update.message.reply_text("SSH сессия остановлена")
    client.close()
    return ConversationHandler.END


def get_repl_logs(update: Update, context):
    try:
        ssh_connect(RM_HOST, RM_USER, RM_PASSWORD, int(RM_PORT))
        execute_command('docker logs db_repl_image --tail 15', update)
        client.close()
    except Exception as e:
        update.message.reply_text("Не удалось установить соединение с сервером")
        update.message.reply_text(f"Причина: {e}")


def db_query(update, sql, select: bool):
    try:
        conn = psycopg2.connect(dbname=DB_DATABASE, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS emails(id SERIAL PRIMARY KEY, email VARCHAR(50));")
        cursor.execute("CREATE TABLE IF NOT EXISTS phones(id SERIAL PRIMARY KEY, numbers VARCHAR(15));")
        cursor.execute(sql)
        if select:
            for row in cursor:
                update.message.reply_text(row)
        else:
            update.message.reply_text("Данные успешно записаны!")
    except Exception as e:
        update.message.reply_text(f"Ошибка при работе с PostgreSQL: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()


def get_emails(update: Update, context):
    db_query(update, 'select * from emails;', True)


def get_phone_numbers(update: Update, context):
    db_query(update, 'select * from phones;', True)


def execute_command(command, update):
    stdin, stdout, stderr = client.exec_command(command)
    error = stderr.read().decode()
    output = stdout.read().decode()
    if error:
        update.message.reply_text(error)
    if output:
        update.message.reply_text(output)


def get_apt_list(update: Update, context):
    user_input = update.message.text
    if user_input == "ALL":
        execute_command('apt list | head -n 5', update)
    else:
        execute_command(f'apt show {user_input}', update)
    return COMMAND_HANDLER


def ssh_commands(update: Update, context):
    user_input = update.message.text[1:]
    if user_input == 'get_release':
        execute_command('lsb_release -a', update)
    elif user_input == 'get_uname':
        execute_command('uname -a', update)
    elif user_input == 'get_uptime':
        execute_command('uptime', update)
    elif user_input == 'get_df':
        execute_command('df', update)
    elif user_input == 'get_free':
        execute_command('free', update)
    elif user_input == 'get_mpstat':
        execute_command('mpstat', update)
    elif user_input == 'get_w':
        execute_command('w', update)
    elif user_input == 'get_auths':
        execute_command('last -n 10', update)
    elif user_input == 'get_critical':
        execute_command('journalctl -p crit -n 5 | tail', update)
    elif user_input == 'get_ps':
        execute_command('ps', update)
    elif user_input == 'get_ss':
        execute_command('ss -tulpn', update)
    elif user_input == 'get_apt_list':
        update.message.reply_text("Введите название пакета, иноформацию о котором вы хотите получить")
        update.message.reply_text("Либо введите \'ALL\' для получения информации обо всех пакетах")
        return GET_APT_LIST
    elif user_input == 'get_services':
        execute_command('systemctl list-units --type service | head -n 5', update)
    elif user_input == 'help_ssh':
        help_ssh(update, context)
    elif user_input == 'stop':
        update.message.reply_text("SSH сессия остановлена")
        client.close()
        return ConversationHandler.END
    else:
        update.message.reply_text("Неверная команда!")


#def connect_command(update: Update, context):
#    update.message.reply_text('Для подключения к SSH-серверу введите через пробел IP-адрес, имя пользователя, пароль и порт: ')
#    return CONNECT


def connect(update: Update, context):
    user_input = update.message.text.split(" ")
    try:
        ssh_connect(RM_HOST, RM_USER, RM_PASSWORD, int(RM_PORT))
        update.message.reply_text("Введите команду для получения информации о системе (/help_ssh - для справки):")
        return COMMAND_HANDLER
    except Exception as e:
        update.message.reply_text("Не удалось установить соединение с сервером")
        update.message.reply_text(f"Причина: {e}")
        return ConversationHandler.END


def verify_password_command(update: Update, context):
    update.message.reply_text('Введите пароль для проверки\n/stop для остановки: ')
    return CHECK_PASSWORD


def verify_password(update: Update, context):
    user_input = update.message.text
    passRegex = re.compile(r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()])(.{8,})')
    if re.match(passRegex, user_input):
        update.message.reply_text("Пароль сложный")
    else:
        update.message.reply_text("Пароль простой")
    return


def find_emails_command(update: Update, context):
    update.message.reply_text('Введите текст для поиска email-адресов\n/stop для остановки: ')
    return FIND_EMAILS


def write_emails(update: Update, context):
    user_input = update.message.text.lower()
    if user_input == "да":
        for row in emailList:
            db_query(update, f'insert into emails(email) values(\'{row}\');', False)
    return FIND_EMAILS


def find_emails(update: Update, context):
    global emailList
    user_input = update.message.text

    emailRegex = re.compile(r'[\w.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    emailList = emailRegex.findall(user_input)
    if not emailList:
        update.message.reply_text('Электронные адреса не найдены')
        return

    emails = ''
    for i in range(len(emailList)):
        emails += f'{i + 1}. {emailList[i]}\n'

    update.message.reply_text(emails)  # Отправляем сообщение пользователю
    update.message.reply_text("Записать обнаруженные электронные адреса в базу данных? (Да/Нет)")
    return INSERT_EMAILS


def find_phone_numbers_command(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров:')
    return FIND_NUMBERS


def write_phones(update: Update, context):
    user_input = update.message.text.lower()
    if user_input == "да":
        for row in phoneNumberToInsert:
            db_query(update, f'insert into phones(numbers) values(\'{row}\');', False)
    return FIND_NUMBERS


def find_phone_numbers(update: Update, context):
    global phoneNumberToInsert
    user_input = update.message.text  # Получаем текст, содержащий(или нет) номера телефонов
    phoneNumRegex = re.compile(r'(8|\+7)?([ \-])?(\(\d{3}\)|\d{3})([ \-])?(\d{3})([ \-])?(\d{2})([ \-])?(\d{2})')
    phoneNumberList = phoneNumRegex.findall(user_input)  # Ищем номера телефонов
    phoneNumberToInsert = []
    if not phoneNumberList:  # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return
    phoneNumbers = ''  # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        string_numbers = ''
        phoneNumbers += f'{i + 1}. '
        for j in range(len(phoneNumberList[i])):
            phoneNumbers += f'{phoneNumberList[i][j]}'  # Записываем очередной номер
            string_numbers += phoneNumberList[i][j]
        phoneNumberToInsert.append(string_numbers)
        phoneNumbers += f'\n'
    update.message.reply_text(phoneNumbers)  # Отправляем сообщение пользователю
    update.message.reply_text("Записать обнаруженные номера в базу данных? (Да/Нет)")
    return INSERT_PHONES


def echo(update: Update, context):
    update.message.reply_text("Используй /help для получения справки...")
