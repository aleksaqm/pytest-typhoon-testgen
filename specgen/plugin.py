import argparse


def main():
    parser = argparse.ArgumentParser(description="A command-line tool that greets the user.")
    parser.add_argument('name', type=str, help="The name of the person to greet")
    args = parser.parse_args()

    print("Hi " + args.name)