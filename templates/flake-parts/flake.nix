{
  description = "Project with ALTO orchestration (flake-parts pattern)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devenv.url = "github:cachix/devenv";
    flake-parts.url = "github:hercules-ci/flake-parts";
    alto.url = "github:gonzaloetjo/alto";
  };

  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [ inputs.devenv.flakeModule ];

      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];

      perSystem = { pkgs, ... }: {
        devenv.shells.default = {
          # Import ALTO module
          imports = [ inputs.alto.devenvModules.default ];

          alto.enable = true;

          # Uncomment to include domain skills
          # alto.includeSpawnerSkills = true;

          # Add your project packages here
          # packages = with pkgs; [ python3 nodejs ];
        };
      };
    };
}
