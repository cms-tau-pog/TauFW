#! /bin/bash
# Author: Izaak Neutelings (Februari 2021)
# Description: Some helpfunctions
# Instructions: source utils/tools.sh

function peval { # print and evaluate given command
  echo -e ">>> $(tput setab 0)$(tput setaf 7)$@$(tput sgr0)"
  eval "$@";
}

function header { # print box around given string
  local HDR="$@"
  local BAR=`printf '#%.0s' $(seq 1 ${#HDR})`
  printf "\n\n\n"
  echo ">>>     $(tput setab 0)$(tput setaf 7)####${BAR}####$(tput sgr0)"
  echo ">>>     $(tput setab 0)$(tput setaf 7)#   ${HDR}   #$(tput sgr0)"
  echo ">>>     $(tput setab 0)$(tput setaf 7)####${BAR}####$(tput sgr0)"
  echo ">>> ";
}

function ensureDir {
  [ -e "$1" ] || { echo ">>> making $1 directory..."; mkdir -p "$1"; }
}

function runtime {
  END=`date +%s`; RUNTIME=$((END-START))
  printf "%d minutes %d seconds" "$(( $RUNTIME / 60 ))" "$(( $RUNTIME % 60 ))"
}
