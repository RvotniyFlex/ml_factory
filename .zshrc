
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/opt/anaconda3/bin/conda' 'shell.zsh' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/opt/anaconda3/etc/profile.d/conda.sh" ]; then
        . "/opt/anaconda3/etc/profile.d/conda.sh"
    else
        export PATH="/opt/anaconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<


# The next line updates PATH for CLI.
if [ -f '/Users/kekernikola/yandex-cloud/path.bash.inc' ]; then source '/Users/kekernikola/yandex-cloud/path.bash.inc'; fi

# The next line enables shell command completion for yc.
if [ -f '/Users/kekernikola/yandex-cloud/completion.zsh.inc' ]; then source '/Users/kekernikola/yandex-cloud/completion.zsh.inc'; fi

export PATH="/opt/homebrew/opt/openjdk@11/bin:$PATH"
export PATH="/Users/kekernikola/.local/bin:$PATH"

