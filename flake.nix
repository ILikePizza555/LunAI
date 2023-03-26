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
            openai
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