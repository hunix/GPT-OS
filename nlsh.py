import subprocess, os

WHITELIST_PATH = "config/whitelist.txt"

with open(WHITELIST_PATH, 'r') as f:
    whitelist = [line.strip() for line in f.readlines() if line.strip()]

def is_safe(cmd):
    return any(cmd.startswith(w) for w in whitelist)

def run(prompt):
    print("\n⏳ Thinking...")
    cmd = subprocess.getoutput(f"./llama.cpp/main -m models/model.gguf -p '{prompt}'")
    print(f"\n🤖 Suggested command:\n{cmd}")
    if not is_safe(cmd):
        print("\n❌ Command not whitelisted. Skipping.")
        return
    confirm = input("\nExecute? [y/N]: ").lower()
    if confirm == 'y':
        os.system(cmd)

if __name__ == '__main__':
    while True:
        try:
            prompt = input("\n🧠 GPT-OS:> ")
            run(prompt)
        except KeyboardInterrupt:
            print("\nExiting GPT-OS Shell")
            break
