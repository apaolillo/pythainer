#!/bin/sh
set -e

script_dir=$(dirname "$(readlink -f "$0")")

python_exec=python3.10

${python_exec} -m venv venv

pip_execs=$(find venv/ -name "pip3*")
pip_exec=$(echo "${pip_execs}" | head -n 1)

${pip_exec} install --upgrade pip
${pip_exec} install --upgrade setuptools
${pip_exec} install --upgrade wheel
${pip_exec} install --upgrade pycodestyle isort pylint black black[d] black[jupyter] flake8 docopt

requirement_file="requirements.txt"
if [ -e "${requirement_file}" ]
then
  ${pip_exec} install --upgrade --requirement "${requirement_file}"
fi
