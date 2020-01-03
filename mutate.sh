#!/bin/bash

#set -e
#set -x

TOOL_DIR=$(dirname $0)
SOURCE_DIR=$1
#cd $SOURCE_DIR

MODES="OR
INFS1
INFS2
INFS3
INFS4
INFEQ1
INFEQ2
INFEQ3
INFEQ4
SUPS1
SUPS2
SUPS3
SUPS4
SUPEQ1
SUPEQ2
SUPEQ3
SUPEQ4
NOTEQ1
NOTEQ2
NOTEQ3
NOTEQ4
NOTEQ5
NUM0
NUM1
NUM2
NUM3
NUM4
NUM5
NUM6
NUM7
NUM8
NUM9
STR"

NUMS="0
1
2
3
4
5
6
7
8
9"

get_files()
{
	#find $SOURCE_DIR/ -iname '*.rs' | grep -v test | grep -v main | xargs echo
	find $SOURCE_DIR/ | egrep '((\.c)|(\.h)|(\.cpp)|(\.hpp)|(\.rs)|(\.py))$' | grep -v .git | grep -v test | xargs readlink -f
}

filter_lines()
{
	grep -v assert | grep -v assume | grep -v DEBUG | egrep -v '^ * ' | egrep -v '//'
}

cat_all()
{
	#xargs cat
	filter_lines
}

line_protect()
{
	#TODO
	cat
}

extract_covered_lines()
{
	#get list of files
	get_files > lst.txt

	#loop in coverage
	filename=''
	cat out.info | while read line; do
		case $line in
			SF:*)
				filename=$(echo ${line} | cut -f 2- -d ':')
				if [ -z "$(egrep "^${filename}$" lst.txt)" ]; then
					#skip
					filename=''
				fi
				;;
			DA:*)
				if [ ! -z "${filename}" ]; then
					line_id=$(echo ${line} | cut -f 2 -d ':' | cut -f 1 -d ',')
					cat ${filename} | sed "${line_id}q;d"
				fi
				;;
			*)
				;;
		esac
	done
}

xtail_rust()
{
	while read line; do
		reach_test="false"
		tail -n +7 $line | while read wline; do
			if [ "${wline}" = "#[cfg(test)]" ]; then
				reach_test="true"
			elif [ "${reach_test}" = "false" ]; then
				echo "${wline}"
			fi
		done
	done
}

extract_lines()
{
	#extract_covered_lines 1>&2
	if [ -f out.info ]; then
		extract_covered_lines | select_line
	else
		#get_files | xargs tail -n +7 | select_line
		get_files | xtail_rust | select_line
	fi
}

select_line()
{
	case $mode in
		OR)
			cat_all | grep '||' | shuf -n 1
			;;
		INFS*)
			cat_all | grep ' < ' | shuf -n 1
			;;
		INFEQ*)
			cat_all | grep ' <= ' | shuf -n 1
			;;
		SUBS*)
			cat_all | grep ' > ' | shuf -n 1
			;;
		SUBEQ*)
			cat_all | grep ' >= ' | shuf -n 1
			;;
		NOTEQ*)
			cat_all | grep ' != ' | shuf -n 1
			;;
		NUM*)
			orig=$(echo $mode | sed -e 's/NUM//g')
			cat_all | grep "$orig" | shuf -n 1
			;;
		STR)
			cat_all | egrep '"[0-9A-Za-z_ -]+"' | shuf -n 1
			;;
	esac
}

mutate_line()
{
	case $mode in
		OR)
			sed -e 's/[|][|]/\&\&/g'
			;;
		INFS1)
			sed -e 's/ < / <= /g'
			;;
		INFS2)
			sed -e 's/ < / > /g'
			;;
		INFS3)
			sed -e 's/ < / >= /g'
			;;
		INFS4)
			sed -e 's/ < / == /g'
			;;
		INFS5)
			sed -e 's/ < / != /g'
			;;
		INFEQ1)
			sed -e 's/ <= / < /g'
			;;
		INFEQ2)
			sed -e 's/ <= / > /g'
			;;
		INFEQ3)
			sed -e 's/ <= / >= /g'
			;;
		INFEQ4)
			sed -e 's/ <= / == /g'
			;;
		INFEQ5)
			sed -e 's/ <= / != /g'
			;;
		SUPS1)
			sed -e 's/ > / <= /g'
			;;
		SUPS2)
			sed -e 's/ > / < /g'
			;;
		SUPS3)
			sed -e 's/ > / >= /g'
			;;
		SUPS4)
			sed -e 's/ > / = /g'
			;;
		SUPS5)
			sed -e 's/ > / != /g'
			;;
		SUPEQ1)
			sed -e 's/ >= / < /g'
			;;
		SUPEQ2)
			sed -e 's/ >= / > /g'
			;;
		SUPEQ3)
			sed -e 's/ >= / <= /g'
			;;
		SUPEQ4)
			sed -e 's/ >= / == /g'
			;;
		SUPEQ5)
			sed -e 's/ >= / != /g'
			;;
		NOTEQ1)
			sed -e 's/ != / == /g'
			;;
		NOTEQ1)
			sed -e 's/ != / == /g'
			;;
		NOTEQ2)
			sed -e 's/ != / > /g'
			;;
		NOTEQ3)
			sed -e 's/ != / < /g'
			;;
		NOTEQ4)
			sed -e 's/ != / >= /g'
			;;
		NOTEQ5)
			sed -e 's/ != / <= /g'
			;;
		NUM*)
			orig=$(echo $mode | sed -e 's/NUM//g')
			target=$(echo "$NUMS" | grep -v $orig | shuf -n 1)
			sed -e "s/${orig}/${target}/g"
			;;
		STR)
			set -x
			l=$(cat)
			instr="$(echo "$l" | egrep -o '"[0-9A-Za-z_ -]+"')"
			len=${#instr}
			plen=$(($len - 2))
			pos=$(( ($RANDOM % $plen) + 1 ))
			ppos=$(($pos+1))
			chr=$(dd if=/dev/urandom bs=10 count=1 2> /dev/null | base64)
			chr=${chr:0:1}
			outstr=${instr:0:pos}${chr}${instr:ppos}
			echo "$l" | $TOOL_DIR/replace.sh "$instr" "$outstr"
			;;
	esac
}

#reset
git reset --hard

line=""

while [ -z "$line" ]
do

mode=$(echo "$MODES" | shuf -n 1)
echo "Mode : $mode"

#get a line
line="$(extract_lines | line_protect)"

done

#mutage
repl="$(echo "$line" | mutate_line)"

#apply
for tmp in $(get_files)
do
	$TOOL_DIR/replace.sh "$line" "$repl" $tmp
done

if [ -z "$(git diff)" ]; then
	exit 1
fi

#check
git status
git --no-pager diff
