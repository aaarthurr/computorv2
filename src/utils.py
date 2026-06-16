import math
from .number import Rational, ComplexRational
from .monomial import Monomial


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