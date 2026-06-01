import copy

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
                    m._coefficient = -m._coefficient # Accessing via property rules
            terms.extend(right_terms)
        return self.compress_monomials(terms)

    # --- PEMDAS LAYER 2: Multiplication & Division ---
    def parse_term(self) -> list:
        factors = self.parse_factor()
        while self.peek() in ('*', '/', '**'):
            op = self.consume()
            right_factors = self.parse_factor()
            # Here you cross-multiply the lists using your Monomial __mul__ logic
            factors = self.multiply_lists(factors, right_factors, op)
        return factors

    # --- PEMDAS LAYER 3: Literals, Parens, Variables, Functions ---
    def parse_factor(self) -> list:
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
                return copy.deepcopy(stored_val)
            
            # If not found, check our security lock!
            if self.allow_unbound:
                # We are solving an equation (e.g., 'x = 0?'), so keep 'x' as a symbolic unknown
                return [Monomial(coefficient=1, variable=token, power=1)]
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
            # Extract the raw number from the Monomial, run python math, and wrap it back
            # Example: abs(-5) -> 5
            raw_val = argument_monomials[0].coefficient 
            result = func_data["callback"](raw_val)
            return [Monomial(coefficient=result)]
        else:
            # User defined function substitution logic goes here...
            pass

    def compress_monomials(self, term_list: list) -> list:
        """Groups terms with the same power to keep the list flat and clean."""
        # Combines [2x, 3x] into [5x]
        return term_list 

    def multiply_lists(self, left: list, right: list, op: str) -> list:
        """Distributes multiplication across two Monomial lists."""
        return left # Logic placeholder