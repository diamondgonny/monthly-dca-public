#!/bin/bash

current_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
file="PortfolioCalculator.py"
python_interpreter="/usr/local/bin/python3"
log_path="log"
mkdir -p "$log_path"
full_path="$current_dir/$file"
file_without_extension="${file%.py}"
log_file="$current_dir/$log_path/$file_without_extension.log"
[ -e "$log_file" ] || touch "$log_file"

# execute the file, print both in 'console' and 'log file'
echo "Executing $file..."
echo ""
"$python_interpreter" -u "$full_path" 2>&1 | tee "$log_file"
echo "-----------------------------------------------------------------------------------------"
echo ""
echo "Executed : $file"
echo "Log file : $log_file"
echo "Done."
echo ""
