import argparse
import os
from pathlib import Path

from testgen.generator import TestGenerator
from testgen.reqif_parser import ReqifParser


def main():
    parser = argparse.ArgumentParser(description="Parse a .reqif file and generate pytest tests.")
    parser.add_argument('file_path', type=str, help="Path to the .reqif file")
    parser.add_argument('output_path', type=str, nargs='?', default=os.getcwd(),
                        help="Directory where tests will be generated (default: current working directory)")

    args = parser.parse_args()

    print("Parsing .reqif file:", args.file_path)
    print("Generating tests into:", args.output_path)

    reqif_parser = ReqifParser(args.file_path)
    data = reqif_parser.parse_reqif()

    print("Requirements:", data)

    start_path = Path(args.output_path)
    test_generator = TestGenerator(data, start_path)
    test_generator.generate()



