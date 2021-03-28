#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Создайте файл "/home/pi/dev/application.yml" со следующим содержимым:
"""
"""
user:
    admin_group: -311647268
    bot_token: xxxxxx
    camera_qty: кол_во_камер
"""
import logging
import glob
import os, time, shutil, paramiko, sys
import telegram
import yaml

import paho.mqtt.client as mqtt
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


conf = yaml.safe_load(open("/home/pi/dev/application.yml"))
admin_group = conf["user"]["admin_group"]
bot_token = conf["user"]["bot_token"]
camera_qty = conf["user"]["camera_qty"] + 1
cam_topic = "cam_debug"
help_message = """
/ping_cam - запросить ответ от каждой камеры
/send_photo - получить последнее фото с каждой камеры
/take_photo - снять фото со всех камер
/start_caption - начать серийную съёмку
/stop_caption - закончит серийную съёмку
/set_interval_1500 - установить интервал съёмки 1500 мс
/clear_gallery - удалить ВСЕ ФОТО ИЗ ПАМЯТИ

/reboot - перезагрузить сервер и камеры
/restart_router - перезагрузить вспомогательный роутер
/restart_service - перезагрузить бота

/help - показать эту справку
"""
def start(update, context):
    if update.message.chat.id == admin_group:
        send_telegram_message(help_message)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Запрещено!")

def help_command(update, context):
    if update.message.chat.id == admin_group:
        send_telegram_message(help_message)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Запрещено!")

def reboot(update, context):
    if update.message.chat.id == admin_group:
        send_telegram_message("Перезагружаем камеры")
        for i in range(1, camera_qty):
            client = mqtt.Client()
            client.connect("localhost", 1883, 60)
            client.publish("cam_0{}".format(i), payload="restart")
        time.sleep(1)
        send_telegram_message("Перезагружаем вспомогательный роутер")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('192.168.1.10', port=22, username='root', password='tAUmAtAt93')
        client.exec_command('reboot now')
        client.close()
        time.sleep(1)
        send_telegram_message("Перезагружаем сервер")
        os.system("reboot now");
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Запрещено!")

def restart_router(update, context):
    if update.message.chat.id == admin_group:
        send_telegram_message("Перезагружаем роутер")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('192.168.1.10', port=22, username='root', password='tAUmAtAt93')
        client.exec_command('reboot now')
        client.close()
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Запрещено!")
    

def restart_service(update, context):
    if update.message.chat.id == admin_group:
        send_telegram_message("Перезагрузка скрипта...")
        for i in range(1, camera_qty):
            client = mqtt.Client()
            client.connect("localhost", 1883, 60)
            client.publish("cam_0{}".format(i), payload="restart")
        os.system("sudo systemctl restart esp_cam");
        time.sleep(100000)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Запрещено!")

def ping_cam(update, context):
    if update.message.chat.id == admin_group:
        send_telegram_message("Ждём ответа от камер...")
        for i in range(1, camera_qty):
            client = mqtt.Client()
            client.connect("localhost", 1883, 60)
            client.publish("cam_0{}".format(i), payload="ping")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Запрещено!")

def clear_gallery(update, context):
    if update.message.chat.id == admin_group:
        for i in range(1, camera_qty):
            folder = "/var/www/html/cam_0{}".format(i)
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
        send_telegram_message("Галерея очищена.\n{}".format(help_message))
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Запрещено!")

def take_photo(update, context):
    if update.message.chat.id == admin_group:
        for i in range(1, camera_qty):
            client = mqtt.Client()
            client.connect("localhost", 1883, 60)
            client.publish("cam_0{}".format(i), payload="take_photo")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Запрещено!")

def send_photo(update, context):
    if update.message.chat.id == admin_group:
        for i in range(1, camera_qty):
            list_of_files = glob.glob("/var/www/html/cam_0{}/*".format(i))
            if list_of_files:
                latest_file = max(list_of_files, key=os.path.getctime)
                context.bot.send_document(chat_id=update.effective_chat.id, document=open(latest_file, 'rb'), caption=latest_file.replace("/var/www/html/", ""))
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Запрещено!")

def start_caption(update, context):
    if update.message.chat.id == admin_group:
        for i in range(1, camera_qty):
            client = mqtt.Client()
            client.connect("localhost", 1883, 60)
            client.publish("cam_0{}".format(i), payload="start_caption")

def stop_caption(update, context):
    if update.message.chat.id == admin_group:
        for i in range(1, camera_qty):
            client = mqtt.Client()
            client.connect("localhost", 1883, 60)
            client.publish("cam_0{}".format(i), payload="stop_caption")
            list_of_files = glob.glob("/var/www/html/cam_0{}/*".format(i))
            if list_of_files:
                latest_file = max(list_of_files, key=os.path.getctime)
                context.bot.send_document(chat_id=update.effective_chat.id, document=open(latest_file, 'rb'), caption=latest_file.replace("/var/www/html/", ""))

def unknown(update, context):
    if update.message.chat.id == admin_group:
        bot_command = update.message.text.replace("@esp_illintsi_bot", "")
        client = mqtt.Client()
        client.connect("localhost", 1883, 60)
        for i in range(1, camera_qty):
            if "/cam_0{}".format(i) in bot_command:
                client.publish("cam_0{}".format(i), payload=bot_command.replace("/cam_0{}".format(i), ""))
            if "/set_interval_" in bot_command:
                client.publish("cam_0{}".format(i), payload=bot_command.replace("/", ""))

    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Запрещено!")

def on_connect(client, userdata, flags, rc):
    client.subscribe("#")
    send_telegram_message("Система загружена.\n{}".format(help_message))
    for i in range(1, camera_qty):
            client = mqtt.Client()
            client.connect("localhost", 1883, 60)
            client.publish("cam_0{}".format(i), payload="take_photo")
            client.publish("cam_0{}".format(i), payload="set_interval_30000")
            client.publish("cam_0{}".format(i), payload="start_caption")

def send_telegram_message(tg_msg):
    bot = telegram.Bot(token=bot_token)
    bot.send_message(chat_id=admin_group, text=tg_msg, disable_notification=False)

def on_message(client, userdata, msg):
    if (msg.topic == cam_topic):
        for i in range(1, camera_qty):
            if "cam_0{}".format(i) in (msg.payload).decode("utf-8"):
                cam_identity = "cam_0{}".format(i)
                cam_response = (msg.payload).decode("utf-8").replace(cam_identity, "")
                if cam_response == "start_caption":
                    send_telegram_message("{} начата серийная съёмка".format(cam_identity.replace("cam_", "Для камеры ")))
                if cam_response == "stop_caption":
                    send_telegram_message("{} остановлена серийная съёмка".format(cam_identity.replace("cam_", "Для камеры ")))
                if cam_response == "take_photo":
                    send_telegram_message("{}...".format(cam_identity.replace("cam_", "Делаем фото с камеры ")))
                    bot = telegram.Bot(token=bot_token)
                    list_of_files = glob.glob("/var/www/html/cam_0{}/*".format(i))
                    if list_of_files:
                        latest_file = max(list_of_files, key=os.path.getctime)
                        bot.send_document(chat_id=admin_group, document=open(latest_file, 'rb'), caption=latest_file.replace("/var/www/html/", ""))
                if cam_response == "restart":
                    send_telegram_message("{}".format(cam_identity.replace("cam_", "Перезагружаем камеру ")))
                if cam_response == "pong":
                    send_telegram_message("{} активна".format(cam_identity.replace("cam_", "Камера ")))
                if cam_response == "online":
                    send_telegram_message("{} активна".format(cam_identity.replace("cam_", "Камера ")))
                if "set_interval_" in cam_response:
                    send_telegram_message("{} установлен инервал съёмки {} мс".format(cam_identity.replace("cam_", "Для камеры "), cam_response.replace("set_interval_", "")))
        

def main():
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("ping_cam", ping_cam))
    dp.add_handler(CommandHandler("send_photo", send_photo))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("clear_gallery", clear_gallery))
    dp.add_handler(CommandHandler("reboot", reboot))
    dp.add_handler(CommandHandler("restart_router", restart_router))
    dp.add_handler(CommandHandler("restart_service", restart_service))
    dp.add_handler(CommandHandler("take_photo", take_photo))
    dp.add_handler(CommandHandler("start_caption", start_caption))
    dp.add_handler(CommandHandler("stop_caption", stop_caption))
    dp.add_handler(MessageHandler(Filters.command, unknown))
    #dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    updater.start_polling()
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.loop_forever()
    updater.idle()


if __name__ == '__main__':
    main()