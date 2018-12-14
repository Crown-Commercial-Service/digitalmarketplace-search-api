argsOuter@{...}:
let
  # specifying args defaults in this slightly non-standard way to allow us to include the default values in `args`
  args = rec {
    pkgs = import <nixpkgs> {};
    pythonPackages = pkgs.python36Packages;
    forDev = true;
    localOverridesPath = ./local.nix;
    withLocalES = true;
  } // argsOuter;
in (with args; {
  digitalMarketplaceApiEnv = (pkgs.stdenv.mkDerivation rec {
    name = "digitalmarketplace-search-api-env";
    shortName = "dm-search-api";
    buildInputs = [
      pythonPackages.python
      pkgs.libffi
      pkgs.libyaml
      # pip requires git to fetch some of its dependencies
      pkgs.git
      # for `cryptography`
      pkgs.openssl
      pkgs.cacert
    ] ++ pkgs.stdenv.lib.optionals forDev [
      # exotic things possibly go here
    ] ++ pkgs.stdenv.lib.optionals withLocalES [
      ((import ./es.nix) (with pkgs; {
        inherit stdenv makeWrapper writeScript;
        elasticsearch = elasticsearch5;
        homePath = (toString (./.)) + "/local_es_home";
      }))
    ];

    hardeningDisable = pkgs.stdenv.lib.optionals pkgs.stdenv.isDarwin [ "format" ];

    GIT_SSL_CAINFO="${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
    VIRTUALENV_ROOT = (toString (./.)) + "/venv${pythonPackages.python.pythonVersion}";
    VIRTUAL_ENV_DISABLE_PROMPT = "1";
    SOURCE_DATE_EPOCH = "315532800";

    # if we don't have this, we get unicode troubles in a --pure nix-shell
    LANG="en_GB.UTF-8";

    shellHook = ''
      export PS1="\[\e[0;36m\](nix-shell\[\e[0m\]:\[\e[0;36m\]${shortName})\[\e[0;32m\]\u@\h\[\e[0m\]:\[\e[0m\]\[\e[0;36m\]\w\[\e[0m\]\$ "

      if [ ! -e $VIRTUALENV_ROOT ]; then
        ${pythonPackages.python}/bin/python -m venv $VIRTUALENV_ROOT
      fi
      source $VIRTUALENV_ROOT/bin/activate
      make -C ${(./.)} requirements${pkgs.stdenv.lib.optionalString forDev "-dev"}
    '' + pkgs.stdenv.lib.optionalString withLocalES ''
      init-local-es-home
    '';
  }).overrideAttrs (if builtins.pathExists localOverridesPath then (import localOverridesPath args) else (x: x));
})
