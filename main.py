import argparse
import sys
import io

from src.parser import parse_free_form_equation, strip_and_check, get_options
from src.maths import solve, assign



from src.number import Rational, ComplexRational
from src.runtimeContext import RuntimeContext
from src.utils import tc

override_options = ["context", "delete", "derivate", "curv", "display", "transpose", "inverse", "determinant", "norm"]
passive_options = ["rad", "frac", "dec"]

def parse_arguments():
    parser = argparse.ArgumentParser(description="Computor V1: The Parser")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")

    return parser.parse_args()


def catch_override_options(tags_list: list[str], prompt: str) -> bool:
    matched_tags = [t for t in tags_list if t in override_options]
    
    if len(matched_tags) > 1:
        raise ValueError(
            f"Syntax Error: Multiple override options detected: {matched_tags}. "
            f"Only one of {override_options} can be used at a time."
        )
    
    if not matched_tags:
        return False
    
    sanitized_prompt = prompt.strip()
    
    match matched_tags[0]:
        case "context":
            context.print_context()
            return True
            
        case "delete":
            if not sanitized_prompt:
                print(f"{tc.BOLD}{tc.RED}Error: Delete command requires a valid identifier name.{tc.RESET}")
                return True
                
            if context.remove(sanitized_prompt):
                print(f"{tc.GREEN}Deleted '{sanitized_prompt}' from memory.{tc.RESET}")
            else:
                print(f"{tc.BOLD}{tc.RED}Error: '{sanitized_prompt}' not found in memory (or is protected).{tc.RESET}")
            return True
            
        case "derivate":
            try:
                base_expr, param, derived_expr = context.derivate(sanitized_prompt)
                print(f"Derivate of {tc.BOLD}{base_expr}{tc.RESET} with respect to {tc.BOLD}{param}{tc.RESET} is: {tc.BOLD}{tc.GREEN}{derived_expr}{tc.RESET}")
            except ValueError as e:
                print(f"{tc.BOLD}{tc.RED}Syntax Error parsing derivation arguments: {e}{tc.RESET}")
            return True
            
        case "curv":
            context.analyze(sanitized_prompt)
            return True
            
        case "display":
            context.display(sanitized_prompt)
            return True

        case "transpose":
            context.transpose(sanitized_prompt)
            return True

        case "inverse":
            context.inverse(sanitized_prompt)
            return True
        
        case "determinant":
            context.determinant(sanitized_prompt)
            return True

        case "norm":
            context.norm(sanitized_prompt)
            return True

        case _:
            return False


def catch_passive_options(tags_list):
    tag = [t for t in tags_list if t in passive_options]

    if not tag:
        return None

    for t in tag:
        if t == "rad":
            context.set_to_rad()
        elif t == "frac":
            context.set_to_frac()
        elif t == "dec":
            context.set_to_dec()
    
    return tag[0]

if __name__ == "__main__":
    args = parse_arguments()

    context = RuntimeContext()

    if args.verbose:
        print(f"{tc.UNDERLINE}{tc.GREEN}\n--- VERBOSE MODE --- \n\n{tc.RESET}")

    while True:
        try:
            prompt = input(f"{tc.BOLD}{tc.CYAN}> {tc.RESET}")

            if prompt.lower() in {"exit", "quit"}:
                print(f"{tc.BOLD}{tc.YELLOW}Exiting...{tc.RESET}")
                break

            prompt, tags = get_options(prompt)

            for t in tags:
                if t not in override_options and t not in passive_options:
                    raise ValueError(f"Unknown option '{t}' detected. Valid options are: {override_options + passive_options}.")

            catched = catch_override_options(tags, prompt)
            if catched:
                continue
            
            catch_passive_options(tags)
            
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
            print(f"\n{tc.BOLD}{tc.YELLOW}Exiting...{tc.RESET}")
            break
        except Exception as e:
            print(f"{tc.BOLD}{tc.RED}Error: {e}{tc.RESET}")