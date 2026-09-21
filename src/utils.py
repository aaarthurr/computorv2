import math
from .number import Rational, ComplexRational
from .monomial import Monomial

class tc:
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"


    # Interface Accents
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


active_display_mode = 'auto'

def set_active_display_mode(mode: str) -> None:
    global active_display_mode
    if mode == 'default':
        active_display_mode = 'auto'
    elif mode in ('frac', 'dec', 'auto'):
        active_display_mode = mode

def format_rational(r: Rational, mode: str = 'auto') -> str:
    if mode == 'auto':
        mode = active_display_mode

    if r.den == 1:
        return str(r.num)
    
    val = r.num / r.den
    if mode == 'dec':
        return f"{val:.9g}"

    if mode == 'frac':
        if r.den >= 1000000:
            temp = r.den
            while temp % 2 == 0:
                temp //= 2
            while temp % 5 == 0:
                temp //= 5
            if temp == 1:
                return f"{val:.9g}"
        return f"{r.num}/{r.den}"
        
    if (val * 100000000).is_integer():
        return f"{val:.9g}"
        
    frac_str = f"{r.num}/{r.den}"
    dec_str = f"{val:.9g}"
    if len(frac_str) < len(dec_str) + 2:
        return frac_str
    return dec_str

def format_complex(c: ComplexRational, mode: str = 'auto') -> str:
    if mode == 'auto':
        mode = active_display_mode

    real_str = format_rational(c.real, mode)
    imag_str = format_rational(c.imag, mode)
    
    if c.imag.num == 0:
        return real_str
    if c.real.num == 0:
        if c.imag.num == 1 and c.imag.den == 1:
            return "i"
        if c.imag.num == -1 and c.imag.den == 1:
            return "-i"
        if "/" in imag_str:
            return imag_str.replace("/", "i/")
        return f"{imag_str}i"
        
    sign = "+" if c.imag.num > 0 else "-"
    abs_imag = abs(c.imag)
    abs_imag_str = format_rational(abs_imag, mode)
    if abs_imag.num == 1 and abs_imag.den == 1:
        abs_imag_str = ""
        
    if "/" in abs_imag_str:
        abs_imag_str = abs_imag_str.replace("/", "i/")
        return f"{real_str} {sign} {abs_imag_str}"
    return f"{real_str} {sign} {abs_imag_str}i"

def exact_or_float_sqrt(r: Rational) -> tuple[Rational | float, bool]:
    if r.num < 0:
        raise ValueError("Cannot calculate real square root of a negative rational.")
    n_sqrt = math.isqrt(r.num)
    d_sqrt = math.isqrt(r.den)
    
    if n_sqrt * n_sqrt == r.num and d_sqrt * d_sqrt == r.den:
        return Rational(n_sqrt, d_sqrt), True
    return math.sqrt(r.num / r.den), False

def pretty_print(tokens, print_output: bool = True) -> str:
    if not tokens:
        return ""
        
    result = []
    n = len(tokens)
    builtins = {"sqrt", "cbrt", "log", "ln", "exp", "sin", "cos", "tan", "abs"}
    
    for i in range(n):
        current = str(tokens[i])
        
        next_token = str(tokens[i + 1]) if i + 1 < n else None
        prev_token = str(tokens[i - 1]) if i > 0 else None
        
        if current == '^':
            continue
        if prev_token == '^':
            result[-1] = f"{result[-1]}^{current}"
            continue
            
        # Check if the next token is a variable name to strip spacing around multiplication
        is_next_var = False
        if next_token and next_token.isalpha() and next_token.lower() not in builtins:
            is_next_var = True
            
        if current == '*' and is_next_var:
            if result:
                result[-1] = result[-1].rstrip()
            result.append(f"*{next_token}")
            continue
            
        if current.isalpha() and current.lower() not in builtins and prev_token == '*':
            continue
            
        if current in ('+', '-'):
            result.append(f" {current} ")
        else:
            result.append(current)

    formatted_str = "".join(result).strip()
    if print_output:
        print(f"{tc.CYAN}{formatted_str}{tc.RESET}")
    return formatted_str

def to_parseable_string(val):
    from .matrix import Matrix
    from .number import Rational, ComplexRational
    
    if isinstance(val, Matrix):
        rows_str = []
        for row in val.data:
            row_str = ",".join(to_parseable_string(elem) for elem in row)
            rows_str.append(f"[{row_str}]")
        return f"[{';'.join(rows_str)}]"
        
    elif isinstance(val, ComplexRational):
        from .utils import format_complex
        return format_complex(val, mode='frac')
        
    elif isinstance(val, Rational):
        from .utils import format_rational
        return format_rational(val, mode='frac')
        
    return str(val)

def format_monomial_list(monomials: list) -> str:
    if not monomials:
        return "0"
        
    from .matrix import Matrix
    from .number import Rational, ComplexRational
    
    def is_zero(coeff):
        if isinstance(coeff, (int, float)):
            return coeff == 0
        elif hasattr(coeff, 'num'):
            return coeff.num == 0
        elif hasattr(coeff, 'real') and hasattr(coeff, 'imag'):
            return coeff.real.num == 0 and coeff.imag.num == 0
        return False
        
    active_monomials = [m for m in monomials if not is_zero(m.coefficient)]
    
    if not active_monomials:
        return "0"
            
    parts = []
    for idx, m in enumerate(active_monomials):
        coeff = m.coefficient
        is_neg = False
        abs_coeff = coeff
        
        if isinstance(coeff, (int, float)):
            if coeff < 0:
                is_neg = True
                abs_coeff = -coeff
        elif isinstance(coeff, Rational):
            if coeff.num < 0:
                is_neg = True
                abs_coeff = abs(coeff)
        elif isinstance(coeff, ComplexRational):
            if coeff.imag.num == 0 and coeff.real.num < 0:
                is_neg = True
                abs_coeff = ComplexRational(abs(coeff.real), Rational(0))
                
        if m.is_constant():
            if idx > 0 and is_neg:
                parts.append("-")
                parts.append(to_parseable_string(abs_coeff))
            elif idx > 0:
                parts.append("+")
                parts.append(to_parseable_string(coeff))
            else:
                parts.append(to_parseable_string(coeff))
            continue

        if isinstance(coeff, Matrix):
            var_str = m.variable
            if m.power != 1:
                var_str = f"{var_str}^{m.power}"
            m_str = f"{var_str} * {to_parseable_string(coeff)}"
            if idx > 0:
                parts.append("+")
            parts.append(m_str)
            continue
            
        coeff_val_str = ""
        if abs_coeff == 1:
            coeff_val_str = ""
        else:
            coeff_val_str = f"{to_parseable_string(abs_coeff)} * "
            
        var_str = m.variable
        if m.power != 1:
            var_str = f"{var_str}^{m.power}"
            
        m_str = f"{coeff_val_str}{var_str}"
        
        if idx > 0:
            if is_neg:
                parts.append("-")
                parts.append(m_str)
            else:
                parts.append("+")
                if coeff == 1:
                    coeff_val_str = ""
                else:
                    coeff_val_str = f"{to_parseable_string(coeff)} * "
                parts.append(f"{coeff_val_str}{var_str}")
        else:
            if is_neg:
                if abs_coeff == 1:
                    parts.append(f"-{var_str}")
                else:
                    parts.append(f"-{coeff_val_str}{var_str}")
            else:
                if coeff == 1:
                    parts.append(var_str)
                else:
                    coeff_val_str = f"{to_parseable_string(coeff)} * "
                    parts.append(f"{coeff_val_str}{var_str}")
                    
    res_str = ""
    for i, p in enumerate(parts):
        if i == 0:
            res_str = p
        else:
            if p in ("+", "-"):
                res_str += f" {p}"
            else:
                if res_str[-1] in ("+", "-"):
                    res_str += f" {p}"
                else:
                    res_str += f" + {p}"
    return res_str