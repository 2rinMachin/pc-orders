{
  pkgs ? import <nixpkgs> { },
}:
pkgs.mkShell {
  packages = with pkgs; [
    awscli2
    nodejs
    (python313.withPackages (ps: with ps; [ pip ]))
  ];
}
