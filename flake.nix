{
  description = "LCA Protocol - Lifecycle Architecture for Claude Code autonomous agents";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devenv.url = "github:cachix/devenv";
  };

  outputs = { self, nixpkgs, devenv, ... }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      # Devenv module for importing into projects
      devenvModules.default = ./devenv-module.nix;
      devenvModules.lca = ./devenv-module.nix;

      # Expose the module's source files for reference
      lib = {
        agents = ./agents;
        hooks = ./hooks;
        skills = ./skills;
        templates = ./templates;
      };

      # Development shell for working on lca-protocol itself
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            buildInputs = with pkgs; [
              python3
              jq
            ];
          };
        }
      );
    };
}
