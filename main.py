import argparse
import sys
import io

from src.parser import parse_free_form_equation, strip_and_check
from src.maths import solve, assign



from src.number import Rational, ComplexRational
from src.runtimeContext import RuntimeContext

def parse_arguments():
    parser = argparse.ArgumentParser(description="Computor V1: The Parser")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    context = RuntimeContext()

    if args.verbose:
        print(UNDERLINE + GREEN+ "\n--- VERBOSE MODE --- \n\n" + RESET)

    while True:
        try:
            prompt = input("> ")

            if prompt == "context":
                print("\n--- CURRENT CONTEXT ---")
                print("Variables:")
                for var_name, value in context._variables.items():
                    print(f"  {var_name} = {value}")
                print("Functions:")
                for func_name, func_data in context._functions.items():
                    print(f"  {func_name}({func_data['parameter']}) = {func_data['tokens']}")
                continue


            if prompt.lower() in {"exit", "quit"}:
                print("Exiting...")
                break
            
            prompt, is_assignment = strip_and_check(prompt, args)

            tokens = parse_free_form_equation(prompt, args, context)


            tokens_list = [
                value for value in tokens.values() 
                if value is not None
            ]

            if not is_assignment:
                print("\n--- SOLVING ---")
                solve(tokens_list, context, args)
            else:
                assign(tokens_list, context, args)

            

            print(tokens)
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")