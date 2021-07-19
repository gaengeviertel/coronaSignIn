{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python39.withPackages (ps: [ps.pipenv]) {}
  ];
}
