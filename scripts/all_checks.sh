#!/bin/sh
set -e

script_dir=$(readlink -e "$(dirname "$0")")
pythainer_root_dir=$(readlink -e "${script_dir}/..")
venv_dir=$(readlink -f "${pythainer_root_dir}/venv")

(
  cd "${pythainer_root_dir}"

  if [ ! -d "${venv_dir}" ]
  then
    echo "-- venv in root dir of pythainer not present. Creating one. --"
    ./scripts/install_venv.sh
    echo "-- venv created. --"
  fi

  pylint=$(readlink -f "${venv_dir}/bin/pylint")
  flake8=$(readlink -f "${venv_dir}/bin/flake8")
  isort=$(readlink -f "${venv_dir}/bin/isort")
  black=$(readlink -f "${venv_dir}/bin/black")

  echo "-- check copyright. --"
  ./scripts/list_missing_copyright.sh

  echo "-- running pylint. --"
  ${pylint} src/ || true

  echo "-- running flake8. --"
  ${flake8} src/ || true

  echo "-- running isort. --"
  ${isort} --profile=black src/

  echo "-- running black. --"
  ${black} -l 100 .
)
