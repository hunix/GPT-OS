#!/usr/bin/env python3
"""
GPT-OS: AI-Powered Natural Language Shell
A revolutionary shell that understands natural language and executes Linux commands
"""

import os
import sys
import subprocess
import json
import re
from typing import Optional, Tuple
from openai import OpenAI

class GPTShell:
    def __init__(self):
        """Initialize the GPT Shell with OpenAI client"""
        self.client = OpenAI()
        self.history = []
        self.current_dir = os.getcwd()
        self.username = os.getenv('USER', 'user')
        self.hostname = os.uname().nodename
        
        # Dangerous commands that require confirmation
        self.dangerous_commands = [
            'rm -rf', 'mkfs', 'dd', 'format', 'fdisk',
            'shutdown', 'reboot', 'init 0', 'init 6',
            'kill -9', 'killall', ':(){:|:&};:', # fork bomb
        ]
        
        # System prompt for the LLM
        self.system_prompt = """You are GPT-OS, an intelligent Linux shell assistant. Your role is to:

1. Translate natural language requests into precise Linux shell commands
2. Provide clear explanations of what the command does
3. Warn about potentially dangerous operations
4. Support multiple languages and accents
5. Be conversational and helpful

When responding, use this JSON format:
{
    "command": "the actual shell command to execute",
    "explanation": "human-friendly explanation of what this does",
    "warning": "warning message if dangerous, otherwise null",
    "safe": true/false
}

Examples:
- "update my software" → {"command": "sudo apt update && sudo apt upgrade -y", "explanation": "This updates your package lists and upgrades all installed packages", "warning": null, "safe": true}
- "delete everything in this folder" → {"command": "rm -rf *", "explanation": "This permanently deletes all files and folders in the current directory", "warning": "⚠️ This is DESTRUCTIVE and cannot be undone!", "safe": false}
- "show me large files" → {"command": "du -ah . | sort -rh | head -20", "explanation": "This shows the 20 largest files and folders in the current directory", "warning": null, "safe": true}

Always respond ONLY with valid JSON. No additional text."""

    def print_banner(self):
        """Display the GPT-OS welcome banner"""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                         GPT-OS v1.0                           ║
║          AI-Powered Natural Language Linux Shell              ║
║                                                               ║
║  Speak naturally, command powerfully!                         ║
║  Type 'help' for assistance, 'exit' to quit                   ║
╚═══════════════════════════════════════════════════════════════╝
"""
        print(banner)

    def get_prompt(self) -> str:
        """Generate the shell prompt"""
        cwd = os.getcwd()
        home = os.path.expanduser('~')
        if cwd.startswith(home):
            cwd = '~' + cwd[len(home):]
        return f"\n🤖 {self.username}@{self.hostname}:{cwd}$ "

    def parse_llm_response(self, response: str) -> Optional[dict]:
        """Parse the LLM JSON response"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return None
        except json.JSONDecodeError:
            return None

    def translate_to_command(self, user_input: str) -> Optional[dict]:
        """Translate natural language to shell command using LLM"""
        try:
            # Add context about current directory
            context = f"Current directory: {os.getcwd()}\n"
            context += f"Operating System: {os.uname().sysname}\n"
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": context + user_input}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            llm_output = response.choices[0].message.content
            return self.parse_llm_response(llm_output)
            
        except Exception as e:
            print(f"❌ Error communicating with AI: {str(e)}")
            return None

    def is_dangerous(self, command: str) -> bool:
        """Check if a command is potentially dangerous"""
        for dangerous in self.dangerous_commands:
            if dangerous in command.lower():
                return True
        return False

    def execute_command(self, command: str) -> Tuple[int, str, str]:
        """Execute a shell command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out after 30 seconds"
        except Exception as e:
            return -1, "", str(e)

    def handle_builtin_commands(self, user_input: str) -> bool:
        """Handle built-in shell commands"""
        user_input = user_input.strip().lower()
        
        if user_input in ['exit', 'quit', 'q']:
            print("\n👋 Thank you for using GPT-OS! Goodbye!\n")
            sys.exit(0)
        
        elif user_input in ['help', '?']:
            self.show_help()
            return True
        
        elif user_input == 'clear':
            os.system('clear')
            return True
        
        elif user_input == 'history':
            self.show_history()
            return True
        
        elif user_input.startswith('cd '):
            path = user_input[3:].strip()
            try:
                os.chdir(os.path.expanduser(path))
                self.current_dir = os.getcwd()
                print(f"📁 Changed directory to: {self.current_dir}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            return True
        
        return False

    def show_help(self):
        """Display help information"""
        help_text = """
╔═══════════════════════════════════════════════════════════════╗
║                        GPT-OS HELP                            ║
╚═══════════════════════════════════════════════════════════════╝

🗣️  Natural Language Commands:
   Just type what you want in plain English (or your language)!
   
   Examples:
   • "update my software"
   • "show me all PDF files"
   • "find large files taking up space"
   • "check my disk usage"
   • "install python packages"
   • "compress this folder"

🔧 Built-in Commands:
   • help     - Show this help message
   • history  - Show command history
   • clear    - Clear the screen
   • exit     - Exit GPT-OS

💡 Tips:
   • Be specific about what you want to do
   • You can use your local accent and dialect
   • The AI will explain each command before executing
   • Dangerous commands require confirmation

🔒 Safety:
   • All commands are shown before execution
   • Dangerous operations require your approval
   • You can always cancel with Ctrl+C
"""
        print(help_text)

    def show_history(self):
        """Display command history"""
        if not self.history:
            print("📜 No command history yet.")
            return
        
        print("\n📜 Command History:")
        print("─" * 70)
        for i, entry in enumerate(self.history, 1):
            print(f"{i}. {entry['input']}")
            print(f"   → {entry['command']}")
            print()

    def format_output(self, stdout: str, stderr: str, exit_code: int):
        """Format command output for display"""
        if exit_code == 0:
            if stdout.strip():
                print("\n✅ Output:")
                print("─" * 70)
                print(stdout)
        else:
            print(f"\n❌ Command failed with exit code {exit_code}")
            if stderr.strip():
                print("Error details:")
                print("─" * 70)
                print(stderr)

    def run(self):
        """Main shell loop"""
        self.print_banner()
        
        while True:
            try:
                # Get user input
                user_input = input(self.get_prompt()).strip()
                
                if not user_input:
                    continue
                
                # Handle built-in commands
                if self.handle_builtin_commands(user_input):
                    continue
                
                # Check if it's a direct command (starts with !)
                if user_input.startswith('!'):
                    command = user_input[1:].strip()
                    print(f"\n🔧 Executing: {command}")
                    exit_code, stdout, stderr = self.execute_command(command)
                    self.format_output(stdout, stderr, exit_code)
                    continue
                
                # Translate natural language to command
                print("\n🤔 Thinking...")
                result = self.translate_to_command(user_input)
                
                if not result:
                    print("❌ Sorry, I couldn't understand that. Try rephrasing or use '!' for direct commands.")
                    continue
                
                command = result.get('command', '')
                explanation = result.get('explanation', '')
                warning = result.get('warning')
                safe = result.get('safe', True)
                
                # Display the command and explanation
                print("\n💡 I understand! Here's what I'll do:")
                print("─" * 70)
                print(f"Command: {command}")
                print(f"Explanation: {explanation}")
                
                if warning:
                    print(f"\n{warning}")
                
                # Ask for confirmation
                if not safe or self.is_dangerous(command):
                    confirm = input("\n⚠️  This command may be dangerous. Execute? (yes/no): ").strip().lower()
                    if confirm not in ['yes', 'y']:
                        print("❌ Command cancelled.")
                        continue
                else:
                    confirm = input("\n▶️  Execute this command? (yes/no): ").strip().lower()
                    if confirm not in ['yes', 'y']:
                        print("❌ Command cancelled.")
                        continue
                
                # Execute the command
                print(f"\n⚙️  Executing...")
                exit_code, stdout, stderr = self.execute_command(command)
                
                # Store in history
                self.history.append({
                    'input': user_input,
                    'command': command,
                    'exit_code': exit_code
                })
                
                # Display output
                self.format_output(stdout, stderr, exit_code)
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted. Type 'exit' to quit.")
                continue
            except EOFError:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {str(e)}")
                continue

def main():
    """Entry point for GPT-OS shell"""
    shell = GPTShell()
    shell.run()

if __name__ == "__main__":
    main()
