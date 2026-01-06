{
  config,
  lib,
  dream2nix,
  pkgs,
  ...
}: let
  pyproject = lib.importTOML (config.mkDerivation.src + /pyproject.toml);
in {
  
  imports = [
    dream2nix.modules.dream2nix.pip
  ];

  # package dependencies
  deps = {nixpkgs,... } : {
    python = nixpkgs.python3;
  };

  inherit (pyproject.project) name version;

  mkDerivation = {
    src = lib.cleanSourceWith {
      src = lib.cleanSource ./..;
      filter = name : type:
        !(builtins.any (x: x) [
          (lib.hasSuffix ".nix" name) # do not package nix files
          (lib.hasPrefix "." (builtins.baseNameOf name)) # do not package hidden files
          (lib.hasSuffix "flake.lock" name) # do not include the flake lock
        ]);
    };
  };

  buildPythonPackage = {
   pyproject = true; 
   pythonImportsCheck = [ # checks that python can import pythainer
    "pythainer" 
   ];
  };

  pip = {
    # concatenate both the build system (above) and the requirements.txt
    requirementsList =
      pyproject.build-system.requires or [] 
      ++  pyproject.project.dependencies or [];
    flattenDependencies = true;
  };

}
