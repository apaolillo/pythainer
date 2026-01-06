{
  description = "A pythonic toolkit for composing, managing, and deploying Docker images and containers. ";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    dream2nix.url = "github:nix-community/dream2nix";
  };

  outputs = {
    self,
      nixpkgs,
      dream2nix,
  }:
    let
      eachSystem = nixpkgs.lib.genAttrs [
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-darwin"
        "x86_64-linux"
      ];
    in {

      packages = eachSystem (system : {
        default = dream2nix.lib.evalModules {
          packageSets.nixpkgs = nixpkgs.legacyPackages.${system};
          modules = [
            .nix/default.nix
            {
              paths.lockFile = ".nix/lock.${system}.json";
              paths.projectRoot = ./.; 
              paths.projectRootFile = "flake.nix"; 
              paths.package = ./.;
            }
          ];
        };
      });


      devShells = eachSystem (system:
        let
          pkgs = nixpkgs.legacyPackages.${system}; # 
          pythainer = self.packages.${system}.default;
          python = pythainer.config.deps.python;
        in {
          default = pkgs.mkShell { # 
            inputsFrom = [pythainer.devShell]; # 
            packages = [
              pythainer
              python.pkgs.python-lsp-ruff
              python.pkgs.pip

              pkgs.ruff 
              pkgs.black
            ];
          };
        });
    };
}
