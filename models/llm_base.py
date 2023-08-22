from abc import abstractmethod
from typing import *


class BaseLLM:
    REMAIN_ITER_NUM = 3

    def __init__(self, system_prompt: str = ""):
        self.system_prompt = system_prompt
        self.temperature = 1
        self.top_p = 1

        # 'msg': messages, 'hits': hit #, 'id': msg id
        self.best_messages: List[Dict[str, Union[Tuple[dict, dict], int]]] = []
        self.total_msg_cnt = 0

    @abstractmethod
    def __call__(self, prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def reset(self):
        raise NotImplementedError

    def append_successful(
        self, prompt: Dict[str, str], response: Dict[str, str], cur_coverage: int
    ):
        self.best_messages.append(
            {"msg": (prompt, response), "hit": cur_coverage, "id": self.total_msg_cnt}
        )

    def update_successful(self, new_coverage: int):
        self.best_messages[-1]["hit"] = new_coverage - self.best_messages[-1]["hit"]
        self.best_messages = sorted(
            self.best_messages, key=lambda d: (d["hit"], d["id"]), reverse=True
        )[: BaseLLM.REMAIN_ITER_NUM]

    # TODO: keep more best msgs & then sample 3 from them
    def _select_successful(self) -> List[Dict[str, str]]:
        self.best_messages.sort(key=lambda d: d["id"])
        return [msg for entry in self.best_messages for msg in entry["msg"]]
