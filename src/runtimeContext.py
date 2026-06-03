import math
import copy

class RuntimeContext:
    """
    Manages symbol tables with built-in transcendental constants and functions.
    Protects immutable system environments from unauthorized mutations.
    """
    def __init__(self):
        # Seed core un-writeable system values
        self._immutable_constants = {
            "pi": 3.141592653589793,
            "phi": 1.618033988749895,
            "e": 2.718281828459045,
            "tau": 6.283185307179586
        }
        
        self._builtins = {
            "sqrt": math.sqrt,
            "cbrt": lambda x: x ** (1/3),
            "log": math.log10,
            "ln": math.log,
            "exp": math.exp,
            "sin": lambda x: math.sin(math.radians(x)),
            "cos": lambda x: math.cos(math.radians(x)),
            "tan": lambda x: math.tan(math.radians(x)),
            "abs": abs
        }

        # User-allocated space tables
        self._variables = {}
        self._functions = {}

    def is_reserved_name(self, name: str) -> bool:
        clean = name.lower()
        return (clean == 'i' or 
                clean in self._immutable_constants or 
                clean in self._builtins)

    def lookup_variable(self, name: str):
        clean = name.lower()
        if clean == 'i':
            from .number import Rational, ComplexRational
            return ComplexRational(Rational(0), Rational(1))
        if clean in self._immutable_constants:
            from .number import Rational
            val = self._immutable_constants[clean]
            return Rational.from_string(f"{val:.12f}".rstrip('0').rstrip('.'))
        return self._variables.get(clean, None)

    def lookup_function(self, name: str):
        clean = name.lower()
        if clean in self._builtins:
            return {"type": "BUILTIN", "callback": self._builtins[clean]}
        return self._functions.get(clean, None)

    def store_variable(self, name: str, value) -> None:
        if self.is_reserved_name(name):
            raise ValueError(f"Context Error: '{name}' is a protected system constant or function.")
        if name.lower() in self._functions:
            raise ValueError(f"Context Error: '{name}' is already defined as a user function.")
        self._variables[name.lower()] = copy.deepcopy(value)

    def check_recursion_cycle(self, start_func: str, current_func: str, functions_dict: dict, rhs_tokens: list) -> None:
        # Gather all user-defined functions called in this expression
        called_funcs = set()
        for token in rhs_tokens:
            if isinstance(token, str) and token.isalpha():
                token_clean = token.lower()
                if token_clean in functions_dict:
                    called_funcs.add(token_clean)
                    
        for func in called_funcs:
            # If we trace back to the function currently being defined, we found a cycle!
            if func == start_func:
                raise ValueError(
                    f"Context Error: Infinite loop detected! "
                    f"Defining '{start_func}' creates a recursive cycle involving '{current_func}' and '{func}'."
                )
            # Recursively inspect the dependencies of the called function
            if func in functions_dict:
                self.check_recursion_cycle(start_func, func, functions_dict, functions_dict[func]["tokens"])

    def store_function(self, name: str, parameter: str, rhs_tokens: list) -> None:
        if self.is_reserved_name(name):
            raise ValueError(f"Context Error: '{name}' is a protected system name.")
        if name.lower() in self._variables:
            raise ValueError(f"Context Error: '{name}' is already defined as a user variable.")
        
        # Check for immediate self-recursion
        if name.lower() in [t.lower() for t in rhs_tokens if isinstance(t, str)]:
            raise ValueError(f"Context Error: Infinite self-recursion blocked for function '{name}'.")
            
        param_clean = parameter.lower()
        for token in rhs_tokens:
            if isinstance(token, str) and token.isalpha():
                token_clean = token.lower()
                # 1. Allow already defined user functions, parameter, and system constants
                if (token_clean != param_clean and 
                    not self.is_reserved_name(token_clean) and 
                    token_clean not in self._functions):
                    raise ValueError(f"Context Error: Function definition '{name}' cannot reference external variable '{token}'.")
            
        # 2. Run the recursion loop check (LHS 'name' is start_func)
        self.check_recursion_cycle(name.lower(), name.lower(), self._functions, rhs_tokens)
            
        self._functions[name.lower()] = {
            "type": "USER",
            "parameter": parameter.lower(),
            "tokens": list(rhs_tokens)
        }

    def evaluate_function_call(self, func_name: str) -> list:
        """Executes built-in callbacks or substitutes user templates."""
        func_data = self.context.lookup_function(func_name)
        if func_data is None:
            raise ValueError(f"Runtime Error: Function '{func_name}' is not defined.")

        self.consume() # Eat '('
        argument_monomials = self.parse_expression() # Solve the inside math first
        self.consume() # Eat ')'

        if func_data["type"] == "BUILTIN":
            # SECURITY CHECK: Prevent passing variables into Python math functions
            # The argument must collapse down to exactly one purely constant chunk
            if len(argument_monomials) != 1 or not argument_monomials[0].is_constant():
                raise ValueError(
                    f"Math Error: Cannot evaluate built-in function '{func_name}' with an unresolved variable. "
                    "This engine only solves polynomial equations up to degree 2, not transcendental equations."
                )
            
            # Now it's 100% safe to extract the number and run Python math
            raw_val = argument_monomials[0].coefficient 
            result = func_data["callback"](raw_val)
            
            return [Monomial(coefficient=result)]
            
        else:
            # User defined function substitution logic...
            pass

    def print_context(self):
        print("Constants:")
        for const_name, value in self._immutable_constants.items():
            print(f"  {const_name} = {value}")
        print("Built-in Functions:")
        for func_name, func_data in self._builtins.items():
            print(f"  {func_name}")

        print("-------------------------")
        print("Variables:")
        for var_name, value in self._variables.items():
            print(f"  {var_name} = {value}")


        print("Functions:")
        for func_name, func_data in self._functions.items():
            tokens_str = "".join(str(t) for t in func_data["tokens"])
            print(f"  {func_name}({func_data['parameter']}) = {tokens_str}")