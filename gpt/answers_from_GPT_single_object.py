import sys
sys.path.append('../')

from mllm import local_llm, GPT4, GPT4_Rare2Frequent
import torch
import argparse
import json


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default="GPT4",
        type=str,
    )
    parser.add_argument(
        "--test_file",
        type=str,
        default="../test/single_object_rare_attribute3_4action.txt",
        help="Test file used for generation",
    )
    parser.add_argument(
        "--out_path",
        type=str,
        nargs="?",
        default="../test_gpt/rarebench_single_4action_gpt4.txt",
        help="output file path",
    )
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    api_key = "sk-proj-IAZ4GP2D8ZiWo9yichrqT3BlbkFJTTlc56ffedaIrc5Y3ytu" # KRAFTON research

    ## User input
    test_file = args.test_file
    test_case = test_file.split('/')[-1].split('.')[0]
    with open(test_file) as f:
        prompts = [line.rstrip() for line in f]

    result = {}
    for i, prompt in enumerate(prompts):

        # Get GPT responses
        if args.model == "GPT4":
            r2f_prompts = GPT4_Rare2Frequent(prompt, key=api_key)

            result[prompt] = r2f_prompts

    with open(args.out_path, 'w') as f:
        json.dump(result, f, indent=4)
    

if __name__ == "__main__":
    main()