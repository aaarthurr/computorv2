import math

class Rational:
    """Represents an exact rational number (numerator / denominator)."""
    
    def __init__(self, numerator: int, denominator: int = 1):
        if denominator == 0:
            raise ZeroDivisionError("Division by zero: Denominator cannot be zero.")
        
        # Enforce sign consistency: denominator must always be positive
        sign = -1 if (numerator < 0) ^ (denominator < 0) else 1
        
        # Automatically simplify the fraction to its irreducible form using GCD
        gcd = math.gcd(abs(numerator), abs(denominator))
        
        self.num = (abs(numerator) // gcd) * sign
        self.den = abs(denominator) // gcd

    @classmethod
    def from_string(cls, value: str):
        """
        Robust string parser to handle standard integers and decimals.
        Converts '4.5' into 45/10, which __init__ automatically reduces to 9/2.
        """
        if '.' in value:
            integer_part, decimal_part = value.split('.')
            # Calculate the denominator based on the number of decimal places
            # e.g., .123 means denominator is 1000 (10^3)
            denominator = 10 ** len(decimal_part)
            numerator = int(integer_part + decimal_part)
            return cls(numerator, denominator)
        else:
            return cls(int(value), 1)

    # --- Operator Overloading for Addition ---
    def __add__(self, other):
        if isinstance(other, int):
            other = Rational(other)
            
        if isinstance(other, Rational):
            # Math formula: a/b + c/d = (ad + bc) / bd
            return Rational(self.num * other.den + other.num * self.den, self.den * other.den)
            
        # If it's a ComplexRational, defer to its __radd__ method
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __neg__(self):
        """Returns the negated version of the fraction: -self"""
        return Rational(-self.num, self.den)

    def __sub__(self, other):
        if isinstance(other, int):
            other = Rational(other)
            
        if isinstance(other, Rational):
            # A - B is exactly equivalent to A + (-B)
            return self + (-other)
            
        return NotImplemented

    def __rsub__(self, other):
        # Handles: 5 - Rational(1, 2) -> 5 + (-Rational(1, 2))
        return -self + other


    # --- Operator Overloading for Multiplication ---
    def __mul__(self, other):
        if isinstance(other, int):
            other = Rational(other)
            
        if isinstance(other, Rational):
            # Math formula: a/b * c/d = ac / bd
            return Rational(self.num * other.num, self.den * other.den)
            
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def reciprocal(self):
        """Returns 1 / self (flips the numerator and denominator)"""
        if self.num == 0:
            raise ZeroDivisionError("Math Error: Cannot divide by zero.")
        return Rational(self.den, self.num)

    def __truediv__(self, other):
        if isinstance(other, int):
            other = Rational(other)
            
        if isinstance(other, Rational):
            # A / B is exactly equivalent to A * (1 / B)
            return self * other.reciprocal()
            
        return NotImplemented

    def __rtruediv__(self, other):
        # Handles: 5 / Rational(2, 3) -> 5 * Rational(3, 2)
        if isinstance(other, int):
            other = Rational(other)
        return other * self.reciprocal()

    def __mod__(self, other):
        if isinstance(other, int):
            other = Rational(other)
            
        if isinstance(other, Rational):
            if other.num == 0:
                raise ZeroDivisionError("Math Error: Modulo by zero.")
            common_den = self.den * other.den
            self_num = self.num * other.den
            other_num = other.num * self.den
            remainder_num = self_num % other_num
            return Rational(remainder_num, common_den)
            
        return NotImplemented

    def __rmod__(self, other):
        if isinstance(other, int):
            other = Rational(other)
        return other.__mod__(self)


    def __repr__(self):
        if self.den == 1:
            return f"{self.num}"
        return f"{self.num}/{self.den}"

    def __str__(self):
        from .utils import format_rational
        return format_rational(self)

    def __eq__(self, other):
        """
        Crucial for the parser's compress_monomials to check if a coefficient is 0.
        """
        if isinstance(other, int):
            return self.num == other and self.den == 1
        if isinstance(other, Rational):
            return self.num == other.num and self.den == other.den
        return False

    def __abs__(self):
        """
        Required because ComplexRational's __repr__ calls abs(self.imag).
        """
        return Rational(abs(self.num), self.den)

    def __pow__(self, power):
        """
        Handles polynomial exponentiation (e.g., squaring a fraction).
        Currently restricted to integer powers to avoid forcing irrational numbers 
        (like sqrt(2)) back into the Rational class.
        """
        if not isinstance(power, int):
            raise ValueError("Math Error: Rational numbers currently only support integer exponentiation.")
        
        if power == 0:
            return Rational(1, 1)
        if power < 0:
            return Rational(self.den ** abs(power), self.num ** abs(power))
        
        return Rational(self.num ** power, self.den ** power)



class ComplexRational:
    """Represents a complex number with exact rational coefficients: real + imag * i"""
    
    def __init__(self, real, imag=0):
        self.real = real if isinstance(real, Rational) else Rational(int(real))
        self.imag = imag if isinstance(imag, Rational) else Rational(int(imag))

    def __add__(self, other):
        if isinstance(other, (int, Rational)):
            other = ComplexRational(other, Rational(0))
            
        if isinstance(other, ComplexRational):
            return ComplexRational(self.real + other.real, self.imag + other.imag)
            
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __neg__(self):
        return ComplexRational(-self.real, -self.imag)

    def __sub__(self, other):
        if isinstance(other, (int, Rational)):
            other = ComplexRational(other, Rational(0))
            
        if isinstance(other, ComplexRational):
            return self + (-other)
            
        return NotImplemented

    def __rsub__(self, other):
        return -self + other
        
    def __mul__(self, other):
        if isinstance(other, (int, Rational)):
            other = ComplexRational(other, Rational(0))
            
        if isinstance(other, ComplexRational):
            real_part = (self.real * other.real) - (self.imag * other.imag)
            imag_part = (self.real * other.imag) + (self.imag * other.real)
            return ComplexRational(real_part, imag_part)
            
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def conjugate(self):
        """Returns the complex conjugate: conj(a + bi) = a - bi"""
        return ComplexRational(self.real, -self.imag)

    def __truediv__(self, other):
        if isinstance(other, (int, Rational)):
            other = ComplexRational(other, Rational(0))
            
        if isinstance(other, ComplexRational):
            denominator_scalar = (other.real * other.real) + (other.imag * other.imag)
            if denominator_scalar.num == 0:
                raise ZeroDivisionError("Math Error: Cannot divide by a complex zero value.")
                
            numerator_complex = self * other.conjugate()
            
            return ComplexRational(
                numerator_complex.real / denominator_scalar,
                numerator_complex.imag / denominator_scalar
            )
            
        return NotImplemented

    def __rtruediv__(self, other):
        if isinstance(other, (int, Rational)):
            other = ComplexRational(other, Rational(0))
        return other / self

    def __eq__(self, other):
        if isinstance(other, (int, float, Rational)):
            other = ComplexRational(other, Rational(0))
        if isinstance(other, ComplexRational):
            return self.real == other.real and self.imag == other.imag
        return False

    def __repr__(self):
        # Purely real (includes 0 + 0i)
        if self.imag.num == 0:
            return f"{self.real}"
            
        # Purely imaginary
        if self.real.num == 0:
            return f"{self.imag}i"
            
        # Standard complex layout
        sign = "+" if self.imag.num > 0 else "-"
        # Utilizes the newly added Rational.__abs__ to prevent printing "4 + -3i"
        return f"{self.real} {sign} {abs(self.imag)}i"

    def __str__(self):
        from .utils import format_complex
        return format_complex(self)