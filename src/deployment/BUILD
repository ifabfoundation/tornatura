# Dependencies and source files
files(
  name="compose-files",
  sources=[
    "docker-compose-dev.yml",
  ],
  dependencies=[],
)

system_binary(
  name="docker",
  binary_name="docker",
)

run_shell_command(
    name="dev",
    command="docker compose -f docker-compose-dev.yml up -d",
    execution_dependencies=[":compose-files"],
)
