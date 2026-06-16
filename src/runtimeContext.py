import math
import matplotlib.pyplot as plt
import numpy as np
import copy

class RuntimeContext:
    """
    Manages symbol tables with built-in transcendental constants and functions.
    Protects immutable system environments from unauthorized mutations.
    """
    def __init__(self):
        # Seed core un-writeable system values
        self._angle_type = "deg"  # Default angle type for trigonometric functions

        self._display_type = "default"  # Default display type for output formatting
        from .utils import set_active_display_mode
        set_active_display_mode("default")

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
            "sin": lambda x: math.sin(math.radians(x) if self._angle_type == "deg" else x),
            "cos": lambda x: math.cos(math.radians(x) if self._angle_type == "deg" else x),
            "tan": lambda x: math.tan(math.radians(x) if self._angle_type == "deg" else x),
            "abs": abs
        }

        # User-allocated space tables
        self._variables = {}
        self._functions = {}

    def set_to_rad(self) -> None:
        self._angle_type = "rad"

    def set_to_deg(self) -> None:
        self._angle_type = "deg"

    def set_to_frac(self) -> None:
        self._display_type = "frac"
        from .utils import set_active_display_mode
        set_active_display_mode("frac")
    
    def set_to_dec(self) -> None:
        self._display_type = "dec"
        from .utils import set_active_display_mode
        set_active_display_mode("dec")

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
        # Validate syntax of function body before storing
        from .mathParser import MathParser
        parser = MathParser(rhs_tokens, self, allow_unbound=True)
        parser.parse_expression()
        if parser.peek() is not None:
            raise ValueError(f"Syntax Error: Unexpected token '{parser.peek()}' in function definition.")

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
    

    def remove(self, name: str) -> bool:
        clean = name.lower()
        deleted = False
        
        # Remove from variables if present
        if clean in self._variables:
            del self._variables[clean]
            deleted = True
            
        # Remove from functions if present
        if clean in self._functions:
            del self._functions[clean]
            deleted = True
            
        return deleted


    def derivate(self, name) -> dict:

        #local import to prevent cicular
        from .mathParser import MathParser
        from .monomial import Monomial
        from .number import Rational


        if '(' in name:
            clean_name = name.split('(')[0].strip().lower()
        else:
            clean_name = name.strip().lower()

        if clean_name not in self._functions:
            raise ValueError(f"Function '{clean_name}' not found in context.")

        func_data = self._functions[clean_name]
        param = func_data["parameter"]
        tokens = func_data["tokens"]

        parser = MathParser(tokens, self, allow_unbound=True)
        monomials = parser.parse_expression()
        if parser.peek() is not None:
            raise ValueError(f"Unexpected token '{parser.peek()}' in function definition.")

        derived_monomials = []
        for m in monomials:
            if m.power > 0:
                new_coeff = m.coefficient * m.power
                derived_monomials.append(Monomial(new_coeff, m.variable, m.power - 1))
                
        if not derived_monomials:
            derived_monomials = [Monomial(Rational(0))]
            
        compressed = parser.compress_monomials(derived_monomials)
        
        base_expr = "".join(str(t) for t in tokens)
        
        derived_parts = []
        for m in compressed:
            m_str = str(m)
            derived_parts.append(m_str)
            
        derived_expr = " + ".join(derived_parts).replace("+ -", "- ")
        if not derived_expr:
            derived_expr = "0"
            
        return base_expr, param, derived_expr
    
        
    def analyze(self, name) -> dict:
        from .mathParser import MathParser
        from .monomial import Monomial
        from .number import Rational

        if '(' in name:
            clean_name = name.split('(')[0].strip().lower()
        else:
            clean_name = name.strip().lower()
            
        if clean_name not in self._functions:
            raise ValueError(f"Function '{clean_name}' not found in context.")

        # 1. Retrieve original monomials to build original poly coefficients
        func_data = self._functions[clean_name]
        tokens = func_data["tokens"]
        param = func_data["parameter"]

        parser = MathParser(tokens, self, allow_unbound=True)
        monomials = parser.parse_expression()
        if parser.peek() is not None:
            raise ValueError(f"Syntax Error: Unexpected token '{parser.peek()}'")

        poly = {}
        for m in monomials:
            coeff = m.coefficient
            if hasattr(coeff, 'imag') and coeff.imag.num != 0:
                raise ValueError("Cannot analyze functions with complex coefficients.")
            from .matrix import Matrix
            if isinstance(coeff, Matrix):
                raise ValueError("Cannot analyze functions returning matrices.")
            
            if hasattr(coeff, 'num'):
                val = float(coeff.num) / coeff.den
            else:
                val = float(coeff)
            
            if m.variable is None or m.variable == param:
                poly[m.power] = val

        a = poly.get(2, 0.0)
        has_higher_degree = any(pwr > 2 for pwr in poly.keys())
        if a == 0 or has_higher_degree:
            raise ValueError("Curve analysis is only supported for quadratic (degree 2) functions.")

        # 2. Call self.derivate as requested to calculate the information
        base_expr, param_name, derived_expr = self.derivate(clean_name)

        # 3. Build derived_poly from the coefficients of original poly
        derived_poly = {}
        for pwr, val in poly.items():
            if pwr > 0:
                derived_poly[pwr - 1] = val * pwr

        d_x = derived_poly.get(1, 0.0)
        d_c = derived_poly.get(0, 0.0)
        
        if d_x == 0:
            raise ValueError("Curve analysis is only supported for quadratic (degree 2) functions.")

        x_vertex = -d_c / d_x
        
        def eval_poly(p, x):
            res = 0.0
            for pwr, coeff in p.items():
                res += coeff * (x ** pwr)
            return res

        y_vertex = eval_poly(poly, x_vertex)
        
        extremum = "Minimum" if a > 0 else "Maximum"
        direction = "upwards" if a > 0 else "downwards"

        print("\n--- Curve Analysis ---")
        print(f"The parabola opens {direction}.")
        print(f"The derivative is 0 at X = {x_vertex:g}")
        print(f"The vertex is a {extremum} at coordinates: ({x_vertex:g}, {y_vertex:g})")

        return {
            "direction": direction,
            "x_vertex": x_vertex,
            "y_vertex": y_vertex,
            "extremum": extremum
        }


         

        
    def display(self, prompt):
        from .mathParser import MathParser
        from .matrix import Matrix

        error_names = []
        names = prompt.split(' ')
        functions_to_display = {}

        for name in names:
            if '(' in name:
                clean_name = name.split('(')[0].strip().lower()
            else:
                clean_name = name.strip().lower()

            if clean_name in self._functions:
                functions_to_display[clean_name] = self._functions[clean_name]
            else:
                error_names.append(name)
        
        if error_names and functions_to_display:
            print(f"Warning: The following functions are not registered in the context: {', '.join(error_names)}. Please register a function before using #display.")
        
        if not functions_to_display:
            raise ValueError("No valid functions found to display.")
        
        x_val = np.linspace(-40, 40, 500)
    
        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        
        for func_name, metadata in functions_to_display.items():
            param = metadata['parameter']
            tokens = metadata['tokens']
            
            try:
                # 1. Parse and simplify the function expression
                parser = MathParser(tokens, self, allow_unbound=True)
                monomials = parser.parse_expression()
                if parser.peek() is not None:
                    raise ValueError(f"Syntax Error: Unexpected token '{parser.peek()}'")
                
                # 2. Evaluate the simplified monomials over x_val
                y_val = np.zeros_like(x_val)
                for m in monomials:
                    coeff = m.coefficient
                    if hasattr(coeff, 'imag'):  # ComplexRational
                        if coeff.imag.num != 0:
                            raise ValueError("Math Error: Cannot plot complex-valued functions with imaginary parts.")
                        coeff = coeff.real
                    if isinstance(coeff, Matrix):
                        raise ValueError("Math Error: Cannot plot functions returning a Matrix.")
                        
                    if hasattr(coeff, 'num'):  # Rational
                        coeff_val = float(coeff.num) / coeff.den
                    else:
                        coeff_val = float(coeff)
                    
                    if m.variable is None or m.power == 0:
                        y_val += coeff_val
                    else:
                        y_val += coeff_val * (x_val ** m.power)
                
                # 3. Construct a simplified expression string for the legend
                simplified_parts = []
                for m in monomials:
                    simplified_parts.append(str(m))
                simplified_expr = " + ".join(simplified_parts).replace("+ -", "- ")
                if not simplified_expr:
                    simplified_expr = "0"
                
                # 4. Generate dynamic line styles using formatting anchors
                ax.plot(x_val, y_val, label=f"${func_name}({param}) = {simplified_expr}$", linewidth=2)
                
            except Exception as e:
                print(f"[Runtime Error] Failed to evaluate function '{func_name}': {e}")
                continue

        # 5. Presentation Layer & Aesthetics
        ax.axhline(0, color='black', linewidth=0.8, linestyle=':', alpha=0.5)
        ax.axvline(0, color='black', linewidth=0.8, linestyle=':', alpha=0.5)
        ax.grid(True, which='both', linestyle='--', alpha=0.4)
        
        ax.set_title('Dynamic Function Visualization Matrix', fontsize=12, fontweight='bold', pad=15)
        ax.set_xlabel('Independent Input Variable (Unified Domain)', fontsize=10)
        ax.set_ylabel('Calculated Range Outputs', fontsize=10)
        
        ax.legend(loc='best', frameon=True, facecolor='white')
        plt.tight_layout()
        
        # Display non-blocking canvas element
        plt.show()
        

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



    def transpose(self, name):
        from .matrix import Matrix

        names = name.split(' ')
        if names and len(names) > 1:
            raise ValueError("Only one matrix can be transposed at a time.")
        clean_name = names[0].strip().lower()
        matrix = self.lookup_variable(clean_name)
        
        if matrix is None or not isinstance(matrix, Matrix):
            raise ValueError(f"Variable '{names[0]}' is not a matrix or does not exist in context.")
        transposed_matrix = matrix.transpose()

        print(transposed_matrix)
        return transposed_matrix
    
    def inverse(self, name):
        from .matrix import Matrix

        names = name.split(' ')
        if names and len(names) > 1:
            raise ValueError("Only one matrix can be inverted at a time.")
        clean_name = names[0].strip().lower()
        matrix = self.lookup_variable(clean_name)
        
        if matrix is None or not isinstance(matrix, Matrix):
            raise ValueError(f"Variable '{names[0]}' is not a matrix or does not exist in context.")
        inverted_matrix = matrix.inverse()

        print(inverted_matrix)
        return inverted_matrix

    def determinant(self, name):
        from .matrix import Matrix

        names = name.split(' ')
        if names and len(names) > 1:
            raise ValueError("Only one matrix can be evaluated for determinant at a time.")
        clean_name = names[0].strip().lower()
        matrix = self.lookup_variable(clean_name)
        
        if matrix is None or not isinstance(matrix, Matrix):
            raise ValueError(f"Variable '{names[0]}' is not a matrix or does not exist in context.")
        det_value = matrix.determinant()

        print(f"Determinant of {names[0]}: {det_value}")
        return det_value


    def norm(self, name):
        from .matrix import Matrix

        names = name.split(' ')
        if names and len(names) > 1:
            raise ValueError("Only one matrix/vector can be evaluated for norm at a time.")
        clean_name = names[0].strip().lower()
        matrix = self.lookup_variable(clean_name)
        
        if matrix is None or not isinstance(matrix, Matrix):
            raise ValueError(f"Variable '{names[0]}' is not a matrix or vector, or does not exist in context.")
        norm_value = matrix.norm()

        if "L2" in norm_value:
            print(f"Vector Norms of {names[0]}: L1={norm_value['L1']}, L2={norm_value['L2']}, Linf={norm_value['Linf']}")
        else:
            print(f"Matrix Norms of {names[0]}: L1 (column sum)={norm_value['L1']}, Linf (row sum)={norm_value['Linf']}, Frobenius={norm_value['Frobenius']}")
        return norm_value