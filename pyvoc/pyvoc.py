import argparse

import requests
from termcolor import cprint
import colorama

from pyvoc.check_config import read_config_file, check_config_dir
from pyvoc.dmanager import add_word_to_vocab, list_all_groups
from pyvoc.termoutput import revise_vocab, quiz, terminal_width

import textwrap


colorama.init()

"""
saving as dictionary in a same file or in two files.
maybe make two files. one for the word and the other saving different meanings in the dictionary
form, as printed to the console.
For now saving them in a json file.
"""


def parse_dictionary_response(response):
    lexicalEntries = response.json().get("results")[0]["lexicalEntries"]
    parsed_response = dict()
    examples = dict()
    for i in lexicalEntries:
        lexicalCategory = i["lexicalCategory"]
        try:
            definition = i["entries"][0]["senses"][0]["short_definitions"][0]
            try:
                example = i["entries"][0]["senses"][0]["examples"][0]["text"]
            except KeyError:
                example = "None"
        except KeyError:
            try:
                definition = i["entries"][0]["senses"][0]["crossReferenceMarkers"][0]
                try:
                    example = i["entries"][0]["senses"][0]["examples"][0]["text"]
                except KeyError:
                    example = "None"
            except Exception:
                print("No definition found")
        parsed_response[lexicalCategory] = definition
        examples[lexicalCategory] = example
    return parsed_response, examples


# red, green, yellow, blue, magenta, cyan, white
# bold, dark, underlined, blink, reverse, concealed


def pretty_print_definition(word, parsed_response, examples):
    print("")
    cprint(word + " ", color="magenta", attrs=["bold", "reverse"])
    for key in parsed_response:
        # x = wrapper.wrap(s)
        cprint(key + ":", color="green", end=" " * (16 - len(key)))
        width_left = terminal_width - 18
        sentences = textwrap.wrap(parsed_response[key], width=width_left)
        s_count = 1
        for sentence in sentences:
            if s_count == 1:
                print(sentence)
            else:
                print(" " * (17) + sentence)
            s_count += 1
        cprint("example:", color="yellow", end=" " * (16 - len("example")))
        sentences = textwrap.wrap(examples[key], width=width_left)
        s_count = 1
        for sentence in sentences:
            if s_count == 1:
                print(sentence)
            else:
                print(" " * (15) + sentence)
            s_count += 1
        # cprint(examples[key])
        print("")


def dictionary(word):
    url = "https://od-api.oxforddictionaries.com:443/api/v1/entries/en/" + word.lower()
    # Please handle with care.
    check_config_dir()

    app_id, app_key = read_config_file()
    headers = {"app_id": app_id, "app_key": app_key}
    # headers = {"app_id": "49a68a4f", "app_key": "98b5944f8e61c97dd755d1d682712dfa"}
    try:
        response = requests.get(url, headers=headers)
    # TODO: test this except block.
    except ConnectionError:
        print("Unable to connect. Please check your internet connection.")
    if response.status_code == 200:
        parsed_response, examples = parse_dictionary_response(response)
        pretty_print_definition(word, parsed_response, examples)
        # print(parsed_response)
        return parsed_response
    elif response.status_code == 404:
        print("No definition found. Please check the spelling!!")
        exit()
    if response.status_code == 403:
        print(
            "You have reached the api limit.This may happen because the api keys",
            "are shared among multiple users. you can either create your free personal api key on https://developer.oxforddictionaries.com",
            " and paste them in ~/.pyvoc/pyvoc.config. ",
        )
    elif response.status_code == 500:
        print("Internal error. Error occured while processing the data")
        exit()
    else:
        print("Something went wrong. Check after some time.")
        exit()


def main():
    parser = argparse.ArgumentParser(
        description="vocabulary building tool (with dictionary api)"
    )
    parser.add_argument("word", help="give meaning of WORD")
    parser.add_argument(
        "-l", "--list", action="store_true", help="list all vocabulary groups"
    )
    parser.add_argument(
        "-a", "--add", action="store_true", help="add WORD to vocabulary group"
    )
    parser.add_argument(
        "-g", help="{optional} group no.(1-50) to add the word to", type=int
    )
    parser.add_argument(
        "-r",
        action="store_true",
        help="revise words in vocabulary group.(WORD is group number)",
    )
    parser.add_argument(
        "-q",
        "--quiz",
        type=int,
        help="starts quiz. WORD is group no. and QUIZ is no. of questions(default=5)",
    )
    args = parser.parse_args()
    if args.r:
        revise_vocab(args.word)
        exit()
    if args.quiz:
        cprint("\n\t\tStarting Quiz", color="red", attrs=["bold", "reverse"])
        quiz(int(args.word), args.quiz)
        exit()
    parsed_response = dictionary(args.word)
    if args.add:
        add_word_to_vocab(args.word.lower(), parsed_response, args.g)
    if args.list:
        list_all_groups()


if __name__ == "__main__":
    main()
