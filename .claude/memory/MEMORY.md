# Project Memory - vitai backend

## Python/FastAPI Development Guidelines

### Naming Conventions
- Use `snake_case` for variables, functions, and file names
- Use `PascalCase` for classes
- Use `SCREAMING_SNAKE_CASE` for constants
- Names should reflect what things ARE: if it's a regex pattern, call it `pattern`, not `phrase`
- Be specific in class names: `ConversationsAnswerTypeClassifier` not `AnswerTypeClassifier`

### Enums
- Use `StrEnum` for string-based enums (Python 3.11+)
- Benefits: type safety, auto-serialization, IDE autocomplete, prevents typos

### Error Handling
- Fail fast: raise exceptions early with clear messages
- Don't return `None` to hide errors - use `raise ValueError("...")`
- Use specific exception types (`ValueError`, `TypeError`, custom exceptions)
- Use FastAPI's `HTTPException` for API errors with proper status codes

### Code Organization
- Place classes where they logically belong
- One responsibility per file when possible
- Imports should be explicit: `from module import SpecificClass`

### Performance
- Don't check conditions that don't change inside loops
- Handle edge cases before entering loops

### Type Hints
- Always use type hints for function parameters and return values
- Use `list[str]` instead of `List[str]` (Python 3.9+)
- Be specific: `-> AnswerTypeEnum` not `-> str`

### Code Should Match Its Contract
- If a field is called `non_response_regex`, treat values as regex
- If a method returns an enum, type hint it as such

### FastAPI Specific
- Use Pydantic models for request/response validation
- Use dependency injection for shared resources
- Keep controllers/routers thin, business logic in services
- Use `async/await` consistently for I/O operations
- Use `response_model` in route decorators for response validation

### Pydantic Best Practices
- Separate request/response models even if similar (e.g., `UserCreate`, `UserResponse`)
- Use `ConfigDict` with `from_attributes=True` for ORM compatibility
- Use validators for complex field validation

### General Principles
- Don't over-engineer: only add complexity when needed
- Keep functions small and focused
- Prefer explicit over implicit
- Follow PEP 8 style guide - use `black` for formatting
- Use `ruff` or `pylint` for linting
- Keep dependencies minimal and up-to-date
- Write code that's easy to test
