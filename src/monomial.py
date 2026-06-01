class Monomial:
    """
    Represents an exact algebraic term: coefficient * (variable ^ power).
    """
    def __init__(self, coefficient, variable: str = None, power: int = 0):
        self.coefficient = coefficient
        self.variable = variable.lower() if isinstance(variable, str) else None
        self.power = int(power) if self.variable else 0

    def is_constant(self) -> bool:
        return self.variable is None or self.power == 0

    def __repr__(self) -> str:
        if self.is_constant():
            return f"{self.coefficient}"
        return f"{self.coefficient}*{self.variable}^{self.power}"