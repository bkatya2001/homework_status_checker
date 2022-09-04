import logging
import os
import requests
import sys
import time

import telegram
from dotenv import load_dotenv
from http import HTTPStatus

import exceptions

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

errors = {
    'get_api_answer': False,
    'check_response': False,
    'parse_status': False,
    'main': False
}


def send_message(bot, message):
    """Отправка сообщения."""
    logging.info('Совершается попытка отправить сообщение')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение успешно отправлено')
    except Exception as e:
        raise exceptions.SendMessageException('Ошибка при отправке сообщения')
        logging.error('Ошибка при отправке сообщения: ' + str(e))


def get_api_answer(current_timestamp):
    """Обращение к API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        if homework_statuses.status_code == HTTPStatus.OK:
            errors['get_api_answer'] = False
            return homework_statuses.json()
        else:
            raise exceptions.StrangeAPIAnswerException('Эндпоинт недоступен')
    except Exception:
        raise exceptions.StrangeAPIAnswerException('Эндпоинт недоступен')


def check_response(response):
    """Проверка ответа."""
    if len(response) == 0 or None:
        raise exceptions.EmptyDictException('Пустой словарь')
    if type(response) == dict:
        if 'homeworks' in response:
            if type(response['homeworks']) == list:
                errors['check_response'] = False
                return response['homeworks']
    else:
        raise TypeError
    raise exceptions.NoKeysException('Отсутствуют необходимые ключи')


def parse_status(homework):
    """Обработка ответа."""
    homework_name = homework['homework_name']
    homework_status = homework['status']

    try:
        verdict = HOMEWORK_VERDICTS[homework_status]
        errors['parse_status'] = False
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception:
        raise exceptions.UnknownStatusException(
            'Неизвестный статус домашнего задания'
        )


def check_tokens():
    """Проверка токенов."""
    if PRACTICUM_TOKEN is None:
        logging.critical('Отсутствует токен практикума')
        return False
    if TELEGRAM_TOKEN is None:
        logging.critical('Отсутствует токен бота')
        return False
    if TELEGRAM_CHAT_ID is None:
        logging.critical('Отсутствует id чата')
        return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise exceptions.NoneTokensException(
            'Отсутствуют переменные окружения'
        )

    current_timestamp = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks is not None:
                if len(homeworks) == 0:
                    logging.debug('Новых статусов нет')
                else:
                    for homework in homeworks:
                        message = parse_status(homework)
                        if message is not None:
                            send_message(bot, message)
            errors['main'] = False
            current_timestamp = int(time.time())
        except exceptions.StrangeAPIAnswerException:
            logging.error('Эндпоинт недоступен')
            if not errors['get_api_answer']:
                errors['get_api_answer'] = True
                send_message(bot, 'Эндпоинт недоступен')
        except exceptions.NoKeysException:
            logging.error('Отсутствуют необходимые ключи')
            if not errors['check_response']:
                errors['check_response'] = True
                send_message(bot, 'Отсутствуют необходимые ключи')
        except exceptions.UnknownStatusException:
            logging.error(
                'Неизвестный статус домашнего задания'
            )
            if not errors['parse_status']:
                errors['parse_status'] = True
                send_message(
                    bot,
                    'Неизвестный статус домашнего задания'
                )
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if not errors['main']:
                errors['main'] = True
                send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='bot.log',
        filemode='a',
        format='%(asctime)s, %(levelname)s, %(message)s'
    )
    handler = logging.StreamHandler(stream=sys.stdout)
    main()
