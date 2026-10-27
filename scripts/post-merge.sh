#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

python -m compileall -q app.py simulation.py advanced_agent.py sms_notifications.py
python -m unittest discover -s tests -v
