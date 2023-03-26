{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-21.11";
  };

  outputs = { self, nixpkgs }:
    let
      pkgs = import nixpkgs {
        system = "aarch64-darwin";
      };
    in
      {
        devShell = pkgs.mkShell {
          buildInputs = [
            pkgs.python311
          ];
        };
      };
}