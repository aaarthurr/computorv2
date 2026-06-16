from .utils import format_rational, format_complex, exact_or_float_sqrt, tc
from .monomial import Monomial
from .mathParser import MathParser
from .runtimeContext import RuntimeContext
from .number import Rational, ComplexRational
from .mathParser import MathParser as MP

def format_polynomial(poly_dict: dict, var_name: str) -> str:
    if not poly_dict:
        return f"0 * {var_name}^0"
        
    parts = []
    # Print all coefficients including zeros in strict ascending power order
    max_deg = max(poly_dict.keys()) if poly_dict else 0
    for exp in range(max_deg + 1):
        coef = poly_dict.get(exp, Rational(0))
        
        # Format the sign/coefficient layout
        coef_str = format_rational(coef)
        if not parts:
            # First term
            parts.append(f"{coef_str} * {var_name}^{exp}")
        else:
            # Subsequent terms
            if coef.num >= 0:
                parts.append(f"+ {coef_str} * {var_name}^{exp}")
            else:
                parts.append(f"- {format_rational(abs(coef))} * {var_name}^{exp}")
                
    return " ".join(parts)


def parse_and_split_polynomial(rhs, lhs, unbound_vars: set, context: RuntimeContext) -> tuple[dict, str, int]:
    if len(unbound_vars) > 1:
        raise ValueError("Solving equations with multiple variables is not supported.")
        
    var_name = list(unbound_vars)[0]
    
    # Parse LHS & RHS allowing unbound variable
    lhs_parser = MathParser(lhs, context, allow_unbound=True)
    lhs_val = lhs_parser.parse_expression()
    if lhs_parser.peek() is not None:
        raise ValueError(f"Syntax Error: Unexpected token '{lhs_parser.peek()}' at end of LHS.")
        
    rhs_parser = MathParser(rhs, context, allow_unbound=True)
    rhs_val = rhs_parser.parse_expression()
    if rhs_parser.peek() is not None:
        raise ValueError(f"Syntax Error: Unexpected token '{rhs_parser.peek()}' at end of RHS.")

    # Subtract RHS from LHS: P(x) = LHS - RHS = 0
    neg_rhs = []
    for m in rhs_val:
        neg_rhs.append(Monomial(coefficient=-m.coefficient, variable=m.variable, power=m.power))
        
    sub_parser = MP([], context, allow_unbound=True)
    reduced_monomials = sub_parser.compress_monomials(lhs_val + neg_rhs)

    # Map exponents to coefficients
    poly = {}
    for m in reduced_monomials:
        poly[m.power] = m.coefficient

    # Display the canonical reduced form
    # print("Reduced form: " + format_polynomial(poly, var_name) + " = 0")
    
    max_deg = max(poly.keys()) if poly else 0
    # print(f"Polynomial degree: {max_deg}")
    
    return poly, var_name, max_deg


def solve_degree_zero(poly: dict):
    coef_zero = poly.get(0, Rational(0))
    if coef_zero.num == 0:
        print(f"{tc.BOLD}{tc.GREEN}All real numbers are solutions.{tc.RESET}")
    else:
        print(f"{tc.BOLD}{tc.RED}No solution.{tc.RESET}")


def solve_degree_one(poly: dict, var_name: str):
    # bx + c = 0
    b = poly.get(1, Rational(0))
    c = poly.get(0, Rational(0))
    sol = -c / b
    # print("The solution is:")
    print(f"{tc.BOLD}{var_name} = {format_rational(sol)}{tc.RESET}")


def solve_degree_two(poly: dict, var_name: str):
    # ax^2 + bx + c = 0
    a = poly.get(2, Rational(0))
    b = poly.get(1, Rational(0))
    c = poly.get(0, Rational(0))

    coeffs = [a, b, c]
    normalized_coeffs = []
    for coef in coeffs:
        if isinstance(coef, ComplexRational):
            if coef.imag.num != 0:
                raise ValueError("Math Error: Solving quadratic equations with complex coefficients is not supported.")
            normalized_coeffs.append(coef.real)
        else:
            normalized_coeffs.append(coef)
    

                
    a, b, c = normalized_coeffs
    
    # Discriminant
    disc = b*b - 4*a*c
    
    # Solve discriminant routes
    if disc.num > 0:
        #print("Discriminant is strictly positive, the two solutions are:")
        sqrt_disc, is_perfect = exact_or_float_sqrt(disc)
        denom = 2 * a
        
        if is_perfect:
            sol1 = (-b - sqrt_disc) / denom
            sol2 = (-b + sqrt_disc) / denom
            print(f"{tc.BOLD}{var_name}1 = {format_rational(sol1)}{tc.RESET}")
            print(f"{tc.BOLD}{var_name}2 = {format_rational(sol2)}{tc.RESET}")
        else:
            # Inexact float solutions
            sol1_float = (-float(b.num)/float(b.den) - sqrt_disc) / (2 * float(a.num)/float(a.den))
            sol2_float = (-float(b.num)/float(b.den) + sqrt_disc) / (2 * float(a.num)/float(a.den))
            print(f"{tc.BOLD}{var_name}1 ≃ {sol1_float:g}{tc.RESET}")
            print(f"{tc.BOLD}{var_name}2 ≃ {sol2_float:g}{tc.RESET}")
            
    elif disc.num == 0:
        #print("Discriminant is zero, the solution is:")
        sol = -b / (2 * a)
        print(f"{tc.BOLD}{var_name} = {format_rational(sol)}{tc.RESET}")
        
    else:
        #print("Discriminant is strictly negative, the two complex solutions are:")
        # Real and imaginary parts
        real_part = -b / (2 * a)
        imag_part_float, is_perfect = exact_or_float_sqrt(-disc)
        
        if is_perfect:
            # Exact ComplexRational representation
            sol1 = ComplexRational(real_part, -imag_part_float / (2 * a))
            sol2 = ComplexRational(real_part, imag_part_float / (2 * a))
            print(f"{tc.BOLD}{var_name}1 = {format_complex(sol1)}{tc.RESET}")
            print(f"{tc.BOLD}{var_name}2 = {format_complex(sol2)}{tc.RESET}")
        else:
            # Inexact ComplexRational representation
            denom_float = 2 * float(a.num)/float(a.den)
            real_float = -float(b.num)/float(b.den) / denom_float
            imag_float = imag_part_float / denom_float
            print(f"{tc.BOLD}{var_name}1 ≃ {real_float:g} - {imag_float:g}i{tc.RESET}")
            print(f"{tc.BOLD}{var_name}2 ≃ {real_float:g} + {imag_float:g}i{tc.RESET}")


def solve_polynomial(rhs, lhs, unbound_vars: set, var_name: str, context: RuntimeContext, args):
    poly, var, degree = parse_and_split_polynomial(rhs, lhs, unbound_vars, context)
    
    if degree == 0:
        solve_degree_zero(poly)
    elif degree == 1:
        solve_degree_one(poly, var)
    elif degree == 2:
        solve_degree_two(poly, var)
    else:
        print("The polynomial degree is greater than 2, I can't solve.")