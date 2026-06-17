import sys
import io
import os
import re

from src.parser import parse_free_form_equation, strip_and_check, get_options
from src.maths import solve, assign
from src.number import Rational, ComplexRational
from src.runtimeContext import RuntimeContext
from src.utils import tc

#options acts like flags 
override_options = ["context", "delete", "derivate", "curv", "display", "transpose", "inverse", "determinant", "norm", "history"]
passive_options = ["rad", "frac", "dec"]

history_log = []


def expand_history(prompt: str, history_log: list) -> str:
    """Expands $<number> patterns to previous history inputs (reversed order: $1 is most recent)."""
    match_exact = re.fullmatch(r'\s*\$(\d+)\s*', prompt)
    if match_exact:
        idx = int(match_exact.group(1))
        if 1 <= idx <= len(history_log):
            return history_log[-idx][0]
        else:
            raise ValueError(f"History index ${idx} out of range.")

    def replace_match(match):
        idx = int(match.group(1))
        if 1 <= idx <= len(history_log):
            return history_log[-idx][0].rstrip('?').strip()
        else:
            raise ValueError(f"History index ${idx} out of range.")

    try:
        expanded = re.sub(r'\$(\d+)', replace_match, prompt)
        if expanded != prompt:
            print(f"{tc.BOLD}{tc.WHITE}Expanded: {expanded}{tc.RESET}")
        return expanded
    except ValueError as e:
        print(f"{tc.BOLD}{tc.RED}Error: {e}{tc.RESET}")
        return ""


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
        case "history":
            if not history_log:
                print(f"{tc.BOLD}{tc.YELLOW}No command history available yet.{tc.RESET}")
            else:
                for idx, (cmd, res, is_assign) in enumerate(reversed(history_log), 1):
                    display_res = res.replace('\n', ' ')
                    print(f"{tc.CYAN}${idx}{tc.RESET} {cmd} {tc.BOLD}|{tc.RESET} {tc.GRAY}{display_res}{tc.RESET}")
            return True

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
    context = RuntimeContext()

    while True:
        try:
            prompt = input(f"{tc.BOLD}{tc.CYAN}> {tc.RESET}")

            if prompt.lower() in {"exit", "quit"}:
                print(f"{tc.BOLD}{tc.YELLOW}Exiting...{tc.RESET}")
                break

            prompt = expand_history(prompt, history_log)
            if not prompt:
                continue

            prompt, tags = get_options(prompt)

            for t in tags:
                if t not in override_options and t not in passive_options:
                    raise ValueError(f"Unknown option '{t}' detected. Valid options are: {override_options + passive_options}.")

            catched = catch_override_options(tags, prompt)
            if catched:
                continue
            
            context.reset_context_options()
            catch_passive_options(tags)
            
            if not prompt.strip():
                continue
            
            success = False
            is_assignment = False
            old_stdout = sys.stdout
            captured_stdout = io.StringIO()
            sys.stdout = captured_stdout

            try:
                prompt_clean, is_assignment = strip_and_check(prompt)
                tokens = parse_free_form_equation(prompt_clean, context, is_assignment=is_assignment)
                tokens_list = [value for value in tokens.values() if value is not None]

                if not is_assignment:
                    solve(tokens_list, context)
                else:
                    assign(tokens_list, context)
                success = True
            finally:
                sys.stdout = old_stdout

            result_str = captured_stdout.getvalue()
            print(result_str, end="")

            if success:
                history_log[:] = [entry for entry in history_log if entry[0].strip() != prompt_clean]
                history_log.append((prompt_clean, result_str.strip(), is_assignment))

        except (EOFError, KeyboardInterrupt):
            print(f"\n{tc.BOLD}{tc.YELLOW}Exiting...{tc.RESET}")
            break
        except Exception as e:
            print(f"{tc.BOLD}{tc.RED}Error: {e}{tc.RESET}")