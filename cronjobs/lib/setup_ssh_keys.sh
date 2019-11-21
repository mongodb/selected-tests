#!/usr/bin/env bash

setup_ssh_keys() {
  local target_dir=$1

  if [ ! -d "$target_dir" ]; then
    mkdir "$target_dir"
    chmod 600 "$target_dir"
  fi

  # Make sure we have the right keys for github.
  ssh-keyscan -t rsa github.com >> "$target_dir/known_hosts"

  cat > "$target_dir/id_rsa" <<END_OF_PRIVATE
$GITHUB_PRIVATE_KEY
END_OF_PRIVATE
  chmod 600 $target_dir/id_rsa

  cat > "$target_dir/id_rsa.pub" <<END_OF_PUBLIC
$GITHUB_PUBLIC_KEY
END_OF_PUBLIC
}
