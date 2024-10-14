#!/bin/bash

echo 'eval "$(starship init bash)"' >> ~/.bashrc
echo "alias ll='ls -alF'" >> ~/.bashrc
mkdir -p ~/.config
cp .devcontainer/starship.toml ~/.config

curl --proto '=https' --tlsv1.2 -LsSf https://github.com/astral-sh/uv/releases/download/0.4.20/uv-installer.sh | sh
source $HOME/.cargo/env
echo 'eval "$(uv generate-shell-completion bash)"' >> ~/.bashrc