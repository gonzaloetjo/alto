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
      # Usage: imports = [ inputs.alto.devenvModules.default ];
      devenvModules.default = ./devenv-module.nix;
      devenvModules.alto = ./devenv-module.nix;

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
