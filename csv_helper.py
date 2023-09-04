import csv
from models.llm_gpt import num_tokens_from_messages


def add_token_cnt(filename: str):
    with open(filename, "r", newline="") as fin:
        pass
        # with open()


def print_token_cnt_avg(filename: str):
    header = [
        "Total Message#",
        "Dialog #",
        "Message #",
        "USER",
        "ASSISTANT",
        "Action",
        "Coverage Rate",
        "Coverage Plan",
    ]
    input_token = []
    output_token = []
    with open(filename, "r", newline="") as f:
        reader = csv.DictReader(f, fieldnames=header)
        for i, row in enumerate(reader):
            if i == 0:
                continue
            input_token.append(num_tokens_from_messages([{"user": row["USER"]}]))
            output_token.append(
                num_tokens_from_messages([{"assistant": row["ASSISTANT"]}])
            )
        print(sum(input_token) / len(input_token))
        print(sum(output_token) / len(output_token))


def main():
    filenames = ["./ibex_decoder/logs/20230829_113216(gpt_harderbins_3).csv"]
    for filename in filenames:
        print_token_cnt_avg(filename)


if __name__ == "__main__":
    main()
