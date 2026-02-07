# Contributing to GPT-OS

Thank you for your interest in contributing to GPT-OS! This document provides guidelines and instructions for contributing.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Your environment (OS, Python version, etc.)
- Any relevant logs or screenshots

### Suggesting Features

We love new ideas! To suggest a feature:
- Open an issue with the "feature request" label
- Describe the feature and its benefits
- Explain how it would work
- Consider potential challenges

### Submitting Pull Requests

1. **Fork the repository** and create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow the existing code style
   - Add comments for complex logic
   - Update documentation if needed

3. **Test your changes**:
   - Ensure the shell still works correctly
   - Test with various natural language inputs
   - Check for any security issues

4. **Commit your changes**:
   ```bash
   git commit -m "Add: brief description of your changes"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**:
   - Provide a clear description of the changes
   - Reference any related issues
   - Explain why the changes are beneficial

## Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Keep functions focused and concise
- Add docstrings to functions and classes

### Security Considerations

- Never auto-execute commands without user confirmation
- Always validate and sanitize user input
- Be cautious with file operations and system commands
- Test dangerous command detection thoroughly

### Testing

Before submitting a PR, test:
- Basic natural language commands
- Edge cases and error handling
- Dangerous command detection
- Built-in commands (help, history, etc.)

## Areas We Need Help

- **Documentation**: Improve README, add tutorials
- **Testing**: Create test cases and automated tests
- **Features**: Implement items from the roadmap
- **Translations**: Add support for more languages
- **Bug Fixes**: Fix reported issues
- **Performance**: Optimize response times

## Questions?

If you have questions, feel free to:
- Open a discussion on GitHub
- Comment on existing issues
- Reach out to maintainers

Thank you for contributing to GPT-OS! 🚀
