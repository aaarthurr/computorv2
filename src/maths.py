import math


from .number import Rational, ComplexRational
from .runtimeContext import RuntimeContext
from .mathParser import MathParser
from .monomial import Monomial
from .utils import format_rational, format_complex, exact_or_float_sqrt, pretty_print, tc




def evaluate_rhs_expression(tokens: list, context: RuntimeContext) -> list:
    parser = MathParser(tokens, context, allow_unbound=False)
    
    resolved_monomial_list = parser.parse_expression()
    
    if parser.peek() is not None:
        raise ValueError(f"Syntax Error: Unexpected token '{parser.peek()}' at the end of the expression.")

    return resolved_monomial_list

def basic_solve(lhs, context: RuntimeContext):
    # Check if the query is a function signature: e.g., f(z) = ?
    is_func_query = False
    func_name = None
    param_name = None
    if len(lhs) == 4 and lhs[1] == '(' and lhs[3] == ')':
        func_name = lhs[0].lower()
        param_name = lhs[2].lower()
        func_data = context.lookup_function(func_name)
        if func_data and func_data["type"] == "USER":
            if context.lookup_variable(param_name) is None:
                is_func_query = True

    try:
        # Evaluate LHS expression (Only allow unbound if it's a function query with unbound parameter)
        parser = MathParser(lhs, context, allow_unbound=is_func_query)
        resolved_value = parser.parse_expression()
        
        # Verify the parser consumed all tokens (avoid syntax errors like "4 + 5 6")
        if parser.peek() is not None:
            raise ValueError(f"Syntax Error: Unexpected token '{parser.peek()}' at the end of the expression.")
        # 3. Unwrap the monomial list for clean output formatting
        if len(resolved_value) == 1 and resolved_value[0].is_constant():
            clean_value = resolved_value[0].coefficient
        else:
            from .utils import format_monomial_list
            clean_value = format_monomial_list(resolved_value)
            
        print(f"{tc.BOLD}{clean_value}{tc.RESET}")
    except Exception as e:
        if is_func_query and func_name and param_name:
            func_data = context.lookup_function(func_name)
            if func_data and func_data["type"] == "USER":
                orig_param = func_data["parameter"]
                orig_tokens = func_data["tokens"]
                
                # Substitute orig_param with param_name in the tokens
                substituted_tokens = []
                for token in orig_tokens:
                    if isinstance(token, str) and token.lower() == orig_param.lower():
                        substituted_tokens.append(param_name)
                    else:
                        substituted_tokens.append(token)
                        
                from .utils import pretty_print
                pretty_print(substituted_tokens)
                return
        raise e
    return

def boolean_solve(lhs, rhs, context: RuntimeContext):
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

    lhs_coeff = lhs_val[0].coefficient if (len(lhs_val) == 1 and lhs_val[0].is_constant()) else lhs_val
    rhs_coeff = rhs_val[0].coefficient if (len(rhs_val) == 1 and rhs_val[0].is_constant()) else rhs_val
    
    if lhs_coeff == rhs_coeff:
        print(f"{tc.BOLD}{tc.WHITE}true{tc.RESET}")
    else:
        print(f"{tc.BOLD}{tc.WHITE}false{tc.RESET}")
    return

def solve(tokens: list, context: RuntimeContext):
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
        basic_solve(lhs_tokens, context)
        return

    if rhs_tokens and len(unbound_vars) == 0:
        boolean_solve(lhs_tokens, rhs_tokens, context)
        return

    if rhs_tokens and len(unbound_vars) > 0:
        from .poly_solver import solve_polynomial
        solve_polynomial(rhs_tokens, lhs_tokens, unbound_vars, var_name=None, context=context)
        return

    return

def assign(tokens: list, context: RuntimeContext) -> None:
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

        resolved_value = evaluate_rhs_expression(rhs_tokens, context)
        
        # Unwrap list of 1 constant monomial to its clean underlying scalar coefficient
        if len(resolved_value) == 1 and resolved_value[0].is_constant():
            clean_value = resolved_value[0].coefficient
        else:
            clean_value = resolved_value
            
        context.store_variable(var_name, clean_value)
        
        # Print the clean, formatted scalar value to console
        print(f"{tc.BOLD}{clean_value}{tc.RESET}")
        return

    # 3. Track B: Function Assignment (LHS must match the 'name(param)' signature pattern)
    if (len(lhs_tokens) == 4 and 
        lhs_tokens[1] == '(' and 
        lhs_tokens[3] == ')'):
        
        func_name = lhs_tokens[0]
        param_name = lhs_tokens[2]

        if not func_name.isalpha() or not param_name.isalpha():
            raise ValueError("Syntax Error: Function names and parameters must consist strictly of letters.")

        # LAZY EVALUATION: Store the raw mathematical blueprint tokens for calculation later
        context.store_function(func_name, param_name, rhs_tokens)
        
        # Print confirmation layout mapping matching subject expectations
        from .mathParser import MathParser
        from .utils import format_monomial_list, pretty_print
        parser = MathParser(rhs_tokens, context, allow_unbound=True, shadowed_param=param_name)
        try:
            monomials = parser.parse_expression()
            if parser.peek() is not None:
                raise ValueError()
            print(f"{tc.CYAN}{format_monomial_list(monomials)}{tc.RESET}")
        except Exception:
            pretty_print(rhs_tokens)
        return

    # 4. Catch-all for structural syntax chaos (e.g., '2 + 2 = x' or 'f(x) + 1 = y')
    raise ValueError("Syntax Error: Invalid assignment layout. Left side must be a single variable name or clean function signature.")