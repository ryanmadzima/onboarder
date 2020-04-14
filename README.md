# Onboarder

#### Quickly onboard a large amount of EX switches to the Mist cloud using a CSV file.

This script was tested using Python 3.8.1 and assumes existing SSH access and a super-user account that can apply a configuration.

CSV file example:
        
        ip,username,password
        192.168.0.2,super_user,MyPassw0rd!
        192.168.0.3,super_user,MyPassw0rd!
        
Usage:

```bash
./onboarder.py -h

usage: onboarder.py [-h] -t TOKEN -o ORG_ID -c CSV [-l {ERROR,WARNING,INFO,DEBUG}]

optional arguments:
  -h, --help            show this help message and exit
  -t TOKEN, --token TOKEN
                        Mist API token.
  -o ORG_ID, --org_id ORG_ID
                        Mist organization ID.
  -c CSV, --csv CSV     CSV file containing switches to be onboarded.
  -l {ERROR,WARNING,INFO,DEBUG}, --log_level {ERROR,WARNING,INFO,DEBUG}
                        Set the logging verbosity.

```

# License
[MIT](LICENSE)