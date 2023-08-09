from stride_detector.logging.logger_base import *


class TXTLogger(BaseLogger):
    def __init__(self, log_path=''):
        super().__init__()
        if log_path == '':
            t = datetime.now()
            t = t.strftime('%Y%m%d_%H%M%S')
            self.log_path = f'./logs/{t}.txt'
        else:
            self.log_path = log_path

    # TODO: txt logger
    def save_log(self):
        if not os.path.exists('./logs'):
            os.makedirs('./logs')
        with open(self.log_path, 'a+') as f:
            while self.logged_index < len(self.log[-1]):
                rec = self.log[-1][self.logged_index]

                if rec['role'] == 'info':
                    agent_info: Dict[str, str] = rec['content']
                    for k, v in agent_info.items():
                        f.write(f'{k}: {v}\n')
                    f.write('\n')

                elif rec['role'] == 'coverage':
                    coverage: Dict[str, int] = rec['content']
                    coverage_plan = {k: v for (k, v) in coverage.items() if v > 0}
                    f.write(f'Coverage rate: {len(coverage_plan)} / {len(coverage)}\n')
                    f.write(f'Coverage plan: {coverage_plan}\n\n')

                elif rec['role'] == 'stop':
                    f.write(f'Stop: {rec["content"]}\n')

                else:
                    if rec['role'] == 'user':
                        self.logged_dialog_index += 1
                    f.write(f'Index: {self.logged_dialog_index}\n')
                    f.write(f'Role: {rec["role"]}\n')
                    f.write(f'Content: {rec["content"]}\n\n')

                self.logged_index += 1
