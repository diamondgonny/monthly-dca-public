#!/bin/bash

current_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
files=("ExecPrep.py" "ExecNH.py" "ExecToFillPurple.py" "ExecKI.py" "ExecToFillRed.py")
python_interpreter="/usr/local/bin/python3"
log_path="log"
mkdir -p "$log_path"

# Iterate through the files and execute them
for file in "${files[@]}"; do
    full_path="$current_dir/$file"
    file_without_extension="${file%.py}"
    log_file="$current_dir/$log_path/$file_without_extension.log"
    [ -e "$log_file" ] || touch "$log_file"

    echo "Executing $file..."
    "$python_interpreter" "$full_path" 2>&1 | tee "$log_file"
    echo "Executed : $file"
    echo "Log file : $log_file"
    echo ""
    echo "------------------------------------------------------"
    echo ""
done

echo "Done."
