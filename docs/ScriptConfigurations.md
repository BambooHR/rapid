# Script Configurations

When we run scripts in rapid, there are a few key words that we can use to activate features
when running. We do this with comments or a file in the `${WORKSPACE}` directory called `rapid_config`.
We can use the following to configure these features:

## Flags set in Comments or Written in rapid_config file
- `__RAPID_ANALYZE_TESTS__` - This option is set as `__RAPID_ANALYZE_TESTS__:<directory to scan>`. When this is set, rapid will scan the directory specified, for
  Rapid annotations and details about the tests.
- `__RAPIDCI_FAILURE_THRESHOLD__` - This option is set as `__RAPIDCI_FAILURE_THRESHOLD__:<int>`. With this set, only when test failures count
  is greater than this number will the action_instance be marked as failed.
- `__RAPIDCI_PARAMETERS__` - This option is set as `__RAPIDCI_PARAMETERS__:<glob for file>`. This file will be parsed as `key`=`value` pairs.
  Any parameters will be passed to each subsequent action_instance as an Environment variable.
- `__RAPIDCI_REQUIRED__` - This option is set as `__RAPIDCI_REQUIRED__:<files from master separated by ;>`. Any file noted here, will be 
  downloaded as required before running this script. You can have multiple files defined in multiple lines, or separated by a `;` on the same
  line.
- `__RAPIDCI_RESULTS__` - This option is set as `__RAPIDCI_RESULTS__:[XUnit|Tap]?-[failures|failures_count]#<results files glob>?;...`
  This option tells the system where the test results are to be expected. If the files are not there, the action_instance will fail. The 
  initial string of `[XUnit|Tap]` is the type of the file. XUnit or tap format. The results will be parsed and sent back to the master.
  
  If the `-failures` option is added, then it will only record the failures and their stack traces.
  If the `-failures_count` option is added, it will record the stack traces of failures and subsequently gather only the counts of passed and failed.
- `__RAPIDCI_STATUSES__` - This option is set as `__RAPIDCI_STATUSES__:<EXIT CODE>:<STATUS STRING>`. When the process will exit with status
  `<EXIT_CODE>` then it will override the status to the `<STATUS_STRING>` meaning the status name. i.e. - `2:MERGECONFLICT` will when exit 
  of 2, it will override to MERGECONFLICT status.
- `__RAPIDCI_STATS__` - This option is set as `__RAPIDCI_STATS__:<filename>`. This file, or a file named `params.txt` found in `${WORKSPACE}`
  will be parsed via `key=<int value>`. You can record stats accordingly.      

