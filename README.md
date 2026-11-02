# Computor v2

**Computor v2** is an interactive command-line mathematical interpreter and symbolic/numerical calculator built from scratch in Python. Inspired by UNIX `bc` and modern computer algebra systems, it combines persistent variable and function management with exact rational/complex arithmetic, matrix and vector linear algebra, polynomial root-finding, symbolic differentiation, and multi-function curve plotting.

> Built as part of the **42** curriculum — all core mathematical types (`Rational`, `ComplexRational`, `Matrix`, `Monomial`) and the recursive-descent algebraic parser are implemented from scratch without external complex-number or linear-algebra libraries.

> [!WARNING]
> This repository is made public solely to showcase my curriculum progress. It is not intended to be copied or used as a base for personal work.
> Please do not use this code to validate your own 42 projects. Blindly copying this repository is considered plagiarism and will result in a **-42** grade for cheating. I take no responsibility for any academic penalties incurred by misusing this code.
---

## Table of Contents

- [Key Features](#key-features)
- [Prerequisites & Installation](#prerequisites--installation)
- [Quick Start](#quick-start)
- [Usage & Syntax Guide](#usage--syntax-guide)
  - [Variables & Data Types](#variables--data-types)
  - [Operators & Precedence](#operators--precedence)
  - [Built-in Constants & Functions](#built-in-constants--functions)
  - [Queries, Equality Checks & Equation Solving](#queries-equality-checks--equation-solving)
- [Options & `#` Commands](#options--commands)
  - [Passive Modifiers (Per-Query Flags)](#passive-modifiers-per-query-flags)
  - [Action / Override Commands](#action--override-commands)
- [History Expansion (`$n`)](#history-expansion-n)
- [Project Architecture](#project-architecture)

---

## Key Features

- **Exact Arithmetic Engine**: Custom `Rational` ($\mathbb{Q}$) and `ComplexRational` ($\mathbb{Q}[i]$) types using automatic GCD fraction reduction to eliminate floating-point precision loss.
- **Matrix & Vector Linear Algebra**: Arbitrary $M \times N$ matrices over $\mathbb{Q}$ and $\mathbb{C}$ supporting addition, subtraction, scalar/Hadamard product (`*`), matrix multiplication (`**`), integer powers (`^`), transpose, Gauss-Jordan inversion, Gaussian determinant, and vector/matrix norms ($L_1$, $L_2$, $L_\infty$, Frobenius).
- **Single-Variable Functions**: Define reusable functions `f(x) = ...` with automatic algebraic simplification, eager capture of defined variables, function composition `f(g(x))`, symbolic evaluation, and recursion-cycle protection.
- **Polynomial Solver**: Solves polynomial equations of degree $\le 2$ (`LHS = RHS ?`) in $\mathbb{R}$ and $\mathbb{C}$, distinguishing exact rational/complex roots from irrational approximations (`≃`).
- **Calculus & Curve Plotting**: Symbolic polynomial differentiation (`#derivate`), quadratic parabola/vertex analysis (`#curv`), and interactive multi-function plotting (`#display`) via `matplotlib`.
- **Interactive Shell UX**: ANSI-colored output, implicit multiplication (`2x`, `3(x+1)`), `#flag` modifiers, and `$n` history expansion.

---

## Prerequisites & Installation

### Requirements

- **Python 3.10+** (uses structural pattern matching `match`/`case` and union type annotations)
- **pip** (for installing optional plotting dependencies)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url> computorv2
   cd computorv2
   ```

2. **(Optional) Create and activate a virtual environment:**
   ```bash
   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Installs `matplotlib` and `numpy`, used exclusively for the `#display` graphical plotting feature.)*

4. **Launch the interpreter:**
   ```bash
   python main.py
   ```

To exit the interpreter at any time, type `exit` or `quit`, or press `Ctrl+C` / `Ctrl+D`.

---

## Quick Start

```text
> varA = 2 + 4 * 2 - 5 % 4 + 2 * (4 + 5)
27
> varB = 2 * i - 4
-4 + 2i
> funA(x) = x^2 + 2x + 1
x^2 + 2 * x + 1
> funA(3) = ?
16
> funA(x) = 0 ?
x = -1
> matA = [[1, 2]; [3, 4]]
[ 1 , 2 ]
[ 3 , 4 ]
> matA #inverse
[ -2 , 1 ]
[ 1.5 , -0.5 ]
```

---

## Usage & Syntax Guide

### Variables & Data Types

Identifiers (variable and function names) must contain **letters only** and are **case-insensitive** (`varA` and `vara` refer to the same symbol). Variables can be dynamically reassigned to any mathematical type by inference:

| Type | Syntax Example | Notes |
| :--- | :--- | :--- |
| **Rational ($\mathbb{Q}$)** | `a = 4.25` or `b = -4 / 3` | Stored internally as exact irreducible fractions. |
| **Complex ($\mathbb{Q}[i]$)** | `z = 2*i + 3` or `w = -4i - 4` | `i` is reserved as the imaginary unit ($i^2 = -1$). |
| **Matrix / Vector** | `M = [[1, 2]; [3, 4]]` | Columns separated by `,`, rows separated by `;`. |
| **Function** | `f(x) = 2*x^2 - 5x + 4` | Single-variable functions; external variables are substituted eagerly at definition time. |

> **Note:** Multi-letter identifiers such as `xx` are treated as a single variable name `xx`, not `x * x`. Implicit multiplication applies between numbers, parentheses, and identifiers (e.g., `2x`, `4(x + 1)`, `(x + 1)(x - 1)`).

### Operators & Precedence

From highest to lowest precedence:

| Precedence | Operator | Description | Example |
| :---: | :---: | :--- | :--- |
| **1** | `(...)`, `[[...]]` | Grouping parentheses & matrix literals | `2 * (3 + 4)` |
| **2** | `!` | Postfix factorial (non-negative integers) | `5! = ?` $\rightarrow$ `120` |
| **3** | `+`, `-` (unary) | Prefix sign operators (supports sign chains like `--` or `+-`) | `-4 + --2` |
| **4** | `^` | Non-negative integer exponentiation (scalars, polynomials, square matrices) | `(x + 2)^2`, `matA^0` |
| **5** | `*`, `**`, `/`, `%` | Scalar/Hadamard product `*`, Matrix product `**`, Division `/`, Modulo `%` | `A ** B`, `5 % 4` |
| **6** | `+`, `-` | Addition and subtraction | `a + b - 3` |

### Built-in Constants & Functions

Protected system symbols cannot be overwritten or deleted:

- **Constants**:
  - `i` — Imaginary unit ($0 + 1i$)
  - `pi` — $\pi \approx 3.14159265359$
  - `tau` — $\tau = 2\pi \approx 6.28318530718$
  - `e` — Euler's number $\approx 2.71828182846$
  - `phi` — Golden ratio $\varphi \approx 1.61803398875$
- **Functions**:
  - **Roots & Magnitude**: `sqrt(x)` (supports negative real inputs returning complex values), `cbrt(x)`, `abs(x)` (supports complex modulus $|a + bi|$)
  - **Exponentials & Logarithms**: `exp(x)`, `ln(x)` (natural log), `log(x)` (base-10 log)
  - **Trigonometry**: `sin(x)`, `cos(x)`, `tan(x)` *(default to **degrees**; append `#rad` for radians)*

### Queries, Equality Checks & Equation Solving

Appending `?` at the end of an instruction triggers **resolution mode**:

1. **Expression & Image Evaluation (`expr = ?` or `expr ?`)**:
   ```text
   > a = 12
   12
   > a + 2 = ?
   14
   > f(x) = 2x + 1
   2 * x + 1
   > f(f(x)) = ?
   4 * x + 3
   ```

2. **Boolean Equality Testing (`LHS = RHS ?` with no unbound unknowns)**:
   Evaluates both sides and prints `true` or `false`:
   ```text
   > 2^3 + 1 = 3^2 ?
   true
   ```

3. **Polynomial Equation Resolution (`LHS = RHS ?` with an unknown variable)**:
   Automatically reduces the equation to canonical form $P(x) = 0$ and solves for degrees $0$, $1$, and $2$ across $\mathbb{R}$ and $\mathbb{C}$:
   ```text
   > x^2 - 5x + 6 = 0 ?
   x1 = 2
   x2 = 3
   > x^2 + 1 = 0 ?
   x1 = -i
   x2 = i
   > x^2 - 2 = 0 ?
   x1 ≃ -1.41421
   x2 ≃ 1.41421
   ```

---

## Options & `#` Commands

Options are appended to the end of any input line using `#option` tags. They are split into **passive modifiers** (which adjust evaluation or number formatting for that command) and **override commands** (which perform dedicated operations).

### Passive Modifiers (Per-Query Flags)

Passive modifiers apply to the current instruction and automatically reset to defaults on the next prompt:

| Option | Effect | Example |
| :--- | :--- | :--- |
| `#rad` | Evaluates trigonometric functions (`sin`, `cos`, `tan`) in **radians** instead of degrees. | `cos(pi) = ? #rad` $\rightarrow$ `-1` |
| `#frac` | Forces rational and complex outputs to render as exact **fractions** (`p/q`). | `1 / 8 = ? #frac` $\rightarrow$ `1/8` |
| `#dec` | Forces rational and complex outputs to render as **decimals**. | `1 / 3 = ? #dec` $\rightarrow$ `0.333333333` |

### Action / Override Commands

Only one override option may be used per prompt:

| Command | Target | Description | Example |
| :--- | :--- | :--- | :--- |
| `#context` | *(none)* | Lists all built-in constants, built-in functions, and user-defined variables & functions. | `#context` |
| `#history` | *(none)* | Displays previously executed commands and their results, indexed as `$1`, `$2`, etc. | `#history` |
| `#delete` | Variable / Function | Deletes a user-defined variable or function from the runtime context. | `varA #delete` |
| `#derivate` | Function | Computes and displays the symbolic derivative $f'(x)$ of a stored polynomial function. | `funA #derivate` |
| `#curv` | Quadratic Function | Analyzes a degree-2 polynomial function: parabola direction, derivative zero, and vertex extremum `(x, y)`. | `funA #curv` |
| `#display` | Function(s) | Plots one or more stored real-valued functions over $[-40, 40]$ in an interactive `matplotlib` window. | `funA funB #display` |
| `#transpose` | Matrix | Computes the transpose $A^T$ of a stored matrix variable. | `matA #transpose` |
| `#inverse` | Square Matrix | Computes the exact inverse $A^{-1}$ via Gauss-Jordan elimination (if non-singular). | `matA #inverse` |
| `#determinant` | Square Matrix | Computes the exact determinant $\det(A)$ via Gaussian elimination. | `matA #determinant` |
| `#norm` | Vector / Matrix | Computes $L_1$, $L_2$, and $L_\infty$ norms for $1 \times N$ or $N \times 1$ vectors; or $L_1$, $L_\infty$, and Frobenius norms for matrices. | `matA #norm` |

---

## History Expansion (`$n`)

Every valid assignment and query is recorded in a deduplicated session log (`$1` is always the most recent command, `$2` the second most recent, and so on).

- **Re-run a previous command directly:**
  ```text
  > $1
  ```
- **Embed a previous expression inside a new calculation** (trailing `?` is stripped automatically during inline substitution):
  ```text
  > 2 + 3 = ?
  5
  > ($1) * 10 = ?
  Expanded: (2+3) * 10 = ?
  50
  ```

---

## Project Architecture

```text
computorv2/
├── main.py                # Interactive REPL loop, history expansion ($n), and #option dispatching
├── requirements.txt       # Python package dependencies (matplotlib)
└── src/
    ├── parser.py          # Input sanitization, #option extraction, lexical tokenization & implicit '*'
    ├── mathParser.py      # Recursive-descent parser & algebraic evaluator (monomial compression, functions, matrices)
    ├── maths.py           # High-level assignment, expression query, boolean check & solver routing
    ├── number.py          # Exact Rational (GCD-reduced p/q) and ComplexRational (a + bi) classes
    ├── matrix.py          # Matrix & vector arithmetic, matmul (**), transpose, inverse, determinant & norms
    ├── monomial.py        # Symbolic algebraic term representation: coefficient * variable^power
    ├── poly_solver.py     # Canonical polynomial reduction and degree 0, 1, and 2 root solver
    ├── runtimeContext.py  # Symbol tables, constants/built-ins, recursion guard, calculus (#derivate, #curv) & plotting (#display)
    └── utils.py           # Number/complex/monomial formatters (#frac, #dec, auto) and ANSI terminal colors
```
