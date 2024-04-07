#!/bin/sh

hatch config set dirs.env.virtual .hatch
echo 'eval "$(starship init bash)"' >> ~/.bashrc
mkdir -p ~/.config
cp .devcontainer/starship.toml ~/.config