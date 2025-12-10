## Python Code Standards

- Any python function must have type annotations and docstring.
- Any class must have a docstring.
- Any script must have a top-level docstring explaining its purpose.
- Use descriptive variable and function names to enhance code readability.
- Follow PEP 8 style guidelines for Python code.

## Error Handling & Logging

- Include error handling to manage potential exceptions gracefully.
- Use logging instead of print statements for tracking events that happen during execution.
- Follow best practices for security, such as validating user inputs and managing sensitive data appropriately.

## Development Approach

- Follow test-driven development: Write unit tests for all functions and methods BEFORE implementing them, to ensure code reliability. Include ALL possible edge cases.
- Ensure code is modular and reusable by breaking down large functions into smaller, focused ones.
- Adhere to the DRY (Don't Repeat Yourself) principle to avoid code duplication.

## Code Quality

- Do not include any unnecessary comments; the code should be self-explanatory through clear naming and structure.
- There should be no hard-coded values; use constants or configuration files instead.
- Ensure that all dependencies are listed in requirements.txt.

## Documentation

- Provide one comprehensive Documentation markdown (README.md or DOCUMENTATION.md) for the whole project.
- Update documentation whenever a new feature is added.
- Include: installation instructions, usage examples, and a brief overview of the codebase structure.
- Do not create additional markdown files unless explicitly asked.

## Database & Security

- When working with databases, use parameterized queries to prevent SQL injection attacks.
- Validate all user inputs before processing.
- Never commit sensitive data (credentials, API keys) to version control.