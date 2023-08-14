import csv

from stride_detector.logging.logger_base import *


class CSVLogger(BaseLogger):
    def __init__(self, log_path=''):
        super().__init__()
        if log_path == '':
            t = datetime.now()
            t = t.strftime('%Y%m%d_%H%M%S')
            self.log_path = f'./logs/{t}.csv'
        else:
            self.log_path = log_path
        if not os.path.exists('./logs'):
            os.makedirs('./logs')

        # one entry per dialog (USER + ASSISTANT)
        self.log: List[Dict[str, Union[int, str]]] = []
        self.header = ["Message#", "USER", "ASSISTANT", "Action", "Coverage Rate", "Coverage Plan"]
        self.logged_index = 0  # log index for logging

    def save_info(self, info: List[Union[str, int]]):
        # save experiment info
        with open(self.log_path, 'a+', encoding='UTF8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(info)
            dict_writer = csv.DictWriter(f, fieldnames=self.header)
            dict_writer.writeheader()

    def save_log(self):
        with open(self.log_path, 'a+', encoding='UTF8', newline="") as f:
            dict_writer = csv.DictWriter(f, fieldnames=self.header)
            while self.logged_index < len(self.log):
                self.log[self.logged_index]['Message#'] = self.logged_index + 1

                dict_writer.writerow(self.log[self.logged_index])

                self.logged_index += 1
