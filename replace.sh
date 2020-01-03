#!/bin/bash

export FIND="$1"
export REPLACE="$2"
if [ -z "$3" ]; then
	ruby -p -e "gsub(ENV['FIND'], ENV['REPLACE'])"
else
	ruby -p -i -e "gsub(ENV['FIND'], ENV['REPLACE'])" $3
fi