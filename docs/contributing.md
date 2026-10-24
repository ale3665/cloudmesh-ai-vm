# Contributing

We welcome contributions to make `cloudmesh-ai-vm` more powerful and supportive of more clouds!

## How to Contribute

### Adding a New Provider

1. **Check libcloud**: See if the provider is already supported by `libcloud`. If so, inherit from `LibcloudManager`.
2. **Implement Interface**: If it's a custom provider, inherit from `CloudBaseManager` and implement all abstract methods.
3. **Add Config**: Update the `clouds.yaml` example in the documentation to show required credentials.
4. **Register**: Add your provider to the `PROVIDERS` map in `src/main.py`.
5. **Test**: Create a new test file in `tests/` using `unittest.mock`.

### Development Workflow

- **Branching**: All active development and feature integration happen in the `dev2` branch. Please create your feature branches from `dev2` rather than `main`.
- **Commits**: Use descriptive commit messages.
- **PRs**: Submit a Pull Request targeting the `dev2` branch with a clear description of the changes and examples of how to use the new feature.

## Code Formatting

To maintain a consistent style across the codebase, please format your code before committing.

### Ruff
We use `ruff` for both linting and formatting. You can run it manually:

```bash
# Check for linting issues
ruff check .

# Automatically fix linting issues
ruff check --fix .

# Format the code
ruff format .
```

### Pre-commit Hooks
The project includes a `.pre-commit-config.yaml` file. We recommend installing the `pre-commit` framework to automate formatting on every commit:

```bash
pip install pre-commit
pre-commit install
```
This will ensure that `ruff` is run automatically before each commit.

## Coding Standards

- Follow **PEP 8** guidelines.
- Use **type hinting** for all method signatures.
- Ensure all new functionality is covered by **unit tests**.
