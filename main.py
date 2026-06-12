import argparse
import sys
import io

from src.parser import parse_free_form_equation, strip_and_check, get_options
from src.maths import solve, assign



from src.number import Rational, ComplexRational
from src.runtimeContext import RuntimeContext

override_options = ["context", "delete", "derivate", "curv", "display"]
passive_options = ["rad", "frac", "dec"]

def parse_arguments():
    parser = argparse.ArgumentParser(description="Computor V1: The Parser")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")

    return parser.parse_args()


def catch_override_options(tags_list, prompt):
    tag = [t for t in tags_list if t in override_options]
    if len(tag) > 1:
        raise ValueError(f"Syntax Error: Multiple override options detected: {tag}. Only one of {override_options} can be used at a time.")
    
    if not tag:
        return False
    
    if tag[0] == "context":
        context.print_context()
        return True
    if tag[0] == "delete":
        name = prompt.strip()
        if context.remove(name):
            print(f"Deleted '{name}' from memory.")
        else:
            print(f"Error: '{name}' not found in memory (or is protected).")
        return True
    
    if tag[0] == "derivate":
        base_expr, param, derived_expr = context.derivate(prompt.strip())
        print(f"Derivate of {base_expr} with respect to {param} is: {derived_expr}")
        return True
    
    if tag[0] == "curv":
        print("Curv option selected: This will compute the curvature of the current polynomial.")
        return True
    
    if tag[0] == "display":
        context.display(prompt.strip())
        return True
    return False

if __name__ == "__main__":
    args = parse_arguments()

    context = RuntimeContext()

    if args.verbose:
        print(UNDERLINE + GREEN+ "\n--- VERBOSE MODE --- \n\n" + RESET)

    while True:
        try:
            prompt = input("> ")

            if prompt.lower() in {"exit", "quit"}:
                print("Exiting...")
                break

            prompt, tags = get_options(prompt)

            catched =catch_override_options(tags, prompt)
            if catched:
                continue
            
            prompt, is_assignment = strip_and_check(prompt, args)

            tokens = parse_free_form_equation(prompt, args, context, is_assignment=is_assignment)


            tokens_list = [
                value for value in tokens.values() 
                if value is not None
            ]

            if not is_assignment:
                solve(tokens_list, context, args)
            else:
                assign(tokens_list, context, args)

        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")