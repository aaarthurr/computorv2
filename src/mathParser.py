import copy
import math

from .number import Rational, ComplexRational
from .parser import parse_free_form_equation
from .runtimeContext import RuntimeContext
from .monomial import Monomial

class MathParser:
    def __init__(self, tokens: list, context: RuntimeContext, allow_unbound: bool):
        self.tokens = tokens
        self.context = context
        self.cursor = 0
        self.allow_unbound = allow_unbound # False for Assignment, True for Equation Queries

    def peek(self) -> str | None:
        if self.cursor < len(self.tokens):
            return self.tokens[self.cursor]
        return None

    def consume(self) -> str:
        token = self.tokens[self.cursor]
        self.cursor += 1
        return token

    # --- PEMDAS LAYER 1: Addition & Subtraction ---
    def parse_expression(self) -> list:
        terms = self.parse_term()
        while self.peek() in ('+', '-'):
            op = self.consume()
            right_terms = self.parse_term()
            # If '-', loop through right_terms and negate their Monomial coefficients
            if op == '-':
                for m in right_terms:
                    m.coefficient = -m.coefficient
            terms.extend(right_terms)
        return self.compress_monomials(terms)

    # --- PEMDAS LAYER 2: Multiplication, Division & Modulo ---
    def parse_term(self) -> list:
        factors = self.parse_power()
        while self.peek() in ('*', '/', '%'):
            op = self.consume()
            right_factors = self.parse_power()
            factors = self.multiply_lists(factors, right_factors, op)
        return factors

    # --- PEMDAS LAYER 3: Exponentiation ---
    def parse_power(self) -> list:
        factors = self.parse_factor()
        while self.peek() in ('**', '^'):
            op = self.consume()
            right_factors = self.parse_factor()
            factors = self.power_lists(factors, right_factors)
        return factors

    # --- PEMDAS LAYER 4: Literals, Parens, Variables, Functions, Unary ---
    def parse_factor(self) -> list:
        # Check for unary operators
        if self.peek() == '-':
            self.consume() # consume '-'
            factor = self.parse_factor()
            # Negate all monomials in factor
            for m in factor:
                m.coefficient = -m.coefficient
            return factor
        elif self.peek() == '+':
            self.consume() # consume '+'
            return self.parse_factor()

        token = self.consume()

        # 1. Handle Parentheses
        if token == '(':
            inner_expr = self.parse_expression()
            if self.consume() != ')':
                raise ValueError("Syntax Error: Missing closing parenthesis.")
            return inner_expr

        # 2. Handle Numbers
        if token.replace('.', '', 1).isdigit():
            parsed_fraction = Rational.from_string(token)
            return [Monomial(coefficient=parsed_fraction)]

        # 3. Handle Identifiers (Variables & Functions)
        if token.isalpha():
            # Check if it's a Function Call: e.g., "sqrt(" or "f("
            if self.peek() == '(':
                return self.evaluate_function_call(token)
            
            # Otherwise, it's a Variable. Look it up!
            stored_val = self.context.lookup_variable(token)
            
            # EAGER EVALUATION: If found, inject its value instantly
            if stored_val is not None:
                # Wrap scalar values (Rational, ComplexRational) into Monomial list
                if isinstance(stored_val, (Rational, ComplexRational)):
                    return [Monomial(coefficient=copy.deepcopy(stored_val))]
                elif isinstance(stored_val, list):
                    return copy.deepcopy(stored_val)
                else:
                    return [Monomial(coefficient=copy.deepcopy(stored_val))]
            
            # If not found, check our security lock!
            if self.allow_unbound:
                # We are solving an equation (e.g., 'x = 0?'), so keep 'x' as a symbolic unknown
                return [Monomial(coefficient=Rational(1), variable=token, power=1)]
            else:
                # We are in Assignment Mode (e.g., 'a = x'). Crash securely.
                raise ValueError(f"Runtime Error: Variable '{token}' is undefined.")

        raise ValueError(f"Syntax Error: Unexpected factor '{token}'")

    # --- HELPER ROUTINES ---
    def evaluate_function_call(self, func_name: str) -> list:
        """Executes built-in callbacks or substitutes user templates."""
        func_data = self.context.lookup_function(func_name)
        if func_data is None:
            raise ValueError(f"Runtime Error: Function '{func_name}' is not defined.")

        self.consume() # Eat '('
        argument_monomials = self.parse_expression() # Solve the inside math first!
        self.consume() # Eat ')'

        if func_data["type"] == "BUILTIN":
            if len(argument_monomials) != 1 or not argument_monomials[0].is_constant():
                raise ValueError(f"Math Error: Cannot evaluate built-in function '{func_name}' with unresolved variables.")
            
            raw_val = argument_monomials[0].coefficient
            
            if func_name.lower() == 'abs':
                if isinstance(raw_val, ComplexRational):
                    r2 = raw_val.real * raw_val.real
                    i2 = raw_val.imag * raw_val.imag
                    sum_sq = r2 + i2
                    float_val = float(sum_sq.num) / float(sum_sq.den)
                    res_sqrt = math.sqrt(float_val)
                    res_rat = Rational.from_string(f"{res_sqrt:.12f}".rstrip('0').rstrip('.'))
                    return [Monomial(coefficient=res_rat)]
                else:
                    return [Monomial(coefficient=abs(raw_val))]
                    
            if func_name.lower() == 'sqrt':
                is_negative = False
                if isinstance(raw_val, Rational) and raw_val.num < 0:
                    is_negative = True
                    float_val = float(-raw_val.num) / float(raw_val.den)
                elif isinstance(raw_val, ComplexRational) and raw_val.imag.num == 0 and raw_val.real.num < 0:
                    is_negative = True
                    float_val = float(-raw_val.real.num) / float(raw_val.real.den)
                elif not isinstance(raw_val, (Rational, ComplexRational)) and raw_val < 0:
                    is_negative = True
                    float_val = float(-raw_val)
                
                if is_negative:
                    res_sqrt = math.sqrt(float_val)
                    res_rat = Rational.from_string(f"{res_sqrt:.12f}".rstrip('0').rstrip('.'))
                    return [Monomial(coefficient=ComplexRational(Rational(0), res_rat))]

            # General built-ins
            float_val = float(raw_val.real.num) / float(raw_val.real.den) if isinstance(raw_val, ComplexRational) else (float(raw_val.num) / float(raw_val.den) if isinstance(raw_val, Rational) else float(raw_val))
            result = func_data["callback"](float_val)
            res_rat = Rational.from_string(f"{result:.12f}".rstrip('0').rstrip('.'))
            return [Monomial(coefficient=res_rat)]
        else:
            # User defined function substitution logic goes here...
            pass

    def compress_monomials(self, term_list: list) -> list:
        """Groups terms with the same power to keep the list flat and clean."""
        grouped = {}
        for m in term_list:
            var = m.variable
            pwr = m.power
            if var is None or pwr == 0:
                key = (None, 0)
            else:
                key = (var, pwr)
            
            if key not in grouped:
                grouped[key] = m.coefficient
            else:
                grouped[key] = grouped[key] + m.coefficient
        
        compressed = []
        for (var, pwr), coeff in grouped.items():
            is_zero = False
            if isinstance(coeff, (int, float)):
                is_zero = coeff == 0
            elif hasattr(coeff, 'num'): # Rational
                is_zero = coeff.num == 0
            elif hasattr(coeff, 'real') and hasattr(coeff, 'imag'): # ComplexRational
                is_zero = coeff.real.num == 0 and coeff.imag.num == 0
                
            if not is_zero:
                compressed.append(Monomial(coefficient=coeff, variable=var, power=pwr))
                
        # If everything was zero, return a single constant zero monomial
        if not compressed:
            if term_list:
                first_coeff = term_list[0].coefficient
                if hasattr(first_coeff, 'imag'):
                    zero_coeff = ComplexRational(Rational(0), Rational(0))
                else:
                    zero_coeff = Rational(0)
            else:
                zero_coeff = Rational(0)
            compressed.append(Monomial(coefficient=zero_coeff))
            
        compressed.sort(key=lambda m: m.power, reverse=True)
        return compressed

    def multiply_lists(self, left: list, right: list, op: str) -> list:
        """Distributes multiplication across two Monomial lists."""
        if op == '*':
            result = []
            for m1 in left:
                for m2 in right:
                    new_coeff = m1.coefficient * m2.coefficient
                    if m1.is_constant():
                        new_var = m2.variable
                        new_pwr = m2.power
                    elif m2.is_constant():
                        new_var = m1.variable
                        new_pwr = m1.power
                    else:
                        if m1.variable == m2.variable:
                            new_var = m1.variable
                            new_pwr = m1.power + m2.power
                        else:
                            raise ValueError(f"Math Error: Multi-variable multiplication ({m1.variable} * {m2.variable}) is not supported.")
                    result.append(Monomial(coefficient=new_coeff, variable=new_var, power=new_pwr))
            return self.compress_monomials(result)
            
        elif op == '/':
            if len(right) != 1 or not right[0].is_constant():
                raise ValueError("Math Error: Division by non-constant expressions is not supported.")
            divisor = right[0].coefficient
            
            is_zero = False
            if isinstance(divisor, (int, float)):
                is_zero = divisor == 0
            elif hasattr(divisor, 'num'):
                is_zero = divisor.num == 0
            elif hasattr(divisor, 'real') and hasattr(divisor, 'imag'):
                is_zero = divisor.real.num == 0 and divisor.imag.num == 0
                
            if is_zero:
                raise ZeroDivisionError("Math Error: Division by zero.")
                
            result = []
            for m in left:
                new_coeff = m.coefficient / divisor
                result.append(Monomial(coefficient=new_coeff, variable=m.variable, power=m.power))
            return self.compress_monomials(result)
            
        elif op == '%':
            if len(right) != 1 or not right[0].is_constant():
                raise ValueError("Math Error: Modulo is only supported with constant scalars.")
            divisor = right[0].coefficient
            if not isinstance(divisor, Rational):
                raise ValueError("Math Error: Modulo is only supported with real rational numbers.")
                
            result = []
            for m in left:
                if not isinstance(m.coefficient, Rational):
                    raise ValueError("Math Error: Modulo is only supported on real rational numbers.")
                new_coeff = m.coefficient % divisor
                result.append(Monomial(coefficient=new_coeff, variable=m.variable, power=m.power))
            return self.compress_monomials(result)
            
        raise ValueError(f"Math Error: Unsupported operator '{op}'")

    def power_lists(self, left: list, right: list) -> list:
        """Raises Monomial lists to integer powers."""
        if len(right) != 1 or not right[0].is_constant():
            raise ValueError("Math Error: Exponent must be a constant scalar.")
        exponent_val = right[0].coefficient
        
        if isinstance(exponent_val, Rational):
            if exponent_val.den != 1:
                raise ValueError("Math Error: Exponent must be an integer.")
            power = exponent_val.num
        elif isinstance(exponent_val, ComplexRational):
            if exponent_val.imag.num != 0 or exponent_val.real.den != 1:
                raise ValueError("Math Error: Exponent must be a real integer.")
            power = exponent_val.real.num
        elif isinstance(exponent_val, int):
            power = exponent_val
        else:
            raise ValueError("Math Error: Exponent must be an integer.")
            
        if power < 0:
            raise ValueError("Math Error: Negative exponents on algebraic expressions are not supported.")
            
        if power == 0:
            return [Monomial(coefficient=Rational(1))]
            
        if len(left) == 1:
            m = left[0]
            new_coeff = m.coefficient ** power
            if m.is_constant():
                return [Monomial(coefficient=new_coeff)]
            else:
                return [Monomial(coefficient=new_coeff, variable=m.variable, power=m.power * power)]
                
        result = left
        for _ in range(power - 1):
            result = self.multiply_lists(result, left, '*')
        return result