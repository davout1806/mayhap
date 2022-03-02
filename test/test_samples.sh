#!/bin/sh
set -u
export PATH='/bin:/usr/bin:/usr/local/bin'

path=$(dirname "$(dirname "$0")")
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
	# TODO use the default production, run all productions, and/or add a
	# "validate" flag
	echo "$mayhap $sample origin"
	if ! "$mayhap" "$sample" origin; then
		failures=$((failures + 1))
	fi
	total=$((total + 1))
	echo
done < "$sample_list"
end_time=$(date +%s)
duration=$((end_time - start_time))

rm "$sample_list"

# Output made to mimic that of unittest
echo "Ran $total tests in ${duration}s"
echo
if [ $failures -gt 0 ]; then
	echo "FAILED (failures=$failures)"
else
	echo 'OK'
fi

exit 0
