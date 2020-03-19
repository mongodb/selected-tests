#!/usr/bin/env bash

target_file=$1

if [ -z "$GITHUB_PRIVATE_KEY" ]; then
  echo "GITHUB_PRIVATE_KEY unset"
  exit 1
fi

if [ -z "$GITHUB_PUBLIC_KEY" ]; then
  echo "GITHUB_PUBLIC_KEY unset"
  exit 1
fi

if [ ! -d "$HOME/.ssh" ]; then
    mkdir "$HOME/.ssh"
    chmod 600 "$HOME/.ssh"
  fi

if [ -f "$HOME/.ssh/$target_file" ]; then
  echo "$target_file already exists"
  exit 1
fi

# Make sure we have the right keys for github.
ssh-keyscan -t rsa github.com >> "$HOME/.ssh/known_hosts"

cat > "$HOME/.ssh/$target_file" <<END_OF_PRIVATE
$GITHUB_PRIVATE_KEY
END_OF_PRIVATE
chmod 600 "$HOME/.ssh/$target_file"

cat > "$HOME/.ssh/$target_file.pub" <<END_OF_PUBLIC
$GITHUB_PUBLIC_KEY
END_OF_PUBLIC

eval "$(ssh-agent -s)"
ssh-add -k "$HOME/.ssh/$target_file"
