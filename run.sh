#!/bin/bash

CNT_FAIL=0
CNT_COMP=0
CNT_SUCCESS=0
CNT_FAIL_PATCH=0
TIMEOUT=$((15*60))
RAMLIMIT=$((2*1024*1024))

fail()
{
	CNT_FAIL=$(($CNT_FAIL + 1))
	echo -e "\e[41m=============== $@ ===================\e[0m" 1>&2
	return 1
}

failc()
{
	CNT_COMP=$(($CNT_COMP + 1))
	#CNT_SUCCESS=$(($CNT_SUCCESS + 1))
	echo -e "\e[44m=============== $@ ===================\e[0m" 1>&2
	return 1
}

failm()
{
	CNT_FAIL_PATCH=$(($CNT_FAIL_PATCH + 1))
	echo -e "\e[45m=============== $@ ===================\e[0m" 1>&2
	return 1
}

success()
{
	CNT_SUCCESS=$(($CNT_SUCCESS + 1))
	echo -e "\e[42m================ SUCCESS ===============\e[0m"
}

cnt=0
for tmp in $(seq 1 300)
do
	if [ $(($cnt - $CNT_FAIL_PATCH)) -gt 0 ]; then
		echo "SCORE $((100 * $CNT_SUCCESS / ($cnt - $CNT_FAIL_PATCH - $CNT_FAIL_COMP)))%   ($CNT_SUCCESS / $cnt - $CNT_FAIL_PATCH - $CNT_FAIL_COMP)"
	fi
	cnt=$(($cnt+1))
	$(dirname $0)/mutate.sh $1 > /dev/null || failm "Fail to patch" || continue
	git --no-pager diff
	# > /dev/null
	#git diff
	make -j4 &> /dev/null || failc "Fail to compile" ||  continue
	#cargo +nightly build &> /dev/null || failc "Failed to compile" || continue
	ulimit -Sv ${RAMLIMIT}
	#if timeout ${TIMEOUT} ctest "$@" &> /dev/null; then
	#if timeout ${TIMEOUT} cargo +nightly test &> /dev/null; then
	#if timeout ${TIMEOUT} ctest -j4 &> /dev/null; then
	if timeout ${TIMEOUT} make run-fast-noreg-tests &> /dev/null; then
		fail "Fail to detect ($?)"
		continue
	fi
	success
	#find ./ -iname "Test*" -type f | grep -v ".cpp" | grep -v ".dir" | while read line; do $line || break; done; done
done

echo
echo
echo
echo "CNT_FAIL=$CNT_FAIL"
echo "CNT_COMP=$CNT_COMP"
echo "CNT_SUCCESS=$CNT_SUCCESS"
echo "CNT_FAIL_PATCH=$CNT_FAIL_PATCH"
echo
echo "Score : $((100 * $CNT_SUCCESS / ($cnt - $CNT_FAIL_PATCH - $CNT_FAIL_COMP)))%"
