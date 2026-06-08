from langchain.tools import tool


@tool
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression and return the numeric result.

    Use this tool when:
    - The user explicitly asks to calculate, compute, or evaluate something
    - Numbers extracted from a document need to be combined mathematically
    - The user asks for a total, difference, percentage, ratio, or average
    - The user asks questions like "what is X% of Y?" or "how much is A + B?"
    - The user wants to verify or compute figures mentioned in a document

    Do NOT use this tool when:
    - The question is about document content (use retrieve_context instead)
    - The question requires reading the document to find numbers first —
      use retrieve_context first, then calculator if computation is needed
    - The input is not a mathematical expression

    Supported operators:
    - Addition:       3 + 4
    - Subtraction:    10 - 3.5
    - Multiplication: 4.2 * 1.12
    - Division:       250000 / 12
    - Power:          2 ** 8
    - Parentheses:    (4.2 + 3.8) / 2
    - Percentage:     85 % 100

    Args:
        expression: a valid mathematical expression as a plain string.
                    Use only numbers and operators — no text or variables.

    Examples:
        "4.2 * 1.12"          → "4.2 * 1.12 = 4.704"
        "100 - 37.5"          → "100 - 37.5 = 62.5"
        "(4.2 + 3.8) / 2"     → "(4.2 + 3.8) / 2 = 4.0"
        "250000 / 12"         → "250000 / 12 = 20833.333..."

    Returns:
        A string showing the expression and its result.
    """
    try:
        # Whitelist allowed characters — prevents code injection via eval
        allowed = set("0123456789+-*/(). %")
        if not all(c in allowed for c in expression):
            return (
                "Error: expression contains invalid characters. "
                "Only use numbers and operators: + - * / ** ( ) ."
            )

        result = eval(expression)  # safe: only digits and operators allowed

        # Format nicely: integers without decimals, floats with up to 6 decimal places
        if isinstance(result, int) or result == int(result):
            formatted = str(int(result))
        else:
            formatted = f"{result:.6f}".rstrip("0").rstrip(".")

        return f"{expression} = {formatted}"

    except ZeroDivisionError:
        return "Error: division by zero."
    except SyntaxError:
        return "Error: invalid mathematical expression. Check the syntax and try again."
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"