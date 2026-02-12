#!/bin/bash
# vliw_audit.sh
{
  echo "--- Environment Audit ---"
  echo "Date: $(date)"
  echo "User: $(whoami)"
  echo "Path: $PATH"
  echo "Jules: $(which jules)"
  echo "Jules Version: $(jules version 2>&1)"
  echo "Git Status: $(git status)"
  echo "Files: $(ls -la)"
  echo "--- End Audit ---"
} > audit_report.txt
echo "[AUDIT] report generated in audit_report.txt"
