from loggers.logger_base import *


class TXTLogger(BaseLogger):
    def __init__(self, log_path=""):
        super().__init__()
        if log_path == "":
            t = datetime.now()
            t = t.strftime("%Y%m%d_%H%M%S")
            self.log_path = f"./logs/{t}.txt"
        else:
            self.log_path = log_path

        t = self.log_path.split("/")
        self.log_prefix = t[0] + "/" + t[1]
        if not os.path.exists(self.log_prefix):
            os.makedirs(self.log_prefix)

        # elements:
        # {role: info, content: [agent_info]},
        # {role: ..., content: ...},
        # {role: coverage, content: [coverage_plan]}
        # {role: stop, content: done | max stimuli number}
        # {role: reset}
        self.log: List[List[Dict[str, Union[str, dict]]]] = [[]]
        self.logged_index = 0  # log index for logging

        self.logged_dialog_index = 1  # dialog index for logging
        self.logged_msg_index = 0  # dialog index for logging
        self.logged_total_msg_cnt = 0  # dialog index for logging

    def save_log(self):
        with open(self.log_path, "a+") as f:
            while self.logged_index < len(self.log[-1]):
                rec = self.log[-1][self.logged_index]

                if rec["role"] == "info":
                    agent_info: Dict[str, str] = rec["content"]
                    for k, v in agent_info.items():
                        f.write(f"{k}: {v}\n")
                    f.write("\n")

                elif rec["role"] == "coverage":
                    coverage: Dict[str, int] = rec["content"]
                    coverage_plan = {k: v for (k, v) in coverage.items() if v > 0}
                    f.write(f"Coverage rate: {len(coverage_plan)} / {len(coverage)}\n")
                    f.write(f"Coverage plan: {coverage_plan}\n\n")

                elif rec["role"] == "stop":
                    f.write(f'Stop: {rec["content"]}\n\n')

                elif rec["role"] == "reset":
                    f.write("\n<<<<< RESET >>>>>\n\n\n")

                else:
                    if rec["role"] == "user":
                        self.logged_msg_index += 1
                        self.logged_total_msg_cnt += 1
                    f.write(f"Dialog index: {self.logged_dialog_index}\n")
                    f.write(f"Message index: {self.logged_msg_index}\n")
                    f.write(f"Total msg cnt: {self.logged_total_msg_cnt}\n")
                    if rec["role"] != "system":
                        f.write(f'Token counts: {rec["token cnt"]}\n')
                    f.write(f'Role: {rec["role"]}\n')
                    f.write(f'Content: {rec["content"]}\n\n')

                self.logged_index += 1
