# OCI Ubuntu System Firewall Guide

This document records the default `iptables` firewall rules on Oracle Cloud Infrastructure (OCI) Ubuntu instances and explains how to open specific ports.

## Overview

* OCI-provided Ubuntu platform images come with preconfigured host-level firewall rules.
* By default, the instance only allows inbound SSH traffic on TCP port 22, while also including rules required for normal OCI platform operation.
* Oracle officially does not recommend directly using UFW to modify firewall rules on OCI Ubuntu images, because UFW may reorganize the rules and interfere with OCI-provided rules. In serious cases, this may prevent the instance from booting normally.
* Therefore, before modifying the firewall, it is recommended to review the existing `iptables` rules and add the required port rules while preserving OCI's default rules.

**Note: In addition to the operating system's internal `iptables` rules, the corresponding traffic must also be allowed in the OCI NSG (Network Security Group) or Security List. Otherwise, the port will still not be accessible externally.**

---

## View the Current iptables Rules

`sudo iptables -L -n -v`

## Example Output

```text
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)          ← Inbound rules
 pkts bytes target     prot opt in     out     source               destination
  12M 5490M ACCEPT     0    --  *      *       0.0.0.0/0            0.0.0.0/0            state RELATED,ESTABLISHED
4173K  282M ACCEPT     1    --  *      *       0.0.0.0/0            0.0.0.0/0
 457K   47M ACCEPT     0    --  lo     *       0.0.0.0/0            0.0.0.0/0
 486K   27M ACCEPT     6    --  *      *       0.0.0.0/0            0.0.0.0/0            state NEW tcp dpt:22
    0     0 ACCEPT     6    --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:4433 state NEW               ← Custom inbound port. Make sure this rule is placed above the REJECT rule
84561   21M REJECT     0    --  *      *       0.0.0.0/0            0.0.0.0/0            reject-with icmp-host-prohibited     ← Reject all other inbound ports

Chain FORWARD (policy ACCEPT 0 packets, 0 bytes)         ← Forwarding rules
 pkts bytes target     prot opt in     out     source               destination
    0     0 REJECT     0    --  *      *       0.0.0.0/0            0.0.0.0/0            reject-with icmp-host-prohibited

Chain OUTPUT (policy ACCEPT 14M packets, 9961M bytes)    ← Outbound rules
 pkts bytes target     prot opt in     out     source               destination
2994K  244M InstanceServices  0    --  *      *       0.0.0.0/0            169.254.0.0/16

Chain InstanceServices (1 references)
 pkts bytes target     prot opt in     out     source               destination
    0     0 ACCEPT     6    --  *      *       0.0.0.0/0            169.254.0.2          owner UID match 0 tcp dpt:3260 /* See the Oracle-Provided Images section in the Oracle Cloud Infrastructure documentation for security impact of modifying or removing this rule */
......
```

## Check Whether netfilter-persistent Is Being Used

`dpkg -l | grep -E 'iptables-persistent|netfilter-persistent'`

## If It Is Installed, View the Saved Persistent Rules

`cat /etc/iptables/rules.v4`

---

## Edit Persistent Rules

### 1. Back Up the Current Rules

`sudo cp /etc/iptables/rules.v4 /etc/iptables/rules.v4.bak`

### 2. Edit the Rules

`sudo nano /etc/iptables/rules.v4`

### 3. Example: Open a Specific TCP Port

```text
-A INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT
-A INPUT -p tcp -m state --state NEW -m tcp --dport 4433 -j ACCEPT        ← Add the port rule before the REJECT rule
-A INPUT -j REJECT --reject-with icmp-host-prohibited
```

### 4. Reload the Rules

`sudo netfilter-persistent reload`

### 5. Verify

`sudo iptables -L INPUT -n -v --line-numbers`        ← Check whether the firewall rule has taken effect

`sudo ss -lntp`                                      ← Check whether the port is being listened on

---

## Important Notes

Do not directly flush the existing firewall rules on an OCI Ubuntu image, for example:

`sudo iptables -F`

Otherwise, you may lock yourself out of the instance. (Happened in actual incident)
