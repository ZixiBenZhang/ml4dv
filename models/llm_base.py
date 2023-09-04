from abc import abstractmethod
from typing import *

import numpy as np

from global_shared_types import GlobalCoverageDatabase


class BaseLLM:
    REMAIN_ITER_NUM = 3

    def __init__(self, system_prompt: str = ""):
        self.system_prompt = system_prompt
        self.temperature = 1
        self.top_p = 1

        # 'msg': messages, 'hits': hit #, 'id': msg id
        self.best_messages: List[Dict[str, Union[Tuple[dict, dict], int, float]]] = []
        self.total_msg_cnt = 0

    @abstractmethod
    def __call__(self, prompt: str) -> Tuple[str, Tuple[int, int, int]]:
        raise NotImplementedError

    @abstractmethod
    def reset(self):
        raise NotImplementedError

    # Called by agent when LLM had generated response
    def append_successful(
        self,
        prompt: Dict[str, str],
        response: Dict[str, str],
        cur_coverage: GlobalCoverageDatabase,
    ):
        self.best_messages.append(
            {
                "msg": (prompt, response),
                "hit": cur_coverage.get_coverage_score(),
                "id": self.total_msg_cnt,
            }
        )

    # Called by agent when the response's coverage has been completely computed
    def update_successful(self, new_coverage: GlobalCoverageDatabase):
        self.best_messages[-1]["hit"] = (
            new_coverage.get_coverage_score() - self.best_messages[-1]["hit"]
        )
        self.best_messages = sorted(
            self.best_messages, key=lambda d: (d["hit"], d["id"]), reverse=True
        )
        if (
            len(self.best_messages) >= BaseLLM.REMAIN_ITER_NUM * 3
            and self.best_messages[BaseLLM.REMAIN_ITER_NUM * 3 - 1]["hit"]
            == self.best_messages[0]["hit"]
        ):
            self.best_messages = list(
                filter(
                    lambda d: d["hit"] == self.best_messages[0]["hit"],
                    self.best_messages,
                )
            )
        else:
            self.best_messages = self.best_messages[: BaseLLM.REMAIN_ITER_NUM * 3]

    # Called by models during conversation compression
    def _select_successful(self, n_best: int = 3) -> List[Dict[str, str]]:
        if len(self.best_messages) < n_best:
            return [
                msg
                for entry in sorted(self.best_messages, key=lambda d: d["id"])
                for msg in entry["msg"]
            ]

        return [
            msg
            for entry in sorted(
                list(np.random.choice(self.best_messages, n_best, replace=False)),
                key=lambda d: d["id"],
            )
            for msg in entry["msg"]
        ]
