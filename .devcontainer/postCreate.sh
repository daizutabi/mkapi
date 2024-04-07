#!/bin/sh

hatch config set dirs.env.virtual .hatch
# echo 'eval "$(starship init zsh)"' >> ~/.zshrc
echo 'eval "$(starship init bash)"' >> ~/.bashrc