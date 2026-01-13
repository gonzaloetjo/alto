{
  description = "ALTO - Autonomous Lifecycle Task Orchestrator for Claude Code";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, ... }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      # Main export: devenv module for consumer projects
      #
      # Usage patterns:
      # 1. Native devenv (recommended):
      #    devenv.yaml: inputs.alto.url = github:cachix/alto, flake: false
      #    devenv.yaml: imports: [alto]
      #
      # 2. Flakes:
      #    modules = [ inputs.alto.devenvModules.default ];
      #
      # 3. Flake-parts:
      #    devenv.shells.default.imports = [ inputs.alto.devenvModules.default ];
      devenvModules.default = ./devenv.nix;
      devenvModules.alto = ./devenv.nix;

      # Templates for quick project setup
      templates = {
        # Native devenv (recommended) - no flake.nix needed
        # Usage: nix flake init -t github:gonzaloetjo/alto
        default = {
          path = ./templates/default;
          description = "ALTO with native devenv (recommended - no flake.nix needed)";
        };

        # Flakes pattern - for projects already using flakes
        # Usage: nix flake init -t github:gonzaloetjo/alto#flakes
        flakes = {
          path = ./templates/flakes;
          description = "ALTO with Nix flakes pattern";
        };

        # Flake-parts pattern - for flake-parts users
        # Usage: nix flake init -t github:gonzaloetjo/alto#flake-parts
        flake-parts = {
          path = ./templates/flake-parts;
          description = "ALTO with flake-parts pattern";
        };
      };

      # Dev shell for working on ALTO itself (not for consumers)
      devShells = forAllSystems (system: {
        default = nixpkgs.legacyPackages.${system}.mkShell {
          buildInputs = with nixpkgs.legacyPackages.${system}; [
            python3
            jq
          ];
        };
      });
    };
}
