{ stdenv, makeWrapper, writeScript, elasticsearch, homePath }:

stdenv.mkDerivation rec {
  name = "es-local";
  unpackPhase = " ";
  configurePhase = " ";
  buildPhase = " ";
  checkPhase = " ";

  initLocalESHome = writeScript "init-local-es-home" ''
    #!/bin/bash

    mkdir -p ${homePath}/bin
    mkdir -p ${homePath}/data
    mkdir -p ${homePath}/logs

    test -e ${homePath}/config || (mkdir -p ${homePath}/config && install ${elasticsearch}/config/* ${homePath}/config)

    mkdir -p ${homePath}/config/scripts

    test -e ${homePath}/lib || ln -s ${elasticsearch}/lib ${homePath}/lib
    test -e ${homePath}/modules || ln -s ${elasticsearch}/modules ${homePath}/modules
    test -e ${homePath}/plugins || ln -s ${elasticsearch}/plugins ${homePath}/plugins
  '';

  buildInputs = [ makeWrapper ];

  installPhase = ''
    install -D ${elasticsearch}/bin/elasticsearch $out/bin/elasticsearch
    wrapProgram $out/bin/elasticsearch \
      --set ES_HOME ${homePath}
    ln -s $initLocalESHome $out/bin/init-local-es-home
  '';
}
