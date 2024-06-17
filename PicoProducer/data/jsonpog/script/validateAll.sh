#!/bin/bash

BROKEN_FILES=()

SOURCE=$1  # path to the root of the repository

STATUS=0

for i in $(find ${SOURCE}/POG -name "*.json*"); do
    # Validate files
    VALIDATION=$(correction validate --version 2 $i)
    if [[ ${?: -1} -ne 0 ]]; then
        echo
        echo "######### ERROR in "$i" #########"
        echo ${VALIDATION}
        echo "#################################################################"
        echo
        BROKEN_FILES+=($i)
        STATUS=1
    fi
done

if (( ${#BROKEN_FILES[@]} )); then
    echo "Broken files: ${BROKEN_FILES[@]}\n"
else
    echo "No broken files.\n"
fi

echo "Done."

exit ${STATUS}
