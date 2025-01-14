#!/bin/bash

echo 'eval "$(starship init bash)"' >> ~/.bashrc
echo "alias ll='ls -alF'" >> ~/.bashrc
mkdir -p ~/.config
cp .devcontainer/starship.toml ~/.config

curl -LsSf https://astral.sh/uv/install.sh | sh
curl -LsSf https://astral.sh/ruff/install.sh | sh
source $HOME/.cargo/env
echo 'eval "$(uv generate-shell-completion bash)"' >> ~/.bashrc