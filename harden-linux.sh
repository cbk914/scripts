#!/bin/bash
# Author: cbk914
#!/bin/bash

# Update the package repository
apt-get update -y

# Install and configure the firewall (ufw)
apt-get install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp # allow incoming SSH traffic
ufw allow 80/tcp # allow incoming HTTP traffic
ufw allow 443/tcp # allow incoming HTTPS traffic
ufw enable

# Disable root login via SSH
sed -i 's/PermitRootLogin yes/PermitRootLogin no/g' /etc/ssh/sshd_config
systemctl restart ssh

# Remove unnecessary packages and services
apt-get remove -y telnet
apt-get remove -y rsh-server
apt-get remove -y rsh-client
apt-get remove -y xinetd
apt-get remove -y tftp
apt-get remove -y tftpd
apt-get remove -y talk
apt-get remove -y talkd

# Enable automatic security updates
apt-get install -y unattended-upgrades
dpkg-reconfigure --priority=low unattended-upgrades

# Remove old software packages and clean up the package cache
apt-get autoremove -y
apt-get clean -y

# Set a strong password policy
echo "password  requisite      pam_cracklib.so retry=3 minlen=12 difok=3 reject_username minclass=3 maxrepeat=2 ucredit=-1 lcredit=-1 dcredit=-1 ocredit=-1" >> /etc/pam.d/common-password
echo "password  required      pam_pwquality.so try_first_pass local_users_only retry=3 enforce_for_root" >> /etc/pam.d/common-password

# Enable audit logging
apt-get install -y auditd
auditctl -e 1

# Disable core dumps
echo "* hard core 0" >> /etc/security/limits.conf

# Log the contents of the /etc/passwd, /etc/shadow, and /etc/group files
chmod 600 /etc/passwd
chmod 600 /etc/shadow
chmod 600 /etc/group

# Log all successful and unsuccessful login attempts
echo "auth required pam_tally2.so onerr=fail audit silent deny=5 unlock_time=900" >> /etc/pam.d/common-auth
echo "auth [default=die] pam_faillock.so authfail deny=5 unlock_time=900" >> /etc/pam.d/common-auth
echo "account required pam_tally2.so" >> /etc/pam.d/common-account
sed -i 's/.*LogLevel.*/LogLevel VERBOSE/' /etc/ssh/sshd_config

# Enable process accounting
apt-get install -y acct
systemctl enable acct

# Install and configure intrusion detection (fail2ban)
apt-get install -y fail2ban
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sed -i 's/bantime\s=\s600/bantime = 3600/g' /etc/fail2ban/jail.local
sed -i 's/findtime\s=\s600/findtime = 3600/g' /etc/fail2ban/jail.local
systemctl restart fail2ban

# Configure SSH to use key-based authentication
sed -i 's/.*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/.*ChallengeResponseAuthentication.*/ChallengeResponseAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh

# Disable unnecessary network protocols and services
apt-get remove -y nfs-common
apt-get remove -y rpcbind

# Disable IPv6
echo "net.ipv6.conf.all.disable_ipv6 = 1" >> /etc/sysctl.conf
echo "net.ipv6.conf.default.disable_ipv6 = 1" >> /etc/sysctl.conf
echo "net.ipv6.conf.lo.disable_ipv6 = 1" >> /etc/sysctl.conf
sysctl -p

# Disable ICMP Redirect Acceptance
echo "net.ipv4.conf.all.accept_redirects = 0" >> /etc/sysctl.conf
echo "net.ipv4.conf.default.accept_redirects = 0" >> /etc/sysctl.conf
sysctl -p

# Disable source packet routing
echo "net.ipv4.conf.all.accept_source_route = 0" >> /etc/sysctl.conf
echo "net.ipv4.conf.default.accept_source_route = 0" >> /etc/sysctl.conf
sysctl -p

# Enable TCP SYN Cookie Protection
echo "net.ipv4.tcp_syncookies = 1" >> /etc/sysctl.conf
sysctl -p

# Enable IP Spoofing Protection
echo "nospoof on" >> /etc/host.conf

# Enable DoS Protection
echo "* hard nproc 50" >> /etc/security/limits.conf
echo "* hard core 0" >> /etc/security/limits.conf

# Restrict access to /boot/grub/grub.cfg
chmod 600 /boot/grub/grub.cfg

# Set the correct permissions on SSH host keys
chmod 600 /etc/ssh/ssh_host_*
chmod 644 /etc/ssh/ssh_host_*.pub

# Enable Kernel Module Loading Protection
echo "install cramfs /bin/true" >> /etc/modprobe.d/CIS.conf
echo "install freevxfs /bin/true" >> /etc/modprobe.d/CIS.conf
echo "install jffs2 /bin/true" >> /etc/modprobe.d/CIS.conf
echo "install hfs /bin/true" >> /etc/modprobe.d/CIS.conf
echo "install hfsplus /bin/true" >> /etc/modprobe.d/CIS.conf
echo "install squashfs /bin/true" >> /etc/modprobe.d/CIS.conf
echo "install udf /bin/true" >> /etc/modprobe.d/CIS.conf
echo "install vfat /bin/true" >> /etc/modprobe.d/CIS.conf
/sbin/modprobe -n -v cramfs | grep "install /bin/true" || echo "install cramfs /bin/true" >> /etc/modprobe.d/CIS.conf
/sbin/modprobe -n -v freevxfs | grep "install /bin/true" || echo "install freevxfs /bin/true" >> /etc/modprobe.d/CIS.conf
/sbin/modprobe -n -v jffs2 | grep "install /bin/true" || echo "install jffs2 /bin/true" >> /etc/modprobe.d/CIS.conf
/sbin/modprobe -n -v hfs | grep "install /bin/true" || echo "install hfs /bin/true" >> /etc/modprobe.d/CIS.conf
/sbin/modprobe -n -v hfsplus | grep "install /bin/true" || echo "install hfsplus /bin/true" >> /etc/modprobe.d/CIS.conf
/sbin/modprobe -n -v squashfs | grep "install /bin/true" || echo "install squashfs /bin/true" >> /etc/modprobe.d/CIS.conf
/sbin/modprobe -n -v udf | grep "install /bin/true" || echo "install udf /bin/true" >> /etc/modprobe.d/CIS.conf
/sbin/modprobe -n -v vfat | grep "install /bin/true" || echo "install vfat /bin/true" >> /etc/modprobe.d/CIS.conf
/sbin/modprobe -n -v dccp | grep "install /bin/true" || echo "install dccp /bin/true" >> /etc/modprobe.d/CIS.conf
/sbin/modprobe -n -v sctp | grep "install /bin/true" || echo "install sctp /bin/true" >> /etc/modprobe.d/CIS.conf
/sbin/modprobe -n -v rds | grep "install /bin/true" || echo "install rds /bin/true" >> /etc/modprobe.d/CIS.conf
/sbin/modprobe -n -v tipc | grep "install /bin/true" || echo "install tipc /bin/true" >> /etc/modprobe.d/CIS.conf
/sbin/modprobe -n -v usb-storage | grep "install /bin/true" || echo "install usb-storage /bin/true" >> /etc/modprobe.d/CIS.conf

# Restrict access to the su command
dpkg-statoverride --update --add root sudo 4750 /bin/su

# Restrict access to system log files
chmod -R g-w,o-rwx /var/log

# Set a password for the root account
passwd -l root

# Set umask to 027
echo "umask 027" >> /etc/profile

# Update the motd banner
cat << EOF > /etc/motd
*******************************************************************
* This system is for the use of authorized users only.            *
* Individuals using this computer system without authority, or   *
* in excess of their authority, are subject to having all of      *
* their activities on this system monitored and recorded by      *
* system personnel.                                              *
*                                                              *
* In the course of monitoring individuals improperly using this *
* system, or in the course of system maintenance, the activities *
* of authorized users may also be monitored.                     *
*                                                              *
* Anyone using this system expressly consents to such monitoring *
* and is advised that if such monitoring reveals possible        *
* evidence of criminal activity, system personnel may provide   *
* the evidence of such monitoring to law enforcement officials.  *
*******************************************************************
EOF

# Reboot the system
reboot

