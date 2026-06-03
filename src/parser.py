import re

from collections import defaultdict


import re


def resolve_signs(match):
    sequence = match.group(0)
    return '-' if sequence.count('-') % 2 != 0 else '+'


def get_options(text: str) -> tuple[str, list[str]]:
    cleaned_input = text.rstrip()

    end_block_match = re.search(r"(?:\s*#[^\s]+)+$", cleaned_input)

    if not end_block_match:
        return cleaned_input, []

    start_of_tags = end_block_match.start()
    clean_text = cleaned_input[:start_of_tags].rstrip()

    tags_block = end_block_match.group(0)
    tags_list = re.findall(r"#([a-zA-Z0-9_-]+)", tags_block)

    return clean_text, tags_list


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
    
    if is_assignment and cleaned.count('=') > 1:
        raise ValueError("Syntax Error: Assignment instructions must contain exactly one '=' operator.")
    
    if is_assignment and cleaned.count('=') == 0:
        is_assignment = False  # Reclassify as non-assignment if no '=' is present

    if args.verbose:
        GREEN = "\033[92m"
        RESET = "\033[0m"
        print(GREEN + "Stripping complete : " + RESET + cleaned + f" | Is Assignment: {is_assignment}")

    return cleaned, is_assignment




def parse_free_form_equation(equation_str: str, args, context=None, is_assignment: bool = False) -> dict:
    if args.verbose:
        print("parser entered, starting regex tokenization...")

    token_pattern = r'\d+\.\d+|\d+|[a-zA-Z]+|\*\*|=\?|[=+\-*^/%()[\];,]'
    
    raw_tokens = re.findall(token_pattern, equation_str)

    # Helper to check if identifier is a known function call
    def is_function(name):
        builtins = {"sqrt", "cbrt", "log", "ln", "exp", "sin", "cos", "tan", "abs"}
        if name.lower() in builtins:
            return True
        if context and name.lower() in context._functions:
            return True
        return False

    # Insert implicit multiplication '*' tokens
    processed_tokens = []
    eq_index = raw_tokens.index('=') if (is_assignment and '=' in raw_tokens) else -1

    for i in range(len(raw_tokens)):
        if i > 0:
            t1 = raw_tokens[i-1]
            t2 = raw_tokens[i]
            
            insert_star = False
            
            # If it's an assignment, do not insert '*' on the LHS (i <= eq_index)
            if not (is_assignment and i <= eq_index):
                # 1. Digit followed by variable/alpha or parenthesized expression
                # e.g., '2' followed by 'x', 'i', 'pi', or '('
                if t1.replace('.', '', 1).isdigit() and (t2.isalpha() or t2 == '('):
                    insert_star = True
                
                # 2. Variable/alpha followed by parenthesized expression (unless it's a function call)
                # e.g., 'x' followed by '('
                elif t1.isalpha() and t2 == '(':
                    if not is_function(t1):
                        insert_star = True
                
                # 3. Close parenthesis followed by digit, alpha, or open parenthesis
                # e.g., ')' followed by '2', 'x', or '('
                elif t1 == ')' and (t2.replace('.', '', 1).isdigit() or t2.isalpha() or t2 == '('):
                    insert_star = True
                
            if insert_star:
                processed_tokens.append('*')
                
        processed_tokens.append(raw_tokens[i])

    return dict(enumerate(processed_tokens))
