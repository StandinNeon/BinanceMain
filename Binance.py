import asyncio
import json
import websockets
import datetime


class BinanceMain:
    """
    Обьект создает подключение к Binance WebSocket и отслеживает актуальную стоимость фьючерса. Отслеживает максимальное
    значение за последний час. При падении максимального значения на 1% уведомляет об этом в консоль.
    """

    def __init__(self):
        """
        :arg self._uri: Адрес доступа к потоку websocket binance, в :param streams: передается как единичное значение,
                        так и список.
        :arg self.__start_time: Время запуска программы
        :arg self.__period_start_time: Время начала периода
        :arg self.__max_value: Максимальное значение фьючерса
        :arg self.__max_value_write_time: Время записи максимального значения
        :arg self._period: Период за который отслеживается максимальное значение и его падение
        :arg self._price_down_percent: Процент падения для срабатывание триггера
        :arg self._price: Значение фьючерса
        :arg self.__price_list_last_hour: Список значений фьючерса за последний час
        """
        self._uri = "wss://stream.binance.com:9443/stream?streams=xrpusdt@ticker"
        self.__start_time = None
        self.__period_start_time = None
        self.__max_value = 0
        self.__max_value_write_time = None
        self._period = datetime.timedelta(hours=1)
        self._price_down_percent = 1
        self._price = None
        self.__price_list_last_hour = {}

    def run(self):
        """
        Метод запуска работы
        """
        self.__start_time = datetime.datetime.now()
        asyncio.run(self.main())

    async def main(self):
        """
        Метод основной логики работы
        """
        async with websockets.connect(self._uri) as self.conn:
            while True:
                try:
                    self._price = float(json.loads(await self.conn.recv())['data']['c'])
                    self.processing()
                    print(self._price)
                except websockets.ConnectionClosedOK:
                    break

    def processing(self):
        """
        Порядок запуска методов
        """
        self.check_max_price()
        self.check_price_down()
        self.reload_time()
        self.price_list()
        self.check_max_price_time()

    @staticmethod
    def time_now():
        return datetime.datetime.now()

    def price_list(self):
        """
        Работа со списком значений за период
        """
        self.__price_list_last_hour[self._price] = self.time_now().isoformat()
        self.__price_list_last_hour = dict(
            filter(lambda x: True if x[1] > self.__period_start_time.isoformat() else False,
                   self.__price_list_last_hour.items()))

    def check_max_price(self):
        """
        Проверяет, является ли значение максимальным
        """
        if self._price > self.__max_value:
            self.__max_value_write_time = self.time_now()
            self.__max_value = self._price

    def check_max_price_time(self):
        """
        Проверяет актуальность максимального значения
        """
        if self.__max_value_write_time < self.__period_start_time:
            self.__max_value = max(self.__price_list_last_hour.keys())

    def check_price_down(self):
        """
        Проверяет процент падения текущего значения от максимального
        """
        if self._price < (self.__max_value * (1 - self._price_down_percent / 100)):
            print('Price down!')

    def reload_time(self):
        """
        Контроль времени начала периода отслеживания
        """
        if self.time_now() - self._period < self.__start_time:
            self.__period_start_time = self.__start_time
        else:
            self.__period_start_time = self.time_now() - self._period


if __name__ == '__main__':
    BinanceMain().run()
