#!/bin/sh

echo 'eval "$(starship init bash)"' >> ~/.bashrc
mkdir -p ~/.config
cp .devcontainer/starship.toml ~/.config