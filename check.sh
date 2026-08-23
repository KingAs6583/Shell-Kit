#!/usr/bin/env bash
cd /d/Projects/shell-kit
for f in bash/.bashrc bash/.bash_function bash/.bash_profile scripts/history-clean.sh scripts/scan-packages.sh install.sh verify.sh dotfiles.sh; do
  bash -n "$f" && echo "OK: $f" || echo "FAIL: $f"
done
