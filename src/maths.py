import math


from .number import Rational, ComplexRational
from .runtimeContext import RuntimeContext
from .mathParser import MathParser
from .monomial import Monomial





def evaluate_rhs_expression(tokens: list, context: RuntimeContext, args) -> list:

    if args.verbose:
        print(f"Evaluating RHS Tokens: {tokens}")

    parser = MathParser(tokens, context, allow_unbound=False)
    
    resolved_monomial_list = parser.parse_expression()
    
    if parser.peek() is not None:
        raise ValueError(f"Syntax Error: Unexpected token '{parser.peek()}' at the end of the expression.")

    return resolved_monomial_list



def solve(tokens: list, context: RuntimeContext, args):
    print("end of program")


def assign(tokens: list, context: RuntimeContext, args) -> None:
    """
    Processes and validates structural assignments for variables and functions.
    Ensures absolute naming security and isolates memory state allocations.
    """
    if args.verbose:
        print(f"Assignment Engine active. Processing token stream: {tokens}")

    # 1. Safely split the stream into LHS and RHS around the assignment anchor
    try:
        equal_index = tokens.index('=')
    except ValueError:
        raise ValueError("Syntax Error: Assignment instructions must contain exactly one '=' operator.")

    lhs_tokens = tokens[:equal_index]
    rhs_tokens = tokens[equal_index + 1:]

    if not rhs_tokens:
        raise ValueError("Syntax Error: Missing expression payload on the right-hand side of assignment.")

    # 2. Track A: Variable Assignment (LHS must be a single alphabetic identifier)
    if len(lhs_tokens) == 1:
        var_name = lhs_tokens[0]
        
        if not var_name.isalpha():
            raise ValueError(f"Syntax Error: Invalid variable identifier '{var_name}'. Names must be alphabetic letters.")

        if args.verbose:
            print(f"Routing target identified as VARIABLE: '{var_name}'")

        resolved_value = evaluate_rhs_expression(rhs_tokens, context, args)
        
        context.store_variable(var_name, resolved_value)
        
        # Print the success output format to console
        print(resolved_value)
        return

    # 3. Track B: Function Assignment (LHS must match the 'name(param)' signature pattern)
    if (len(lhs_tokens) == 4 and 
        lhs_tokens[1] == '(' and 
        lhs_tokens[3] == ')'):
        
        func_name = lhs_tokens[0]
        param_name = lhs_tokens[2]

        if not func_name.isalpha() or not param_name.isalpha():
            raise ValueError("Syntax Error: Function names and parameters must consist strictly of letters.")

        if args.verbose:
            print(f"Routing target identified as FUNCTION: '{func_name}' with parameter '{param_name}'")

        # LAZY EVALUATION: Store the raw mathematical blueprint tokens for calculation later
        context.store_function(func_name, param_name, rhs_tokens)
        
        # Print confirmation layout mapping matching subject expectations
        print(f"Stored template: {func_name}({param_name})")
        return

    # 4. Catch-all for structural syntax chaos (e.g., '2 + 2 = x' or 'f(x) + 1 = y')
    raise ValueError("Syntax Error: Invalid assignment layout. Left side must be a single variable name or clean function signature.")