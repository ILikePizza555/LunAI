{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-22.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
    let
        pkgs = import nixpkgs { inherit system; };
        python-packages = p: with p; [
            discordpy
            (buildPythonPackage rec {
                pname = "openai";
                version = "0.27.2";
                src = fetchPypi {
                    inherit pname version;
                    sha256 = "sha256-WGn9+jSw7GbDmvoi9KD7g6E13/gfZQX1KDTGqzET92I=";
                };
                doCheck = false;
                propagatedBuildInputs = [
                    p.wandb
                    p.requests
                    p.tqdm
                    p.typing-extensions
                    p.aiohttp
                ];
            })
        ];
        python-with-packages = pkgs.python310.withPackages python-packages;
    in
        {
            devShells.default = pkgs.mkShell {
                buildInputs = [
                    python-with-packages
                ];
            };
        }
    );
}