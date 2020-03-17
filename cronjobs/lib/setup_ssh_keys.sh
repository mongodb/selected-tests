#!/usr/bin/env bash

setup_ssh_keys() {
  local target_dir=$1

  if [ ! -d "$target_dir" ]; then
    mkdir "$target_dir"
    chmod 600 "$target_dir"
  fi

  if [ -d "$target_dir/selected_tests" ]; then
    echo "$target_dir/selected_tests already exists"
    exit 1
  fi

  # Make sure we have the right keys for github.
  ssh-keyscan -t rsa github.com >> "$target_dir/known_hosts"

  cat > "$target_dir/selected_tests" <<END_OF_PRIVATE
$GITHUB_PRIVATE_KEY
END_OF_PRIVATE
  chmod 600 $target_dir/selected_tests

  cat > "$target_dir/selected_tests.pub" <<END_OF_PUBLIC
$GITHUB_PUBLIC_KEY
END_OF_PUBLIC

  eval "$(ssh-agent -s)"
  ssh-add -k $target_dir/selected_tests
}
