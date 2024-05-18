import definitions as defs


def main():
    updater = defs.Updater(defs.TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога телефонных номеров
    convHandlerFindPhoneNumbers = defs.ConversationHandler(
        entry_points=[defs.CommandHandler('find_phone_numbers', defs.find_phone_numbers_command)],
        states={
            defs.FIND_NUMBERS: [
                defs.MessageHandler(defs.Filters.text & ~defs.Filters.command, defs.find_phone_numbers),
                defs.CallbackQueryHandler(defs.find_phone_numbers)
            ],
            defs.INSERT_PHONES: [defs.MessageHandler(defs.Filters.regex('(^Да$|^ДА$|^да$|^Нет$|^НЕТ$|^нет$)'
                                                                        ), defs.write_phones)]
        },
        fallbacks=[
            defs.CommandHandler("stop", defs.stop)
        ]
    )

    convHandlerFindEmails = defs.ConversationHandler(
        entry_points=[defs.CommandHandler('find_email', defs.find_emails_command)],
        states={
            defs.FIND_EMAILS: [
                defs.MessageHandler(defs.Filters.text & ~defs.Filters.command, defs.find_emails),
                defs.CallbackQueryHandler(defs.find_emails)
            ],
            defs.INSERT_EMAILS: [defs.MessageHandler(defs.Filters.regex('(^Да$|^ДА$|^да$|^Нет$|^НЕТ$|^нет$)'),
                                                     defs.write_emails)]
        },
        fallbacks=[
            defs.CommandHandler("stop", defs.stop)
        ]
    )

    convHandlerPassword = defs.ConversationHandler(
        entry_points=[defs.CommandHandler('verify_password', defs.verify_password_command)],
        states={
            defs.CHECK_PASSWORD: [defs.MessageHandler(defs.Filters.text & ~defs.Filters.command, defs.verify_password)],
        },
        fallbacks=[defs.CommandHandler("stop", defs.stop)]
    )

    convHandlerconnect = defs.ConversationHandler(
        entry_points=[defs.CommandHandler('connect', defs.connect)],
        states={
            defs.COMMAND_HANDLER: [defs.MessageHandler(defs.Filters.command, defs.ssh_commands)],
            defs.GET_APT_LIST: [defs.MessageHandler(defs.Filters.text & ~defs.Filters.command, defs.get_apt_list)]
        },
        fallbacks=[]
    )

    # Регистрируем обработчики команд
    dp.add_handler(defs.CommandHandler("start", defs.start))
    dp.add_handler(defs.CommandHandler("help", defs.help_command))
    dp.add_handler(defs.CommandHandler("get_repl_logs", defs.get_repl_logs))
    dp.add_handler(defs.CommandHandler("get_emails", defs.get_emails))
    dp.add_handler(defs.CommandHandler("get_phone_numbers", defs.get_phone_numbers))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerconnect)
    dp.add_handler(convHandlerPassword)

    # Регистрируем обработчик текстовых сообщений
    dp.add_handler(defs.MessageHandler(defs.Filters.text & ~defs.Filters.command, defs.echo))

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
