import math


from .number import Rational, ComplexRational
from .runtimeContext import RuntimeContext
from .mathParser import MathParser
from .monomial import Monomial
from .utils import format_rational, format_complex, exact_or_float_sqrt




def evaluate_rhs_expression(tokens: list, context: RuntimeContext, args) -> list:

    if args.verbose:
        print(f"Evaluating RHS Tokens: {tokens}")

    parser = MathParser(tokens, context, allow_unbound=False)
    
    resolved_monomial_list = parser.parse_expression()
    
    if parser.peek() is not None:
        raise ValueError(f"Syntax Error: Unexpected token '{parser.peek()}' at the end of the expression.")

    return resolved_monomial_list

def basic_solve(lhs, context: RuntimeContext, args):
    # Evaluate LHS expression (Variables must be already bound, so allow_unbound=False)
    parser = MathParser(lhs, context, allow_unbound=False)
    resolved_value = parser.parse_expression()
    
    # Verify the parser consumed all tokens (avoid syntax errors like "4 + 5 6")
    if parser.peek() is not None:
        raise ValueError(f"Syntax Error: Unexpected token '{parser.peek()}' at the end of the expression.")
    # 3. Unwrap the monomial list for clean output formatting
    if len(resolved_value) == 1 and resolved_value[0].is_constant():
        clean_value = resolved_value[0].coefficient
    else:
        clean_value = resolved_value
        
    print(clean_value)
    return

def boolean_solve(lhs, rhs, context: RuntimeContext, args):
    # Evaluate Left Hand Side (allow_unbound=False)
    lhs_parser = MathParser(lhs, context, allow_unbound=False)
    lhs_val = lhs_parser.parse_expression()
    if lhs_parser.peek() is not None:
        raise ValueError(f"Syntax Error: Unexpected token '{lhs_parser.peek()}' at end of LHS.")
        
    # Evaluate Right Hand Side (allow_unbound=False)
    rhs_parser = MathParser(rhs, context, allow_unbound=False)
    rhs_val = rhs_parser.parse_expression()
    if rhs_parser.peek() is not None:
        raise ValueError(f"Syntax Error: Unexpected token '{rhs_parser.peek()}' at end of RHS.")

    # 3. Compare and print the output
    # Since all variables are bound, both sides evaluate to a single constant monomial list
    lhs_coeff = lhs_val[0].coefficient if (len(lhs_val) == 1 and lhs_val[0].is_constant()) else lhs_val
    rhs_coeff = rhs_val[0].coefficient if (len(rhs_val) == 1 and rhs_val[0].is_constant()) else rhs_val
    
    if lhs_coeff == rhs_coeff:
        print("true")
    else:
        print("false")
    return

def solve(tokens: list, context: RuntimeContext, args):
    if '=' in tokens: #split into rhs, and lhs
        equal_index = tokens.index('=')
        lhs_tokens = tokens[:equal_index]
        rhs_tokens = tokens[equal_index + 1:]
    else:
        lhs_tokens = tokens
        rhs_tokens = []

    if not lhs_tokens and not rhs_tokens: #safety net
        raise ValueError("Syntax Error: No expression provided to solve.")

    unbound_vars = set()
    for token in tokens: # allow to know if there are unknown
        if isinstance(token, str) and token.isalpha():
            token_clean = token.lower()
            if (token_clean != 'i' and
                not context.is_reserved_name(token_clean) and
                token_clean not in context._functions and
                context.lookup_variable(token_clean) is None):
                unbound_vars.add(token_clean)

    #--resulution :
    if not rhs_tokens:
        basic_solve(lhs_tokens, context, args)
        return

    if rhs_tokens and len(unbound_vars) == 0:
        boolean_solve(lhs_tokens, rhs_tokens, context, args)
        return

    if rhs_tokens and len(unbound_vars) > 0:
        from .poly_solver import solve_polynomial
        solve_polynomial(rhs_tokens, lhs_tokens, unbound_vars, var_name=None, context=context, args=args)
        return

    return

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
        
        # Unwrap list of 1 constant monomial to its clean underlying scalar coefficient
        if len(resolved_value) == 1 and resolved_value[0].is_constant():
            clean_value = resolved_value[0].coefficient
        else:
            clean_value = resolved_value
            
        context.store_variable(var_name, clean_value)
        
        # Print the clean, formatted scalar value to console
        print(clean_value)
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