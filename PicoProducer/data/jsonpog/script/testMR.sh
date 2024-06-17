#!/bin/bash

NOCHANGED_FILES=()
ADDED_FILES=()
CHANGED_FILES=()
BAD_CHANGED_FILES=()
BROKEN_FILES=()

HEAD=$1  # path to the merge request
MASTER=$2  # path to the clean clone

echo -e "## Validation errors\n" >> ${SCHEMA_REPORT}
echo -e "## Summary of changes\n" >> ${CHANGE_REPORT}

STATUS=0

# make sure tee'ing commands doesn't hide exit status
set -o pipefail

function validate() {
    VALIDATION=$(correction validate --version 2 $1)
    if [[ $? -ne 0 ]]; then
        echo
        echo "######### VALIDATION ERROR in $1 #########"
        echo ${VALIDATION}
        echo "################################################"
        echo ${VALIDATION} >> ${SCHEMA_REPORT}
        BROKEN_FILES+=($1)
        STATUS=1
        return 1
    fi
    return 0
}

for i in $(find ${HEAD}/POG -name "*.json*"); do
    echo
    if [[ -s ${MASTER}/$i ]]; then
        # file already exists in master
        if cmp --silent ${MASTER}/$i $i; then
            echo "No changes in "$i" wrt cms-nanoAOD/jsonpog-integration.git. "
            NOCHANGED_FILES+=($i)
        else
            echo -e "\nThere are changes in $i wrt cms-nanoAOD/jsonpog-integration.git. "
            if validate $i; then
                script/compareFiles.py ${MASTER}/$i $i 2>&1 | tee -a ${CHANGE_REPORT}
                if [[ $? -ne 0 ]]; then
                    BAD_CHANGED_FILES+=($i)
                    STATUS=1
                else
                    CHANGED_FILES+=($i)
                fi
            fi
        fi
    else
        echo "New file found in $i"
        if validate $i; then
            echo "-------------- summary of new file -----------------------------------"
            echo -e "### New valid file was added: $i\n" >> ${CHANGE_REPORT}
            correction summary $i | tee -a ${CHANGE_REPORT}
            echo "----------------------------------------------------------------------------"
            ADDED_FILES+=($i)
        fi
    fi
done

function print_array {
  printf '`'
  local d='`, `'
  local f=${1-}
  if shift 1; then
    printf %s "$f" "${@/#/$d}"
  fi
  printf '`'
}

echo

echo -e "### Summary of changes\n" | tee -a ${SUMMARY_REPORT}

if (( ${#BAD_CHANGED_FILES[@]} )); then
    echo " * Files changed and schema OK but problems found with content, see \`${CHANGE_REPORT}\`: $(print_array ${BAD_CHANGED_FILES[@]})" | tee -a ${SUMMARY_REPORT}
fi
if (( ${#CHANGED_FILES[@]} )); then
    echo " * Files changed (tests passed), see \`${CHANGE_REPORT}\`: $(print_array ${CHANGED_FILES[@]})" | tee -a ${SUMMARY_REPORT}
else
    echo " * No existing file changed (that passed schema test)." | tee -a ${SUMMARY_REPORT}
fi

if (( ${#ADDED_FILES[@]} )); then
    echo " * Files added (schema test passed), see \`${CHANGE_REPORT}\`: $(print_array ${ADDED_FILES[@]})\n"
else
    echo " * No file added (that passed schema test)." | tee -a ${SUMMARY_REPORT}
fi

if (( ${#BROKEN_FILES[@]} )); then
    echo " * Broken files found (schema test failed), see \`${SCHEMA_REPORT}\`: $(print_array ${BROKEN_FILES[@]})" | tee -a ${SUMMARY_REPORT}
else
    echo " * No file fails schema test." | tee -a ${SUMMARY_REPORT}
fi

echo "Done."

exit ${STATUS}
