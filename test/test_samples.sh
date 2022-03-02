#!/bin/sh
set -u
export PATH='/bin:/usr/bin:/usr/local/bin'

path=$(realpath "$(dirname "$0")/..")
mayhap="$path/mayhap.py"
samples="$path/samples"

failures=0
total=0

# Store sample files to a temporary file
# Redirecting find output to the while loop spawns a subshell, preventing
# variable reassignments
sample_list=$(mktemp -t 'mayhap_test_samples-XXX')
find "$samples" -type f -name '*.mh' > "$sample_list"

start_time=$(date +%s)
while read -r sample; do
	echo "$mayhap --test $sample"
	if ! "$mayhap" --test "$sample"; then
		failures=$((failures + 1))
	fi
	total=$((total + 1))
	echo
	echo '----------------------------------------------------------------------'
done < "$sample_list"
end_time=$(date +%s)
duration=$((end_time - start_time))

rm "$sample_list"

# Output made to mimic that of unittest
echo "Ran $total tests in ${duration}s"
echo
if [ $failures -gt 0 ]; then
	echo "FAILED (failures=$failures)"
	exit "$failures"
fi
echo 'OK'
exit 0
