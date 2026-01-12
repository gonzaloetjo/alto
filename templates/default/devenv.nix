{ inputs, pkgs, ... }:
{
  imports = [ inputs.alto.devenvModules.default ];

  alto.enable = true;

  # Uncomment to include domain skills (api-design, frontend, etc.)
  # alto.includeSpawnerSkills = true;

  # Add your project packages here
  # packages = with pkgs; [ python3 nodejs ];
}
