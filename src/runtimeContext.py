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
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
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
        if clean in self._immutable_constants:
            return self._immutable_constants[clean]
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

    def store_function(self, name: str, parameter: str, rhs_tokens: list) -> None:
        if self.is_reserved_name(name):
            raise ValueError(f"Context Error: '{name}' is a protected system name.")
        if name.lower() in self._variables:
            raise ValueError(f"Context Error: '{name}' is already defined as a user variable.")
        
        # Check for immediate self-recursion
        if name.lower() in [t.lower() for t in rhs_tokens if isinstance(t, str)]:
            raise ValueError(f"Context Error: Infinite self-recursion blocked for function '{name}'.")
            
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