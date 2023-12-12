# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# User specific environment
if ! [[ "$PATH" =~ "$HOME/.local/bin:$HOME/bin:" ]]
then
    PATH="$HOME/.local/bin:$HOME/bin:$PATH"
fi
export PATH

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions
if [ -d ~/.bashrc.d ]; then
	for rc in ~/.bashrc.d/*; do
		if [ -f "$rc" ]; then
			. "$rc"
		fi
	done
fi

unset rc

export ORACLE_BASE=/opt/oracle/
export ORACLE_HOME=$ORACLE_BASE/product/19c/dbhome_1
export ORACLE_SID=ORCLCDB
export PATH=$ORACLE_HOME/bin:$PATH

export HISTFILESIZE=20000
export HISTSIZE=1000

export HISTCONTROL=erasedups:ignoredups:ignorespace

shopt -s histappend
export PROMPT_COMMAND="history -a; history -c; history -r; $PROMPT_COMMAND"

export VISUAL=vim
export EDITOR="$VISUAL"


source ~/.git-prompt.sh

#export GIT_PS1_SHOWDIRTYSTATE="true"
#export GIT_PS1_SHOWSTASHSTATE="true"
#export GIT_PS1_SHOWUNTRACKEDFILES="true"
#export GIT_PS1_SHOWUPSTREAM="auto"


k165='\e[38;5;165m'
k171='\e[38;5;171m'
k213='\e[38;5;213m'
k214='\e[38;5;214m'
k196='\e[38;5;196m'
k027='\e[38;5;027m'
krst='\e[0m'    # Text Reset

PS1="$k165\u$k171@$k213\h$k214[$k027\$(__git_ps1 \"(%s) \")$k214\w]$krst\\$ "

alias tmux='tmux -2'

function colorgrid( )
{
    iter=16
    while [ $iter -lt 52 ]
    do
        second=$[$iter+36]
        third=$[$second+36]
        four=$[$third+36]
        five=$[$four+36]
        six=$[$five+36]
        seven=$[$six+36]
        if [ $seven -gt 250 ];then seven=$[$seven-251]; fi

        echo -en "\033[38;5;$(echo $iter)m█ "
        printf "%03d" $iter
        echo -en "   \033[38;5;$(echo $second)m█ "
        printf "%03d" $second
        echo -en "   \033[38;5;$(echo $third)m█ "
        printf "%03d" $third
        echo -en "   \033[38;5;$(echo $four)m█ "
        printf "%03d" $four
        echo -en "   \033[38;5;$(echo $five)m█ "
        printf "%03d" $five
        echo -en "   \033[38;5;$(echo $six)m█ "
        printf "%03d" $six
        echo -en "   \033[38;5;$(echo $seven)m█ "
        printf "%03d" $seven

        iter=$[$iter+1]
        printf '\r\n'
    done
}
