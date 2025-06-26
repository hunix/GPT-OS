#!/bin/bash
sudo apt update && sudo apt install -y git cmake build-essential python3-pip python3-tk

echo "Cloning llama.cpp..."
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp && make && cd ..

pip3 install -r requirements.txt

mkdir -p models
mkdir -p config

echo "df -h\nfree -h\ntop\nwhoami\nls\nreboot" > config/whitelist.txt

echo "Setup complete. Place your model.gguf in models/"
