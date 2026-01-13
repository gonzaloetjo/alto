{ pkgs, ... }:
{
  # ALTO is imported via devenv.yaml imports, just enable it
  alto.enable = true;

  # Uncomment to include domain skills (api-design, frontend, etc.)
  # alto.includeSpawnerSkills = true;

  # Add your project packages here
  # packages = with pkgs; [ python3 nodejs ];
}
