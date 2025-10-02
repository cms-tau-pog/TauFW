#alias sS='source ~/setup_Scripts/setup_SFrame.sh'
#alias cdB='cd ~/analysis/SFrameAnalysis/BatchSubmission' 
function stamp { trap 'echo -e "$(tput setaf 2; tput bold)[$(date +"%H:%M:%S %d/%m/%Y")]$(tput sgr0)"' DEBUG; }
tmux new session \;\
  split-window -v \;\
  send-keys "stamp" C-m \; \
  split-window -h \;\
  send-keys "stamp" C-m \; \
  select-pane -t 1

