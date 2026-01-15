{ pkgs, ... }:
{
  # ALTO is imported via devenv.yaml - active by default
  # Switch modes: alto.orchestrator = "setup" | "build" | "dev"

  # Uncomment to include domain skills (api-design, frontend, etc.)
  # alto.includeSpawnerSkills = true;

  # Add your project packages here
  # packages = with pkgs; [ python3 nodejs ];
}
