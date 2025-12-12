#!/bin/sh
set -e

script_dir=$(dirname "$(readlink -f "$0")")

if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)'
then
  # installed python is at least 3.10
  python_exec=python3
else
  # for earlier default, we force 3.10
  python_exec=python3.10
fi

${python_exec} -m venv venv

pip_execs=$(find venv/ -name "pip3*")
pip_exec=$(echo "${pip_execs}" | head -n 1)

${pip_exec} install --upgrade pip
${pip_exec} install --upgrade setuptools
${pip_exec} install --upgrade wheel

requirement_file="requirements.txt"
if [ -e "${requirement_file}" ]
then
  ${pip_exec} install --upgrade --requirement "${requirement_file}"
fi
