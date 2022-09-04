class NoneTokensException(Exception):
    """Исключение для отсутсвия токенов."""

    pass


class EmptyDictException(Exception):
    """Исключение для пустого словаря."""

    pass


class SendMessageException(Exception):
    """Исключение при отправке сообщения."""

    pass


class StrangeAPIAnswerException(Exception):
    """Исключение при статусе не 200 при работе с API."""

    pass


class NoKeysException(Exception):
    """Исключение при отсутствии необходимых ключей."""

    pass


class UnknownStatusException(Exception):
    """Исключение при неизвестном статусе."""

    pass
