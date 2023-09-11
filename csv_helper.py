import csv
import os.path

from models.llm_gpt import num_tokens_from_messages


def add_token_cnt(filename: str):
    with open(filename, "r", newline="") as fin:
        pass
        # with open()


def print_old_token_cnt_avg(filename: str):
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
            if i <= 1:
                continue
            input_token.append(num_tokens_from_messages([{"user": row["USER"]}]))
            output_token.append(
                num_tokens_from_messages([{"assistant": row["ASSISTANT"]}])
            )
        print(sum(input_token) / len(input_token))
        print(sum(output_token) / len(output_token))


def print_new_msg_for_token_bound(filename: str, token_bound: int = 1254098):
    header = [
        "Total Message#",
        "Dialog #",
        "Message #",
        "Total Token Cnt",
        "USER",
        "Input Token Cnt",
        "ASSISTANT",
        "Output Token Cnt",
        "Action",
        "Coverage Rate",
        "Coverage Plan",
    ]
    total_token = []
    with open(filename, "r", newline="") as f:
        reader = csv.DictReader(f, fieldnames=header)
        for i, row in enumerate(reader):
            if i <= 1:
                continue
            total_token.append(int(row["Total Token Cnt"]))
            if sum(total_token) >= token_bound:
                print(
                    f"Total msg#: {row['Total Message#']}\n"
                    f"Total token cnt: {sum(total_token)} / {token_bound}\n"
                    f"Coverage Rate: {row['Coverage Rate']}\n"
                    f"Coverage Plan: {row['Coverage Plan']}\n"
                )
                break


def generate_summary_4SD(dir_path: str):
    header = ["Trial #", "Message cnt", "Token cnt", "Coverage rate", "Coverage plan"]
    data = []
    prefix = f"./stride_detector/logs/{dir_path}_budget/"
    if os.path.exists(f"{prefix}{dir_path}_summary.csv"):
        t = input("Summary file with the same name already exists. Overwrite? [y/n]:")
        while t not in ["y", "n"]:
            t = input("Please enter [y/n]:")
        if t == "n":
            print("Overwrite cancelled.")
            return

    log_header = [
        "Total Message#",
        "Dialog #",
        "Message #",
        "Total Token Cnt",
        "USER",
        "Input Token Cnt",
        "ASSISTANT",
        "Output Token Cnt",
        "Action",
        "Coverage Rate",
        "Coverage Plan",
    ]

    with open(
        f"{prefix}{dir_path}_summary.csv", "w+", encoding="UTF8", newline=""
    ) as f:
        writer = csv.writer(f)
        writer.writerow(header)
        trial_cnt = 1
        while os.path.exists(f"{prefix}{dir_path}_trial_{trial_cnt}.csv"):
            filename = f"{prefix}{dir_path}_trial_{trial_cnt}.csv"
            with open(filename, "r", newline="") as fin:
                reader = csv.DictReader(fin, fieldnames=log_header)
                msg_cnt = 0
                token_cnt = 0
                for i, row in enumerate(reader):
                    if i <= 1:
                        continue
                    # print(i, row)
                    msg_cnt += 1
                    token_cnt += int(row["Total Token Cnt"])
                    coverage_rate = int(row["Coverage Rate"])
                    coverage_plan = row["Coverage Plan"]

                data.append(
                    [trial_cnt, msg_cnt, token_cnt, coverage_rate, coverage_plan]
                )

            writer.writerow(data[-1])
            trial_cnt += 1


def main():
    # filenames = ["./ibex_decoder/logs/20230829_113216(gpt_harderbins_3).csv"]
    # for filename in filenames:
    #     print_token_cnt_avg(filename)

    dir_path = "20230911_100453"
    generate_summary_4SD(dir_path)

    # print_new_msg_for_token_bound(
    #     filename="ibex_decoder/logs/20230907_201949_budget(Template2, IDAdaNew, Stable, Best3 with harder bins, IDAdaR)/20230907_201949_trial_6.csv"
    # )


if __name__ == "__main__":
    main()
