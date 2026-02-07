# GPT-OS: AI-Powered Natural Language Linux Shell

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)

**GPT-OS** is a revolutionary Linux shell that understands natural language and translates it into precise Linux commands. It makes Linux accessible to users of any age, skill level, or technical background by allowing them to interact with their system using plain, conversational language.

## 🌟 Features

### Natural Language Understanding
- **Speak naturally**: Type commands in plain English or your local language
- **Multi-accent support**: Works with different dialects and accents
- **Context-aware**: Understands your current directory and system state
- **Conversational**: Get explanations in easy-to-understand language

### Safety & Security
- **Command preview**: Always shows what will be executed before running
- **Danger detection**: Identifies potentially destructive commands
- **Confirmation required**: Asks for approval before executing dangerous operations
- **Timeout protection**: Commands automatically timeout after 30 seconds

### User Experience
- **Chat-style interface**: Responses formatted like a conversation
- **Clear explanations**: Every command comes with a human-readable explanation
- **Command history**: Track what you've done
- **Built-in help**: Comprehensive help system

## 🚀 Quick Start

### Prerequisites

- **Operating System**: Linux (Ubuntu, Debian, Fedora, Arch, etc.)
- **Python**: Version 3.8 or higher
- **OpenAI API Key**: Get one from [OpenAI Platform](https://platform.openai.com/api-keys)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/hunix/gpt-os.git
   cd gpt-os
   ```

2. **Run the installation script**:
   ```bash
   ./install.sh
   ```

3. **Set your OpenAI API key**:
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```
   
   To make it permanent, add it to your `~/.bashrc`:
   ```bash
   echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
   source ~/.bashrc
   ```

4. **Launch GPT-OS**:
   ```bash
   ./gpt-os
   ```

### Optional: System-Wide Installation

To use GPT-OS from anywhere on your system:
```bash
sudo ln -s $(pwd)/gpt-os /usr/local/bin/gpt-os
```

Then simply run:
```bash
gpt-os
```

## 💡 Usage Examples

### Basic Commands

Instead of remembering complex syntax, just describe what you want:

| Natural Language | Traditional Command |
|-----------------|---------------------|
| "update my software" | `sudo apt update && sudo apt upgrade -y` |
| "show me all PDF files" | `find . -name "*.pdf"` |
| "check disk space" | `df -h` |
| "find large files" | `du -ah . \| sort -rh \| head -20` |
| "compress this folder" | `tar -czf folder.tar.gz folder/` |
| "show running processes" | `ps aux` |
| "check my IP address" | `curl ifconfig.me` |
| "install python packages" | `pip3 install package-name` |

### Advanced Usage

**Direct command execution**: Prefix with `!` to execute commands directly without AI translation:
```
🤖 user@host:~$ !ls -la
```

**Command history**: View your previous commands:
```
🤖 user@host:~$ history
```

**Built-in help**: Get assistance anytime:
```
🤖 user@host:~$ help
```

## 🏗️ Architecture

GPT-OS is built as a **userspace application** that sits on top of the standard Linux kernel. This means:

- ✅ **No kernel modification required** - Works with any Linux distribution
- ✅ **Easy to install and uninstall** - Just a Python application
- ✅ **Safe and isolated** - Doesn't affect your system's core functionality
- ✅ **Compatible** - Works alongside your existing shell (bash, zsh, etc.)

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                         User Input                          │
│              (Natural Language Command)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      GPT-OS Shell                           │
│  • Context gathering (current dir, OS info)                 │
│  • Safety checks                                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   OpenAI API (GPT-4)                        │
│  • Natural language understanding                           │
│  • Command generation                                       │
│  • Explanation generation                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Command Preview                           │
│  • Show generated command                                   │
│  • Display explanation                                      │
│  • Request user confirmation                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Execution                                │
│  • Run approved command                                     │
│  • Capture output                                           │
│  • Format results                                           │
└─────────────────────────────────────────────────────────────┘
```

## 🔒 Security Features

GPT-OS takes security seriously:

1. **Dangerous Command Detection**: Automatically identifies commands that could harm your system:
   - File deletion (`rm -rf`)
   - Disk formatting (`mkfs`, `fdisk`)
   - System shutdown/reboot
   - Process termination (`kill -9`)
   - And more...

2. **Mandatory Confirmation**: All commands require explicit user approval before execution

3. **Command Preview**: You always see exactly what will be executed

4. **Timeout Protection**: Commands automatically terminate after 30 seconds to prevent runaway processes

5. **No Automatic Execution**: Unlike some AI assistants, GPT-OS never executes commands without your permission

## 🌍 Multi-Language Support

GPT-OS is designed to work with multiple languages and accents. The underlying GPT model understands:

- English (all dialects: US, UK, Australian, etc.)
- Spanish
- French
- German
- Chinese
- Arabic
- And many more...

Simply type your commands in your preferred language!

## 🛠️ Configuration

### Using Different AI Models

By default, GPT-OS uses `gpt-4.1-mini` for fast, cost-effective responses. You can modify the model in `gpt_shell.py`:

```python
response = self.client.chat.completions.create(
    model="gpt-4.1-mini",  # Change this to gpt-4, gpt-4.1-nano, etc.
    ...
)
```

### Customizing the System Prompt

The system prompt in `gpt_shell.py` can be customized to change how the AI interprets commands. This is useful for:
- Adding domain-specific knowledge
- Changing the response format
- Adding custom safety rules

## 📊 Comparison with Existing Solutions

| Feature | GPT-OS | Traditional Shell | Other AI Shells |
|---------|--------|------------------|-----------------|
| Natural Language | ✅ Full support | ❌ No | ✅ Limited |
| Command Explanation | ✅ Always | ❌ No | ⚠️ Sometimes |
| Safety Confirmation | ✅ Required | ❌ No | ⚠️ Optional |
| Multi-language | ✅ Yes | ❌ No | ⚠️ Limited |
| Offline Mode | ❌ No (requires API) | ✅ Yes | ⚠️ Varies |
| Learning Curve | ✅ None | ❌ Steep | ⚠️ Moderate |
| Full Shell Replacement | ✅ Yes | N/A | ❌ No (CLI tools) |

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Report Bugs**: Open an issue describing the problem
2. **Suggest Features**: Share your ideas for improvements
3. **Submit Pull Requests**: Fix bugs or add features
4. **Improve Documentation**: Help make the docs better
5. **Share Examples**: Add more natural language command examples

### Development Setup

```bash
git clone https://github.com/hunix/gpt-os.git
cd gpt-os
pip3 install --user openai
python3 gpt_shell.py
```

## 📝 Roadmap

### Version 1.0 (Current)
- ✅ Natural language command translation
- ✅ Safety features and confirmations
- ✅ Command history
- ✅ Multi-language support

### Version 2.0 (Planned)
- 🔄 Voice input support (speech-to-text)
- 🔄 Voice output (text-to-speech responses)
- 🔄 Offline mode with local LLM (Ollama integration)
- 🔄 Learning from user corrections
- 🔄 Custom command aliases

### Version 3.0 (Future)
- 🔮 GUI interface option
- 🔮 System troubleshooting assistant
- 🔮 Complex workflow automation
- 🔮 Plugin system for extensions
- 🔮 Custom Linux distribution (GPT-OS ISO)

## 🐛 Troubleshooting

### "OpenAI API key not found"
Make sure you've set the environment variable:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

### "Command timed out"
Some commands take longer than 30 seconds. You can modify the timeout in `gpt_shell.py`:
```python
result = subprocess.run(
    command,
    shell=True,
    capture_output=True,
    text=True,
    timeout=30  # Change this value
)
```

### "I couldn't understand that"
Try rephrasing your request or being more specific. You can also use `!` to execute direct commands:
```
🤖 user@host:~$ !your-command-here
```

## 📄 License

GPT-OS is released under the MIT License. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **OpenAI** for providing the GPT models that power natural language understanding
- **BuilderIO/ai-shell** for inspiration on CLI design
- The **Linux community** for creating an amazing open-source operating system
- All contributors and users who help improve GPT-OS

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/hunix/gpt-os/issues)
- **Discussions**: [GitHub Discussions](https://github.com/hunix/gpt-os/discussions)
- **Website**: [gptos.ai](https://gptos.ai)

## ⭐ Star Us!

If you find GPT-OS useful, please consider giving us a star on GitHub! It helps others discover the project.

---

**Made with ❤️ for the Linux community**

*Making Linux accessible to everyone, one natural language command at a time.*
