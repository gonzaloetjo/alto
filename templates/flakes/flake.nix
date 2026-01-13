{
  description = "Project with ALTO orchestration (flakes pattern)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devenv.url = "github:cachix/devenv";
    alto.url = "github:gonzaloetjo/alto";
  };

  outputs = { self, nixpkgs, devenv, alto, ... }@inputs:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    in
    {
      devShells = forAllSystems (system: {
        default = devenv.lib.mkShell {
          inherit inputs;
          pkgs = nixpkgs.legacyPackages.${system};
          modules = [
            # Import ALTO module
            alto.devenvModules.default

            # Project configuration
            ({ pkgs, ... }: {
              alto.enable = true;

              # Uncomment to include domain skills
              # alto.includeSpawnerSkills = true;

              # Add your project packages here
              # packages = with pkgs; [ python3 nodejs ];
            })
          ];
        };
      });
    };
}
