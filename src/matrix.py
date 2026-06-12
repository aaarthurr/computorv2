from .number import Rational, ComplexRational

class Matrix:
    """Represents a matrix of exact Rational or ComplexRational values."""
    
    def __init__(self, data: list):
        if not data or not isinstance(data, list) or not all(isinstance(row, list) for row in data):
            raise ValueError("Matrix Error: Invalid matrix data structure.")
        
        self.rows = len(data)
        self.cols = len(data[0]) if self.rows > 0 else 0
        
        if self.rows == 0 or self.cols == 0:
            raise ValueError("Matrix Error: Empty matrix dimensions are not allowed.")
            
        self.data = []
        for row in data:
            if len(row) != self.cols:
                raise ValueError("Matrix Error: Inconsistent row dimensions.")
            new_row = []
            for val in row:
                if isinstance(val, (int, Rational, ComplexRational)):
                    new_row.append(val)
                else:
                    raise ValueError(f"Matrix Error: Unsupported element type {type(val)}")
            self.data.append(new_row)

    def __add__(self, other):
        if not isinstance(other, Matrix):
            return NotImplemented
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError(f"Matrix Error: Addition dimension mismatch ({self.rows}x{self.cols} vs {other.rows}x{other.cols}).")
        
        new_data = [
            [self.data[i][j] + other.data[i][j] for j in range(self.cols)]
            for i in range(self.rows)
        ]
        return Matrix(new_data)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if not isinstance(other, Matrix):
            return NotImplemented
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError(f"Matrix Error: Subtraction dimension mismatch ({self.rows}x{self.cols} vs {other.rows}x{other.cols}).")
        
        new_data = [
            [self.data[i][j] - other.data[i][j] for j in range(self.cols)]
            for i in range(self.rows)
        ]
        return Matrix(new_data)

    def __rsub__(self, other):
        if not isinstance(other, Matrix):
            return NotImplemented
        return other.__sub__(self)

    def __neg__(self):
        new_data = [
            [-self.data[i][j] for j in range(self.cols)]
            for i in range(self.rows)
        ]
        return Matrix(new_data)

    def __mul__(self, other):
        if isinstance(other, Matrix):
            if self.rows != other.rows or self.cols != other.cols:
                raise ValueError(f"Matrix Error: Element-wise multiplication dimension mismatch ({self.rows}x{self.cols} vs {other.rows}x{other.cols}).")
            new_data = [
                [self.data[i][j] * other.data[i][j] for j in range(self.cols)]
                for i in range(self.rows)
            ]
            return Matrix(new_data)
        elif isinstance(other, (int, Rational, ComplexRational)):
            new_data = [
                [self.data[i][j] * other for j in range(self.cols)]
                for i in range(self.rows)
            ]
            return Matrix(new_data)
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def matmul(self, other):
        if not isinstance(other, Matrix):
            raise ValueError("Matrix Error: Matrix product is only defined between two matrices.")
        if self.cols != other.rows:
            raise ValueError(f"Matrix Error: Matrix product dimension mismatch ({self.rows}x{self.cols} vs {other.rows}x{other.cols}).")
        
        has_complex = any(isinstance(x, ComplexRational) for row in self.data for x in row) or \
                      any(isinstance(x, ComplexRational) for row in other.data for x in row)
        zero = ComplexRational(Rational(0)) if has_complex else Rational(0)
        
        new_data = []
        for i in range(self.rows):
            new_row = []
            for j in range(other.cols):
                val = zero
                for k in range(self.cols):
                    val = val + self.data[i][k] * other.data[k][j]
                new_row.append(val)
            new_data.append(new_row)
        return Matrix(new_data)

    def __pow__(self, power):
        if self.rows != self.cols:
            raise ValueError("Matrix Error: Matrix power is only defined for square matrices.")
        if not isinstance(power, int):
            raise ValueError("Matrix Error: Matrix exponent must be an integer.")
        if power < 0:
            raise ValueError("Matrix Error: Negative matrix exponents are not supported.")
            
        if power == 0:
            has_complex = any(isinstance(x, ComplexRational) for row in self.data for x in row)
            one = ComplexRational(Rational(1)) if has_complex else Rational(1)
            zero = ComplexRational(Rational(0)) if has_complex else Rational(0)
            
            new_data = [
                [one if i == j else zero for j in range(self.cols)]
                for i in range(self.rows)
            ]
            return Matrix(new_data)
            
        res = self
        for _ in range(power - 1):
            res = res.matmul(self)
        return res

    def __mod__(self, other):
        if isinstance(other, (int, Rational)):
            new_data = [
                [self.data[i][j] % other for j in range(self.cols)]
                for i in range(self.rows)
            ]
            return Matrix(new_data)
        raise ValueError("Matrix Error: Modulo is only supported with a real rational scalar divisor.")

    def __truediv__(self, other):
        if isinstance(other, (int, Rational, ComplexRational)):
            new_data = [
                [self.data[i][j] / other for j in range(self.cols)]
                for i in range(self.rows)
            ]
            return Matrix(new_data)
        return NotImplemented

    def __eq__(self, other):
        if not isinstance(other, Matrix):
            return False
        if self.rows != other.rows or self.cols != other.cols:
            return False
        for i in range(self.rows):
            for j in range(self.cols):
                if self.data[i][j] != other.data[i][j]:
                    return False
        return True

    def __str__(self):
        lines = []
        mode = getattr(self.__class__, 'format_mode', 'auto')
        for row in self.data:
            row_str = " , ".join(self._format_element(x, mode) for x in row)
            lines.append(f"[ {row_str} ]")
        return "\n".join(lines)

    def _format_element(self, val, mode) -> str:
        from .utils import format_rational, format_complex
        if isinstance(val, ComplexRational):
            return format_complex(val, mode)
        elif isinstance(val, Rational):
            return format_rational(val, mode)
        return str(val)

    def __repr__(self):
        return self.__str__()
