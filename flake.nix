{
  description = "Machine Learning for Digital Verification";

  outputs = { self, nixpkgs }: let
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
  in {
    devShells.x86_64-linux.default = pkgs.mkShell {
        packages = with pkgs; [
          zlib
          verilator
          python311
          python311Packages.cocotb
          python311Packages.pyzmq
          # Python Code Quality Tools
          python311Packages.flake8
          python311Packages.mypy
        ];
    };
  };
}
