import argparse

from testgen.reqif_parser import ReqifParser


def main():
    parser = argparse.ArgumentParser(description="Parse a .reqif file and extract requirements, tests, and test cases.")
    parser.add_argument('file_path', type=str, help="Path to the .reqif file")
    args = parser.parse_args()

    print("Parsing .reqif file:", args.file_path)
    reqif_parser = ReqifParser(args.file_path)
    data = reqif_parser.parse_reqif()

    print("Requirements:", data)

