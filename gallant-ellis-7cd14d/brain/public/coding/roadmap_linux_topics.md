# Linux Command Line — Topic Index + Quick Reference

> Sumber: roadmap.sh/linux (CC BY-SA 4.0)
> Referensi: https://roadmap.sh/linux

## Linux Fundamentals

### Filesystem Hierarchy Standard (FHS)
```
/           root of the filesystem
├── bin/    essential binaries (ls, cp, bash) → symlink to /usr/bin in modern distros
├── boot/   bootloader files, kernel
├── dev/    device files (block, char devices)
├── etc/    system configuration files
├── home/   user home directories (/home/fahmi)
├── lib/    shared libraries → symlink to /usr/lib
├── media/  mount points for removable media
├── mnt/    temporary mount points
├── opt/    optional/third-party software
├── proc/   virtual fs — kernel/process info (/proc/cpuinfo, /proc/meminfo)
├── root/   root user's home directory
├── run/    runtime data (PIDs, sockets)
├── srv/    data for services (web, ftp)
├── sys/    virtual fs — hardware/driver info
├── tmp/    temporary files (cleared on reboot)
├── usr/    user programs (bin, lib, share, local)
└── var/    variable data (logs, spool, cache)
```

### File Permissions
```
-rwxr-xr--  1  fahmi  staff  4096  Apr 17  file.py
│└──┴──┴──    │  │      │
│  │  │  │    │  owner  group
│  │  │  └── other (r--)
│  │  └───── group (r-x)
│  └──────── owner (rwx)
└─────────── type: - file, d dir, l symlink, c char, b block

r=4, w=2, x=1
rwxr-xr-- = 754
rw-r--r-- = 644 (common for files)
rwxr-xr-x = 755 (common for dirs/executables)

chmod 755 script.sh         # numeric
chmod u+x script.sh         # add execute for user
chmod go-w file             # remove write for group + other
chmod -R 644 dir/           # recursive

chown fahmi:staff file.py   # change owner:group
chown -R fahmi ./project/
sudo chown root /etc/config
```

## Essential Commands

### Navigation
```bash
pwd                         # print working directory
ls                          # list files
ls -la                      # long format, show hidden
ls -lh                      # human-readable sizes
ls -lt                      # sort by modification time
cd /path/to/dir
cd ~                        # home directory
cd -                        # previous directory
cd ..                       # parent directory
```

### File Operations
```bash
# Create
touch file.txt              # create empty file / update timestamp
mkdir dirname               # create directory
mkdir -p a/b/c              # create nested dirs

# Copy / Move / Delete
cp file.txt dest/
cp -r dir/ dest/            # recursive copy
mv file.txt newname.txt     # rename or move
rm file.txt
rm -rf dir/                 # recursive force delete (DANGEROUS)
rmdir empty_dir             # remove empty directory

# View files
cat file.txt                # print entire file
less file.txt               # paginated view (q to quit)
head -n 20 file.txt         # first 20 lines
tail -n 20 file.txt         # last 20 lines
tail -f app.log             # follow live log
wc -l file.txt              # line count
wc -w file.txt              # word count

# Find files
find /path -name "*.py"
find . -name "*.log" -mtime +7   # older than 7 days
find . -size +100M               # larger than 100MB
find . -type d -name __pycache__ # directories named __pycache__
find . -name "*.py" -exec rm {} \;  # delete found files

# Links
ln -s /path/to/target linkname   # symbolic link
ln file.txt hardlink.txt          # hard link
```

### Text Processing
```bash
# grep — search text
grep "pattern" file.txt
grep -r "pattern" ./dir/         # recursive
grep -i "pattern" file.txt       # case-insensitive
grep -n "pattern" file.txt       # show line numbers
grep -v "pattern" file.txt       # invert (non-matching lines)
grep -l "pattern" *.txt          # list files with match
grep -E "regex|pattern" file     # extended regex
grep -c "error" app.log          # count matches

# sed — stream editor
sed 's/old/new/' file.txt        # replace first occurrence per line
sed 's/old/new/g' file.txt       # replace all occurrences
sed -i 's/old/new/g' file.txt    # in-place edit
sed -n '10,20p' file.txt         # print lines 10-20
sed '/pattern/d' file.txt        # delete matching lines

# awk — field processing
awk '{print $1}' file.txt        # print first field
awk -F: '{print $1}' /etc/passwd # colon-delimited, print field 1
awk '{sum += $1} END {print sum}' data.txt  # sum a column
awk 'NR>=10 && NR<=20' file.txt  # lines 10-20

# sort, uniq, cut
sort file.txt                    # alphabetical sort
sort -n numbers.txt              # numeric sort
sort -r file.txt                 # reverse sort
sort -k2 data.txt                # sort by field 2
sort file.txt | uniq             # remove duplicate lines
sort file.txt | uniq -c          # count duplicates
cut -d',' -f1,3 data.csv         # cut fields 1 and 3 (comma delimiter)
cut -c1-10 file.txt              # cut characters 1-10

# tr — translate/delete characters
tr 'a-z' 'A-Z' < file.txt       # uppercase
tr -d '\r' < windows.txt         # remove carriage returns
tr -s ' '                        # squeeze multiple spaces into one

# xargs — build command from stdin
find . -name "*.log" | xargs rm  # delete all .log files
find . -name "*.py" | xargs grep "import"
echo "file1 file2" | xargs -n1 echo   # one argument per line
```

### Pipes and Redirection
```bash
# Redirect stdout
command > file.txt          # overwrite
command >> file.txt         # append

# Redirect stderr
command 2> errors.txt
command 2>> errors.txt

# Redirect both
command > out.txt 2>&1      # stdout and stderr to file
command &> out.txt          # same (bash shorthand)

# Discard output
command > /dev/null 2>&1

# stdin redirect
command < input.txt

# Pipe: stdout → stdin
ls -la | grep ".py"
cat app.log | grep ERROR | tail -20
ps aux | grep python | awk '{print $2}'  # get PIDs

# tee: write to file AND stdout
command | tee output.txt
command | tee -a output.txt  # append
```

## Process Management

```bash
ps aux                      # all processes (all users, BSD format)
ps -ef                      # all processes (full format)
ps aux | grep python        # find Python processes
pgrep -f "brain_qa"         # find PID by pattern
pgrep -l python             # list matching processes + names

# Job control
Ctrl+C                      # interrupt (SIGINT)
Ctrl+Z                      # suspend (SIGTSTP)
jobs                        # list background jobs
bg %1                       # resume job 1 in background
fg %1                       # bring job 1 to foreground
command &                   # run in background

# Kill processes
kill PID                    # send SIGTERM (graceful)
kill -9 PID                 # send SIGKILL (force)
kill -HUP PID               # reload config (SIGHUP)
killall python              # kill all processes named python
pkill -f "brain_qa"         # kill by pattern

# Process priority
nice -n 10 command          # run with lower priority (10)
renice 10 -p PID            # change priority of running process
# nice value: -20 (high priority) to 19 (low priority)

# Monitor processes
top                         # live process monitor
htop                        # better top (if installed)
watch -n 2 'ps aux | grep python'  # run command every 2s

# Background daemons
nohup command &             # run immune to hangup, redirect to nohup.out
nohup python -m brain_qa serve > brain.log 2>&1 &
echo $!                     # PID of last background command
```

## System Information

```bash
# Hardware
uname -a                    # kernel info
lscpu                       # CPU info
lsmem                       # memory info
free -h                     # memory usage (human-readable)
df -h                       # disk usage by filesystem
df -h /                     # disk usage for root filesystem
du -sh dir/                 # directory size
du -sh *                    # size of each item in current dir
lsblk                       # block device list
lspci                       # PCI devices
lsusb                       # USB devices

# Network
ip addr                     # network interfaces and IPs (modern)
ip route                    # routing table
ss -tuln                    # listening ports (modern netstat)
ss -tunp                    # with process names
netstat -tuln               # older equivalent
curl -I https://example.com # HTTP headers
wget -q -O - https://example.com/file.txt  # download
ping -c 4 google.com        # ping 4 times
traceroute google.com       # trace route
nslookup example.com        # DNS lookup
dig example.com             # detailed DNS lookup
```

## Package Management

```bash
# Debian/Ubuntu (apt)
sudo apt update             # update package index
sudo apt upgrade            # upgrade installed packages
sudo apt install package    # install
sudo apt remove package     # remove (keep config)
sudo apt purge package      # remove + config files
sudo apt autoremove         # remove orphaned packages
apt search keyword          # search packages
apt show package            # package details
dpkg -l | grep package      # list installed packages matching name

# RHEL/CentOS/Fedora (dnf/yum)
sudo dnf update
sudo dnf install package
sudo dnf remove package
sudo dnf search keyword

# Python (pip)
pip install package
pip install -r requirements.txt
pip list
pip show package
pip freeze > requirements.txt
```

## Shell Scripting

```bash
#!/bin/bash
# Shebang line — use bash explicitly

# Variables
NAME="SIDIX"
VERSION=1
echo "$NAME version $VERSION"
readonly PI=3.14159          # constant

# String operations
echo "${NAME,,}"             # lowercase
echo "${NAME^^}"             # uppercase
echo "${NAME:0:3}"           # substring (0, length 3)
echo "${#NAME}"              # string length
echo "${NAME/SIDIX/Brain}"   # replace

# Arithmetic
echo $((3 + 4))
COUNT=$((COUNT + 1))
let COUNT+=1

# Conditionals
if [[ -f file.txt ]]; then
    echo "file exists"
elif [[ -d dirname ]]; then
    echo "is a directory"
else
    echo "neither"
fi

# File tests
[[ -f path ]]   # is regular file
[[ -d path ]]   # is directory
[[ -e path ]]   # exists
[[ -r path ]]   # readable
[[ -w path ]]   # writable
[[ -x path ]]   # executable
[[ -s path ]]   # non-empty file
[[ -z "$var" ]] # string is empty
[[ -n "$var" ]] # string is non-empty
[[ "$a" == "$b" ]] # string equality
[[ "$a" != "$b" ]]
[[ $n -eq $m ]] # numeric equality: -eq -ne -lt -le -gt -ge

# Loops
for file in *.py; do
    echo "Processing: $file"
done

for i in {1..10}; do
    echo "Step $i"
done

for i in $(seq 1 5); do
    echo "$i"
done

while [[ $COUNT -lt 10 ]]; do
    echo "$COUNT"
    ((COUNT++))
done

# Arrays
SERVERS=("web1" "web2" "web3")
echo "${SERVERS[0]}"         # first element
echo "${SERVERS[@]}"         # all elements
echo "${#SERVERS[@]}"        # length
for srv in "${SERVERS[@]}"; do
    echo "Checking $srv"
done

# Functions
greet() {
    local name="$1"          # local variable
    echo "Hello, $name!"
    return 0
}
greet "Fahmi"
echo "Exit code: $?"         # $? = last exit code

# Error handling
set -e                       # exit on error
set -u                       # error on undefined variable
set -o pipefail              # pipe fails if any command fails
set -euo pipefail            # combine (use at script top)

trap 'echo "Error on line $LINENO"' ERR
trap 'cleanup' EXIT          # run cleanup on exit

cleanup() {
    rm -f /tmp/tempfile
}
```

## systemd — Service Management

```bash
# Service control
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
sudo systemctl reload nginx      # reload config without restart
sudo systemctl status nginx
sudo systemctl enable nginx      # start on boot
sudo systemctl disable nginx
sudo systemctl is-active nginx
sudo systemctl is-enabled nginx

# View logs
journalctl -u nginx              # logs for nginx unit
journalctl -u nginx -f           # follow
journalctl -u nginx --since "1 hour ago"
journalctl -u nginx -n 50        # last 50 lines
journalctl -p err                # only errors

# Create service unit
# /etc/systemd/system/brain-qa.service
[Unit]
Description=SIDIX Brain QA Server
After=network.target

[Service]
Type=simple
User=fahmi
WorkingDirectory=/home/fahmi/MIGHAN-Model/apps/brain_qa
ExecStart=/home/fahmi/MIGHAN-Model/apps/brain_qa/.venv/bin/python -m brain_qa serve
Restart=on-failure
RestartSec=5
Environment=BRAIN_QA_MODEL_MODE=local_lora

[Install]
WantedBy=multi-user.target

# After creating/modifying unit file:
sudo systemctl daemon-reload
sudo systemctl enable brain-qa
sudo systemctl start brain-qa
```

## SSH

```bash
ssh user@host               # connect
ssh -p 2222 user@host       # custom port
ssh -i ~/.ssh/mykey user@host  # specific key
ssh -L 8080:localhost:80 user@host  # local port forward
ssh -R 8080:localhost:80 user@host  # remote port forward

# SSH key management
ssh-keygen -t ed25519 -C "fahmiwol@gmail.com"  # generate key
ssh-copy-id user@host       # copy public key to server
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys  # manual

# SSH config (~/.ssh/config)
Host myserver
    HostName 192.168.1.100
    User fahmi
    IdentityFile ~/.ssh/mykey
    Port 22

ssh myserver               # connect using config alias

# SCP / rsync
scp file.txt user@host:/path/
scp -r dir/ user@host:/path/
rsync -avz --progress local/ user@host:/remote/  # sync (efficient)
rsync -avz --delete local/ user@host:/remote/    # sync + delete extra
```

## Environment Variables

```bash
printenv                    # list all env vars
printenv PATH
echo $HOME

export MY_VAR="value"       # set for current session + child processes
unset MY_VAR

# Persistent env vars
# ~/.bashrc or ~/.bash_profile or ~/.profile
echo 'export MY_VAR="value"' >> ~/.bashrc
source ~/.bashrc            # reload without restart
. ~/.bashrc                 # same

# .env file (not auto-loaded, use with set -a)
set -a; source .env; set +a  # load .env file into current shell
```

## Referensi Lanjut
- https://roadmap.sh/linux
- https://tldr.sh/ — simplified man pages
- https://explainshell.com/ — explain any shell command
- https://www.gnu.org/software/bash/manual/
- "The Linux Command Line" — William Shotts (free PDF)
