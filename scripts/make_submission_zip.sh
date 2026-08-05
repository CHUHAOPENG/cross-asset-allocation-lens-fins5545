#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"
project_name="$(basename "${project_root}")"
project_parent="$(dirname "${project_root}")"
output_path="${1:-${project_parent}/${project_name}_submission.zip}"

if [[ -e "${output_path}" ]]; then
  echo "Refusing to overwrite existing archive: ${output_path}" >&2
  exit 1
fi

command -v zip >/dev/null
command -v unzip >/dev/null

(
  cd "${project_parent}"
  zip -rq "${output_path}" "${project_name}" \
    -x "${project_name}/.git/*" \
       "${project_name}/.venv/*" \
       "${project_name}/venv/*" \
       "${project_name}/*/__pycache__/*" \
       "${project_name}/__pycache__/*" \
       "${project_name}/*.pyc" \
       "${project_name}/*.pyo" \
       "${project_name}/*/.pytest_cache/*" \
       "${project_name}/.pytest_cache/*" \
       "${project_name}/*/.mypy_cache/*" \
       "${project_name}/*/.ruff_cache/*" \
       "${project_name}/.DS_Store" \
       "${project_name}/*/.DS_Store" \
       "${project_name}/._*" \
       "${project_name}/*/._*" \
       "${project_name}/__MACOSX/*" \
       "${project_name}/*/__MACOSX/*" \
       "${project_name}/.streamlit/secrets.toml" \
       "${project_name}/.env" \
       "${project_name}/*.zip"
)

unzip -t "${output_path}" >/dev/null
echo "Created and verified: ${output_path}"
