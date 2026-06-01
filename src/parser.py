import re

from collections import defaultdict


import re


def resolve_signs(match):
    sequence = match.group(0)
    return '-' if sequence.count('-') % 2 != 0 else '+'


def strip_and_check(equation_str: str, args) -> tuple[str, bool]:
    cleaned = equation_str.replace(" ", "")

    if args.verbose:
        print(f"Initial raw input received: '{equation_str}'")

    if '?' in cleaned:
        # Match a valid pattern: anything followed strictly by one or more '?' at the very end
        if not re.match(r'^[^?]+\?+$', cleaned):
            raise ValueError("Syntax Error: The query operator '?' must only appear at the very end of the line.")
        
        # This is a query/resolution execution command, so it cannot be an assignment
        is_assignment = False
        # Strip all trailing '?' characters out to leave a clean math string for tokenization
        cleaned = cleaned.rstrip('?')
    else:
        # No '?' present anywhere means this track targets a memory context write
        is_assignment = True

    if re.search(r'[*/%^][*/%^]', cleaned):
        raise ValueError("Syntax Error: Invalid operator sequence detected (e.g., multiple consecutive multiplication/division operators).")

    cleaned = re.sub(r'(?<!\*)\*{3,}(?!\*)', '**', cleaned) # Normalizes ***+ to **
    cleaned = re.sub(r'([=/%\^])\1+', r'\1', cleaned)



    cleaned = re.sub(r'[+-]+', resolve_signs, cleaned)

    cleaned = re.sub(r'([\*/%=\^\(\[;,])\+', r'\1', cleaned)

    # 5. Clean up redundant decimal points
    cleaned = re.sub(r'\.{2,}', '.', cleaned)

    if cleaned.count('=') > 1:
        raise ValueError("Syntax Error: The expression must contain at most one '=' assignment or boundary sign.")
    
    if is_assignment and cleaned.count('=') != 1:
        raise ValueError("Syntax Error: Assignment instructions must contain exactly one '=' operator.")

    if args.verbose:
        GREEN = "\033[92m"
        RESET = "\033[0m"
        print(GREEN + "Stripping complete : " + RESET + cleaned + f" | Is Assignment: {is_assignment}")

    return cleaned, is_assignment


def parse_free_form_equation(equation_str: str, args) -> dict:
    if args.verbose:
        print("parser entered, starting regex tokenization...")

    token_pattern = r'\d+\.\d+|\d+|[a-zA-Z]+|\*\*|=\?|[=+\-*^/%()[\];,]'
    
    raw_tokens = re.findall(token_pattern, equation_str)


    return dict(enumerate(raw_tokens))
