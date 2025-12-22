{
  description = "A very basic flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
  };

  outputs = { self, nixpkgs, pyproject-nix, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system : 
      let 
        pkgs = import nixpkgs {inherit system;};

	      python = pkgs.python3;
	      pythonPackages = pkgs.python3Packages;
        project = pyproject-nix.lib.project.loadRequirementsTxt {
          projectRoot = ./.;
        };

        pythonEnv =
          # assert project.validators.validateVersionConstraints { inherit python; } == { };
          python.withPackages (ps:
            (project.renderers.withPackages { inherit python; } ps)
            ++ [ ps.pip ]   # useful for debugging
          );
      in
        {

          packages.pythainer = pythonPackages.buildPythonPackage {
            pname = "pythainer"; 
            version= "0.0.5";

            src = ./.;

            
            propagatedBuildInputs = [
              pythonEnv
            ];
            format = "pyproject";
  	        build-system = [ pythonPackages.hatchling ];
          };
          packages.default = self.packages.${system}.pythainer;

          devShells.default = pkgs.mkShell {
            packages = with pkgs; [
              self.packages.${system}.pythainer
            ];
          };
        }
    );
}
