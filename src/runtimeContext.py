import math
import matplotlib.pyplot as plt
import numpy as np
import copy


from .utils import tc, to_parseable_string

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

    def reset_context_options(self) -> None:
        self._angle_type = "deg"
        self._display_type = "default"
        from .utils import set_active_display_mode
        set_active_display_mode("default")

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
        # 1. Eagerly substitute external variables in rhs_tokens, ignoring the parameter

        from .matrix import Matrix

        param_clean = parameter.lower()
        substituted_tokens = []
        for token in rhs_tokens:
            if isinstance(token, str) and token.isalpha():
                token_clean = token.lower()
                if token_clean != param_clean and token_clean in self._variables:
                    val = self._variables[token_clean]
                    if isinstance(val, list):
                        from .utils import pretty_print
                        val_str = pretty_print(val, print_output=False)
                    else:
                        val_str = to_parseable_string(val)
                    substituted_tokens.append(f"({val_str})")
                else:
                    substituted_tokens.append(token)
            else:
                substituted_tokens.append(token)
        
        # Re-tokenize the joined string to handle implicit multiplications correctly
        joined_str = " ".join(substituted_tokens)
        from .parser import parse_free_form_equation
        class DummyArgs:
            verbose = False
        dummy_args = DummyArgs()
        token_dict = parse_free_form_equation(joined_str, dummy_args, self)
        rhs_tokens_substituted = [token_dict[i] for i in sorted(token_dict.keys())]

        # Validate syntax of function body and simplify it before storing
        from .mathParser import MathParser
        parser = MathParser(rhs_tokens_substituted, self, allow_unbound=True, shadowed_param=parameter)
        monomials = parser.parse_expression()
        if parser.peek() is not None:
            raise ValueError(f"Syntax Error: Unexpected token '{parser.peek()}' in function definition.")

        # Re-format the simplified monomials back into a clean string and re-tokenize it
        def format_monomial_clean(m) -> str:
            if m.is_constant():
                return str(m.coefficient)
            coeff_str = ""
            if m.coefficient == 1:
                coeff_str = ""
            elif m.coefficient == -1:
                coeff_str = "-"
            else:
                coeff_str = f"({to_parseable_string(m.coefficient)})*   "
            
            var_str = m.variable
            if m.power != 1:
                var_str = f"{var_str}^{m.power}"
            return f"{coeff_str}{var_str}"

        simplified_parts = []
        for m in monomials:
            simplified_parts.append(format_monomial_clean(m))
        simplified_str = " + ".join(simplified_parts).replace("+ -", "- ")
        if not simplified_str:
            simplified_str = "0"

        token_dict_simplified = parse_free_form_equation(simplified_str, dummy_args, self)
        rhs_tokens_simplified = [token_dict_simplified[i] for i in sorted(token_dict_simplified.keys())]

        # Update the caller's list in-place so that maths.py:assign prints the simplified form!
        rhs_tokens.clear()
        rhs_tokens.extend(rhs_tokens_simplified)

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

        parser = MathParser(tokens, self, allow_unbound=True, shadowed_param=param)
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
        
        from .utils import pretty_print
        base_expr = pretty_print(tokens, print_output=False)
        
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

        parser = MathParser(tokens, self, allow_unbound=True, shadowed_param=param)
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

        from .utils import tc
        print(f"\n{tc.BOLD}{tc.YELLOW}--- Curve Analysis ---{tc.RESET}")
        print(f"The parabola opens {tc.BOLD}{direction}{tc.RESET}.")
        print(f"The derivative is 0 at X = {tc.BOLD}{x_vertex:g}{tc.RESET}")
        print(f"The vertex is a {tc.BOLD}{extremum}{tc.RESET} at coordinates: ({tc.BOLD}{x_vertex:g}{tc.RESET}, {tc.BOLD}{y_vertex:g}{tc.RESET})")

        return {
            "direction": direction,
            "x_vertex": x_vertex,
            "y_vertex": y_vertex,
            "extremum": extremum
        }
    
    def display(self, prompt):
        import matplotlib
        from .utils import tc
        
        backend = matplotlib.get_backend()
        non_interactive_backends = {'agg', 'cairo', 'pdf', 'pgf', 'ps', 'svg', 'template'}
        if backend.lower() in non_interactive_backends:
            print(f"{tc.BOLD}{tc.RED}Error: Cannot display plots. The current Matplotlib backend '{backend}' is non-interactive (no display/GUI available).{tc.RESET}")
            return

        from .mathParser import MathParser
        from .matrix import Matrix

        error_names = []
        names = prompt.split(' ')
        functions_to_display = {}
        function_displayed = 0

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
    
        try:
            fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        except Exception as e:
            print(f"{tc.BOLD}{tc.RED}Error: Failed to initialize graphical window. Details: {e}{tc.RESET}")
            return
        
        for func_name, metadata in functions_to_display.items():
            param = metadata['parameter']
            tokens = metadata['tokens']
            
            try:
                # 1. Parse and simplify the function expression
                parser = MathParser(tokens, self, allow_unbound=True, shadowed_param=param)
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
                    
                    # if 
                        
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


                function_displayed += 1
                ax.plot(x_val, y_val, label=f"${func_name}({param}) = {simplified_expr}$", linewidth=2)
                
            except Exception as e:
                print(f"Failed to evaluate function '{func_name}': {e}")
                continue


        if function_displayed == 0:
            raise ValueError("No valid functions could be evaluated for display. Please check the function definitions and ensure they are valid.")
        
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
        from .utils import pretty_print, tc
        
        print(f"{tc.BOLD}{tc.YELLOW}Constants:{tc.RESET}")
        for const_name, value in self._immutable_constants.items():
            print(f"  {tc.CYAN}{const_name}{tc.RESET} = {tc.BOLD}{value}{tc.RESET}")
        print(f"{tc.BOLD}{tc.YELLOW}Built-in Functions:{tc.RESET}")
        for func_name, func_data in self._builtins.items():
            print(f"  {tc.BLUE}{func_name}{tc.RESET}")

        print("-------------------------")
        print(f"{tc.BOLD}{tc.YELLOW}Variables:{tc.RESET}")
        for var_name, value in self._variables.items():
            print(f"  {tc.MAGENTA}{var_name}{tc.RESET} = {tc.BOLD}{pretty_print([value], print_output=False)}{tc.RESET}")

        print(f"{tc.BOLD}{tc.YELLOW}Functions:{tc.RESET}")
        for func_name, func_data in self._functions.items():
            tokens_str = pretty_print(func_data["tokens"], print_output=False)
            print(f"  {tc.GREEN}{func_name}{tc.RESET}({tc.BOLD}{func_data['parameter']}{tc.RESET}) = {tc.BOLD}{tokens_str}{tc.RESET}")

    def transpose(self, name):
        from .matrix import Matrix

        names = name.split(' ')
        if names and len(names) > 1:
            raise ValueError("Only one matrix can be transposed at a time.")
        clean_name = names[0].strip().lower()
        matrix = self.lookup_variable(clean_name)
        
        if matrix is None or not isinstance(matrix, Matrix):
            raise ValueError(f"Variable '{names[0]}' is not a matrix or does not exist in context.")
        from .utils import tc
        transposed_matrix = matrix.transpose()

        print(f"{tc.BOLD}{tc.GREEN}{transposed_matrix}{tc.RESET}")
        return transposed_matrix
    
    def inverse(self, name):
        from .matrix import Matrix
        from .utils import tc

        names = name.split(' ')
        if names and len(names) > 1:
            raise ValueError("Only one matrix can be inverted at a time.")
        clean_name = names[0].strip().lower()
        matrix = self.lookup_variable(clean_name)
        
        if matrix is None or not isinstance(matrix, Matrix):
            raise ValueError(f"Variable '{names[0]}' is not a matrix or does not exist in context.")
        inverted_matrix = matrix.inverse()

        print(f"{tc.BOLD}{tc.GREEN}{inverted_matrix}{tc.RESET}")
        return inverted_matrix

    def determinant(self, name):
        from .matrix import Matrix
        from .utils import tc

        names = name.split(' ')
        if names and len(names) > 1:
            raise ValueError("Only one matrix can be evaluated for determinant at a time.")
        clean_name = names[0].strip().lower()
        matrix = self.lookup_variable(clean_name)
        
        if matrix is None or not isinstance(matrix, Matrix):
            raise ValueError(f"Variable '{names[0]}' is not a matrix or does not exist in context.")
        det_value = matrix.determinant()

        print(f"Determinant of {tc.BOLD}{names[0]}{tc.RESET}: {tc.BOLD}{tc.GREEN}{det_value}{tc.RESET}")
        return det_value

    def norm(self, name):
        from .matrix import Matrix
        from .utils import tc

        names = name.split(' ')
        if names and len(names) > 1:
            raise ValueError("Only one matrix/vector can be evaluated for norm at a time.")
        clean_name = names[0].strip().lower()
        matrix = self.lookup_variable(clean_name)
        
        if matrix is None or not isinstance(matrix, Matrix):
            raise ValueError(f"Variable '{names[0]}' is not a matrix or vector, or does not exist in context.")
        norm_value = matrix.norm()

        if "L2" in norm_value:
            print(f"Vector Norms of {tc.BOLD}{names[0]}{tc.RESET}: L1={tc.BOLD}{norm_value['L1']}{tc.RESET}, L2={tc.BOLD}{tc.GREEN}{norm_value['L2']}{tc.RESET}, Linf={tc.BOLD}{norm_value['Linf']}{tc.RESET}")
        else:
            print(f"Matrix Norms of {tc.BOLD}{names[0]}{tc.RESET}: L1 (column sum)={tc.BOLD}{norm_value['L1']}{tc.RESET}, Linf (row sum)={tc.BOLD}{norm_value['Linf']}{tc.RESET}, Frobenius={tc.BOLD}{tc.GREEN}{norm_value['Frobenius']}{tc.RESET}")
        return norm_value