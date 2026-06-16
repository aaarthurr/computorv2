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
            raise ValueError("Addition is only defined between two matrices.")
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
            raise ValueError("Subtraction is only defined between two matrices.")
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError(f"Matrix Error: Subtraction dimension mismatch ({self.rows}x{self.cols} vs {other.rows}x{other.cols}).")
        
        new_data = [
            [self.data[i][j] - other.data[i][j] for j in range(self.cols)]
            for i in range(self.rows)
        ]
        return Matrix(new_data)

    def __rsub__(self, other):
        if not isinstance(other, Matrix):
            raise ValueError("Subtraction is only defined between two matrices.")
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
        raise ValueError("Division is only supported with a scalar divisor (int, Rational, or ComplexRational).")


    def __rtruediv__(self, other):
        raise ValueError("Math Error: Division of a scalar by a Matrix is not defined.")

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




    def transpose(self):
        new_data = [
            [self.data[j][i] for j in range(self.rows)]
            for i in range(self.cols)
        ]
        return Matrix(new_data)


    def determinant(self):
        if self.rows != self.cols:
            raise ValueError("Determinant is only defined for square matrices.")
        
        import copy
        data = copy.deepcopy(self.data)
        n = self.rows
        
        has_complex = any(isinstance(x, ComplexRational) for row in data for x in row)
        det = ComplexRational(Rational(1)) if has_complex else Rational(1)
        
        for i in range(n):
            pivot_row = i
            while pivot_row < n and data[pivot_row][i] == 0:
                pivot_row += 1
                
            if pivot_row == n:
                return ComplexRational(Rational(0)) if has_complex else Rational(0)
                
            if pivot_row != i:
                data[i], data[pivot_row] = data[pivot_row], data[i]
                det = -det
                
            for r in range(i + 1, n):
                factor = data[r][i] / data[i][i]
                for c in range(i, n):
                    data[r][c] = data[r][c] - factor * data[i][c]
                    
            det = det * data[i][i]
            
        return det

    def inverse(self):
        if self.rows != self.cols:
            raise ValueError("Matrix inverse is only defined for square matrices.")
            
        n = self.rows
        import copy
        data = copy.deepcopy(self.data)
        
        has_complex = any(isinstance(x, ComplexRational) for row in data for x in row)
        one = ComplexRational(Rational(1)) if has_complex else Rational(1)
        zero = ComplexRational(Rational(0)) if has_complex else Rational(0)
        
        aug = []
        for i in range(n):
            row_i = data[i] + [one if i == j else zero for j in range(n)]
            aug.append(row_i)
            
        for i in range(n):
            pivot_row = i
            while pivot_row < n and aug[pivot_row][i] == 0:
                pivot_row += 1
                
            if pivot_row == n:
                raise ValueError("Matrix is singular and cannot be inverted.")
                
            if pivot_row != i:
                aug[i], aug[pivot_row] = aug[pivot_row], aug[i]
                
            pivot_val = aug[i][i]
            for c in range(i, 2 * n):
                aug[i][c] = aug[i][c] / pivot_val
                
            for r in range(n):
                if r != i:
                    factor = aug[r][i]
                    for c in range(i, 2 * n):
                        aug[r][c] = aug[r][c] - factor * aug[i][c]
                        
        inv_data = [row[n:] for row in aug]
        return Matrix(inv_data)


    def vector_norm(self):
        if self.rows > 1 and self.cols > 1:
            raise ValueError("Matrix Error: Vector norm can only be computed on a 1xN or Nx1 matrix.")

        if self.rows > 1:
            vector = [self.data[i][0] for i in range(self.rows)]
        else:
            vector = self.data[0]

        l1_norm = Rational(0)
        l2_norm_sq = Rational(0)
        l_inf_norm = Rational(0)

        for val in vector:
            abs_val = abs(val)
            l1_norm = l1_norm + abs_val
            l2_norm_sq = l2_norm_sq + abs_val * abs_val
            if abs_val > l_inf_norm:
                l_inf_norm = abs_val

        from .utils import exact_or_float_sqrt
        l2_norm, _ = exact_or_float_sqrt(l2_norm_sq)

        return {
            "L1": l1_norm,
            "L2": l2_norm,
            "Linf": l_inf_norm
        }


    def matrix_norm(self):
        max_col_sum = Rational(0)
        max_row_sum = Rational(0)
        frobenius_sum_sq = Rational(0)

        for c in range(self.cols):
            current_col_sum = Rational(0)
            for r in range(self.rows):
                current_col_sum = current_col_sum + abs(self.data[r][c])
            
            if current_col_sum > max_col_sum:
                max_col_sum = current_col_sum

        for r in range(self.rows):
            current_row_sum = Rational(0)
            for c in range(self.cols):
                abs_val = abs(self.data[r][c])
                
                current_row_sum = current_row_sum + abs_val
                
                frobenius_sum_sq = frobenius_sum_sq + abs_val * abs_val
                
            if current_row_sum > max_row_sum:
                max_row_sum = current_row_sum

        from .utils import exact_or_float_sqrt
        frobenius_norm, _ = exact_or_float_sqrt(frobenius_sum_sq)

        return {
            "L1": max_col_sum,
            "Linf": max_row_sum,
            "Frobenius": frobenius_norm
        }

    def norm(self):
        if self.rows == 1 or self.cols == 1:
            return self.vector_norm()
        return self.matrix_norm()