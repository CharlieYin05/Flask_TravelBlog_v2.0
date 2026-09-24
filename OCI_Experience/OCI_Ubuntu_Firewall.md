# OCI Ubuntu 系统防火墙操作指南

本文用于记录 Oracle Cloud Infrastructure（OCI）Ubuntu 实例默认的 iptables 防火墙规则，以及如何开放指定端口。

## 说明
- OCI 提供的 Ubuntu 平台镜像预置了本机系统防火墙规则。
- 默认情况下，实例只允许 SSH（TCP 22）入站，同时包含 OCI 平台正常运行所需的规则。
- Oracle 官方不建议直接使用 UFW 修改 OCI Ubuntu 镜像的防火墙规则，因为 UFW 对规则的重新组织可能影响 OCI 预置规则，严重情况下可能导致实例无法正常启动。
- 因此，在修改防火墙之前，建议先查看系统现有的 iptables 规则，并在保留 OCI 默认规则的基础上添加需要开放的端口。

**注意：除了操作系统内部的 iptables，OCI 的 NSG（Network Security Group）或 Security List 也必须允许对应流量，否则外部仍然无法访问该端口。**

---

## 查看当前 iptables 规则：
`sudo iptables -L -n -v`

## 输出示例：
```
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)          ← 入站规则
 pkts bytes target     prot opt in     out     source               destination         
  12M 5490M ACCEPT     0    --  *      *       0.0.0.0/0            0.0.0.0/0            state RELATED,ESTABLISHED
4173K  282M ACCEPT     1    --  *      *       0.0.0.0/0            0.0.0.0/0           
 457K   47M ACCEPT     0    --  lo     *       0.0.0.0/0            0.0.0.0/0           
 486K   27M ACCEPT     6    --  *      *       0.0.0.0/0            0.0.0.0/0            state NEW tcp dpt:22
    0     0 ACCEPT     6    --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:4433 state NEW               ← 自己要开放的入站端口。要确保在 REJECT 规则上面
84561   21M REJECT     0    --  *      *       0.0.0.0/0            0.0.0.0/0            reject-with icmp-host-prohibited     ← 其它入站端口全部 REJECT

Chain FORWARD (policy ACCEPT 0 packets, 0 bytes)         ← 转发规则
 pkts bytes target     prot opt in     out     source               destination         
    0     0 REJECT     0    --  *      *       0.0.0.0/0            0.0.0.0/0            reject-with icmp-host-prohibited

Chain OUTPUT (policy ACCEPT 14M packets, 9961M bytes)    ← 出站规则
 pkts bytes target     prot opt in     out     source               destination         
2994K  244M InstanceServices  0    --  *      *       0.0.0.0/0            169.254.0.0/16      

Chain InstanceServices (1 references)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 ACCEPT     6    --  *      *       0.0.0.0/0            169.254.0.2          owner UID match 0 tcp dpt:3260 /* See the Oracle-Provided Images section in the Oracle Cloud Infrastructure documentation for security impact of modifying or removing this rule */
......
```

## 查看是否使用 netfilter-persistent
`dpkg -l | grep -E 'iptables-persistent|netfilter-persistent'`

## 如果用了，查看保存的永久规则
`cat /etc/iptables/rules.v4`

---

## 编辑永久规则

### 1.备份
sudo cp /etc/iptables/rules.v4 /etc/iptables/rules.v4.bak

### 2.编辑
`sudo nano /etc/iptables/rules.v4`

### 3.开放指定 TCP 端口例子
```
-A INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT
-A INPUT -p tcp -m state --state NEW -m tcp --dport 4433 -j ACCEPT        ← 在 REJECT 之前添加要开放的端口规则
-A INPUT -j REJECT --reject-with icmp-host-prohibited
```

### 4.重新加载
`sudo netfilter-persistent reload`

### 5.检查
`sudo iptables -L INPUT -n -v --line-numbers`        ← 开放的端口是否生效
`sudo ss -lntp`                                      ← 开放的端口是否被监听

--- 

## 注意事项

不要直接清空 OCI Ubuntu 镜像现有的防火墙规则，例如：

`sudo iptables -F`

不然会把自己锁在外面（亲测）。
