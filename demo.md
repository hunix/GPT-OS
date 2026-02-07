# GPT-OS Demo Guide

This guide demonstrates the capabilities of GPT-OS with example interactions.

## Starting GPT-OS

```bash
./gpt-os
```

You'll see the welcome banner:

```
╔═══════════════════════════════════════════════════════════════╗
║                         GPT-OS v1.0                           ║
║          AI-Powered Natural Language Linux Shell              ║
║                                                               ║
║  Speak naturally, command powerfully!                         ║
║  Type 'help' for assistance, 'exit' to quit                   ║
╚═══════════════════════════════════════════════════════════════╝

🤖 user@host:~$
```

## Example Interactions

### 1. System Updates

**User Input:**
```
update my software
```

**GPT-OS Response:**
```
🤔 Thinking...

💡 I understand! Here's what I'll do:
──────────────────────────────────────────────────────────────────
Command: sudo apt update && sudo apt upgrade -y
Explanation: This updates your package lists and upgrades all installed packages to their latest versions

▶️  Execute this command? (yes/no):
```

### 2. Finding Files

**User Input:**
```
show me all PDF files in this folder
```

**GPT-OS Response:**
```
🤔 Thinking...

💡 I understand! Here's what I'll do:
──────────────────────────────────────────────────────────────────
Command: find . -name "*.pdf" -type f
Explanation: This searches the current directory and all subdirectories for files with the .pdf extension

▶️  Execute this command? (yes/no):
```

### 3. Disk Space Check

**User Input:**
```
how much disk space do I have left?
```

**GPT-OS Response:**
```
🤔 Thinking...

💡 I understand! Here's what I'll do:
──────────────────────────────────────────────────────────────────
Command: df -h
Explanation: This displays disk space usage in human-readable format, showing available space on all mounted filesystems

▶️  Execute this command? (yes/no):
```

### 4. Finding Large Files

**User Input:**
```
find the largest files taking up space
```

**GPT-OS Response:**
```
🤔 Thinking...

💡 I understand! Here's what I'll do:
──────────────────────────────────────────────────────────────────
Command: du -ah . | sort -rh | head -20
Explanation: This shows the 20 largest files and directories in the current location, sorted by size

▶️  Execute this command? (yes/no):
```

### 5. Dangerous Command Warning

**User Input:**
```
delete all files in this folder
```

**GPT-OS Response:**
```
🤔 Thinking...

💡 I understand! Here's what I'll do:
──────────────────────────────────────────────────────────────────
Command: rm -rf *
Explanation: This permanently deletes all files and folders in the current directory

⚠️ This is DESTRUCTIVE and cannot be undone! All data will be permanently lost.

⚠️  This command may be dangerous. Execute? (yes/no):
```

### 6. Process Management

**User Input:**
```
show me what programs are running
```

**GPT-OS Response:**
```
🤔 Thinking...

💡 I understand! Here's what I'll do:
──────────────────────────────────────────────────────────────────
Command: ps aux --sort=-%mem | head -20
Explanation: This displays the top 20 running processes sorted by memory usage, showing details like CPU and memory consumption

▶️  Execute this command? (yes/no):
```

### 7. Network Information

**User Input:**
```
what's my IP address?
```

**GPT-OS Response:**
```
🤔 Thinking...

💡 I understand! Here's what I'll do:
──────────────────────────────────────────────────────────────────
Command: curl -s ifconfig.me
Explanation: This retrieves your public IP address from an external service

▶️  Execute this command? (yes/no):
```

### 8. File Compression

**User Input:**
```
compress this folder into a zip file
```

**GPT-OS Response:**
```
🤔 Thinking...

💡 I understand! Here's what I'll do:
──────────────────────────────────────────────────────────────────
Command: tar -czf archive.tar.gz .
Explanation: This creates a compressed archive of the current directory and all its contents

▶️  Execute this command? (yes/no):
```

## Built-in Commands

### Help Command

**User Input:**
```
help
```

**Response:**
```
╔═══════════════════════════════════════════════════════════════╗
║                        GPT-OS HELP                            ║
╚═══════════════════════════════════════════════════════════════╝

🗣️  Natural Language Commands:
   Just type what you want in plain English (or your language)!
   
   Examples:
   • "update my software"
   • "show me all PDF files"
   • "find large files taking up space"
   ...
```

### History Command

**User Input:**
```
history
```

**Response:**
```
📜 Command History:
──────────────────────────────────────────────────────────────────
1. update my software
   → sudo apt update && sudo apt upgrade -y

2. show me all PDF files
   → find . -name "*.pdf" -type f

3. how much disk space do I have left?
   → df -h
```

### Direct Command Execution

**User Input:**
```
!ls -la
```

**Response:**
```
🔧 Executing: ls -la

✅ Output:
──────────────────────────────────────────────────────────────────
total 48
drwxr-xr-x  3 user user 4096 Feb  8 12:00 .
drwxr-xr-x 25 user user 4096 Feb  8 11:30 ..
-rw-r--r--  1 user user 1234 Feb  8 12:00 README.md
...
```

## Multi-Language Support

GPT-OS understands commands in multiple languages:

### Spanish Example
```
🤖 user@host:~$ actualizar mi sistema
```

### French Example
```
🤖 user@host:~$ montrer tous les fichiers PDF
```

### Arabic Example
```
🤖 user@host:~$ حدث البرامج
```

## Safety Features

GPT-OS includes multiple safety features:

1. **Command Preview**: Always shows what will be executed
2. **Explanation**: Provides clear explanation of each command
3. **Confirmation**: Requires user approval before execution
4. **Danger Detection**: Identifies potentially harmful commands
5. **Enhanced Warnings**: Extra warnings for destructive operations

## Tips for Best Results

1. **Be specific**: The more specific your request, the better the result
2. **Use natural language**: Don't try to sound technical
3. **Include context**: Mention file types, locations, or specific requirements
4. **Review before confirming**: Always check the generated command
5. **Use direct mode**: Prefix with `!` for commands you already know

## Exiting GPT-OS

**User Input:**
```
exit
```

**Response:**
```
👋 Thank you for using GPT-OS! Goodbye!
```

---

**Note**: This demo assumes you have set up your OpenAI API key. See the README for setup instructions.
