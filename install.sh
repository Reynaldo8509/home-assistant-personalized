#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
config_dir="${HA_CONFIG_DIR:-}"
if [[ -z "$config_dir" ]]; then echo "Set HA_CONFIG_DIR to the Home Assistant config directory." >&2; exit 2; fi
mkdir -p -- "$config_dir"
for file in configuration.yaml automations.yaml scripts.yaml scenes.yaml firetv_adb.py; do
  src="$repo_dir/config/$file"; [[ -f "$src" ]] || continue
  dst="$config_dir/$file"
  if [[ -e "$dst" && "${FORCE:-0}" != 1 ]]; then echo "Skip existing $file (set FORCE=1 to replace)"; continue; fi
  install -m 0644 -- "$src" "$dst"; echo "Installed $file"
done
if [[ ! -e "$config_dir/secrets.yaml" ]]; then install -m 0600 "$repo_dir/config/secrets.yaml.example" "$config_dir/secrets.yaml.example"; fi
echo "Review entity IDs, local secrets, ADB pairing and configuration before restarting Home Assistant."
