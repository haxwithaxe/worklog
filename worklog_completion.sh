
_worklog(){
	local options

	case "${COMP_WORDS[1]}" in
		start)
			options="--ago --at --day --ticket"
			;;
		stop|resume)
			options="--ago --at --day"
			;;
		report|upload)
			options="--day"
			;;
		*)
			options="start stop resume report upload"
			;;
	esac

	COMPREPLY=( $( compgen -W "--help ${options}" -- "${COMP_WORDS[COMP_CWORD]}" ) )
}

complete -F _worklog worklog

