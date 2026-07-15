# 如何创建OCI免费服务器实例并部署项目网页

---

## 结构：
Internet → 公网 IP → OCI VCN → Public Subnet → Ubuntu Instance → Docker → Flask + Nginx + SQLite

---

## 创建服务器Build Instance

  ### 1.Basic inforamtion
    Name: 服务器名自己填（本案例：cy-server-Ora(x86)）
    Create in compartment: 默认自己的账号(root)
  
    Placement/Availbility domain: 取决于创建账号时选择的城市，固定城市后选择机房
    Placement/Advanced options: 选择服务器主机部署方案（本案例：默认选On-demand capacity（放在共享宿主机上））

    Image：按需选择系统（本案例：Canonical Ubuntu 24.04 Minimal）
    Shape：按钱包选择硬件配置（本案例：VM.Standard.E2.1.Micro 「Always Free-eligible」）
    Image and shape/Advanced options
      Instance metadata service: OCI 给实例提供的“内部信息接口”
      Require an authorization header：要求访问 metadata 时必须使用 IMDSv2，并带上认证 header。开了打开安全性高，关闭兼容性高（本案例：开）
      Initialization script：开机初始化脚本，例如开机自动执行·apt update·（本案例：跳过）
      
  ### 2.Security
    Shielded instance：开启增强启动安全的选项，启用Secure Boot、Measured Boot、TPM 组合来增强 VM。关闭兼容性好（本案例：关闭）
    Advanced options/Security attributes：给资源打安全标签，然后用 ZPR 策略控制哪些资源能互相访问。（本案例：不添加）

  ### 3.Networking
    Primary VNIC/VNIC name：虚拟网卡起名字（本案例：VNIC-FLask）
    
    Primary network：复用已有VCN虚拟网络或者创建新的VCN虚拟网络（本案例：复用vcn-2026XXXX-XXXX）
    
    subnet：复用已有的LAN或者创建新的LAN。注意出入站规则对该LAN内所有Instance生效。（本案例：Create new public subnet）
      New subnet name: 局域网起名字（本案例：subnet-Flask）
      Create in campartment: 默认自己的账号(root)
      CIDR block: 虚拟局域网网段范围，不能和同一个VCN下其他subnet有重复。（本案例：10.0.1.0/24）

    IPv4 address assignment: 跳过，等Subnet随着Instance一起创建后才能设置

    Add SSH keys: 选择SSH密钥方案。（本案例：Generate a key pair for me，然后Download private key，可选Download public key）

  ### 3.Boot volume
    Boot volume：系统盘大小与硬盘吞吐量（本案例：默认46.6G）
    Use in-transit encryption：Instance ↔ 存储之间的数据流量加密（本案例：关闭）
    Encrypt this volume with a key that you manage：自管硬盘加密密钥（本案例：关闭）
    Block volumes：额外挂载硬盘（本案例：不挂载）

  ### 4. Review
    检查配置，没有问题就创建服务器实例

---

## 设置网络和SSH

    ### 1.进入cy-server-Ora(x86)实例，点击Networking，查看是否有Public IPv4 Address

    ### 2.进入VNIC的IP administration，如果没有IPv4就添加一个，有就查看是Reserved还是Ephemeral并记住IP地址（本案例：有，是Ephemeral，地址为161.XX.XX.XX)

    ### 3.把下载的密钥放进~/.ssh

    ### 4.（可选）设置ssh config:
        Host server-agile
          HostName 161.XX.XX.XX
          User ubuntu
          IdentityFile ~/.ssh/ssh-key-2026-05-16.key
      
    ### 5.设置SSH密钥权限:
        ·chmod 600 ~/.ssh/ssh-key-2026-05-16.key·

    ### 6.SSH服务器：
        ·ssh server-agile`

---

## 测试控制台是否工作正常

    ### 1.SSH进入服务器后设置密码：
    ·sudo passwd ubuntu·

    ### 2.进入OS Management，点击Counsole connection
        账号：ubuntu
        密码：刚刚设置的
        
---

## 打开端口

    ### 1. 写subnet-Flask的入站规则
      开放HTTP 80端口：
          Souce CIDR: 0.0.0.0/0（所有IP全部可以进入）
          IP Protocal：TCP（进入协议是网页跑的TCP协议）
          Souce Port Range：留空（所有端口都可以进入）
          Destination Port Range：80（进入内部subnet 80端口）
          Description：HTTP connect
    
      开放HTTPS 443端口：
          Souce CIDR: 0.0.0.0/0（所有IP全部可以进入）
          IP Protocal：TCP（进入协议是网页跑的TCP协议）
          Souce Port Range：留空（所有端口都可以进入）
          Destination Port Range：443（进入内部subnet 443端口）
          Description：HTTPS connect

      开放反向代理服务 81端口：
          Souce CIDR: 0.0.0.0/0（所有IP全部可以进入）
          IP Protocal：TCP（进入协议是网页跑的TCP协议）
          Souce Port Range：留空（所有端口都可以进入）
          Destination Port Range：81（进入内部subnet 81端口）
          Description：npm
    
      开放Ping端口：
          Souce CIDR: 0.0.0.0/0（所有IP全部可以进入）
          IP Protocal：ICMP（Ping跑的协议）
          Souce Port Range：留空
          Destination Port Range：留空
          Description：Ping
    
    ### 2.查看Oracle定制版Ubuntu默认防火墙
      查看ip table:
          ·sudo iptables-save·
          默认是：
          1 established2 icmp
          3 lo
          4 ssh
          5 reject
    （可选）查看nft table
        ·sudo nft list ruleset·

    ### 3. 开放Ubuntu ip table端口
        优先级5开放80端口
        ·sudo iptables -I INPUT 5 -p tcp --dport 80 -j ACCEPT·
        优先级6开放443端口
        ·sudo iptables -I INPUT 6 -p tcp --dport 443 -j ACCEPT·
        检查是否写入ip table
        `sudo iptables -L -n --line-numbers`
        
---

## 安装docker
    https://docs.docker.com/engine/install/ubuntu/#installation-methods
    
    ### 1.安装基础包
    `sudo apt update`
    `sudo apt install -y ca-certificates curl`

    ### 2.创建 keyrings
    `sudo install -m 0755 -d /etc/apt/keyrings`

    ### 3.下载 Docker GPG key
    `sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc`

    ### 4.设置权限
    `sudo chmod a+r /etc/apt/keyrings/docker.asc`

    ### 5.添加 Docker repo
    看官网

    ### 6.更新 apt
    `sudo apt update`

    ### 7.安装 Docker
    `sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin`

    ### 8.测试Docker
    `sudo docker run hello-world`


    ### 9.让普通用户可以直接运行 Docker（可选但推荐）
    把当前 ubuntu 用户加入 docker 用户组：
    `sudo usermod -aG docker $USER`

    退出 SSH 后重新登录：
    `exit`

    重新登录后测试：
    `docker ps`

    如果没有 permission denied，说明配置成功。

    ### 10.测试 Nginx 容器
    先用 Nginx 官方镜像测试公网链路：
    `docker run -d -p 80:80 --name nginx-test nginx`

    浏览器打开：
    `http://161.XX.XX.XX`

    如果看到 Welcome to nginx，说明 Docker、OCI Security List、Ubuntu iptables、公网访问全部正常。

    测试完成后删除测试容器：
    `docker stop nginx-test`
    `docker rm nginx-test`

---

## 克隆项目仓库并 Docker 化 Flask 项目

### 1.克隆仓库

进入服务器后执行：

`cd ~`
`git clone https://github.com/vyshm24/cits3403-project.git`
`cd cits3403-project`

确认项目结构：

`ls`

应该能看到：

`app`
`run.py`
`requirements.txt`
`package.json`

### 2.给 requirements.txt 添加 Gunicorn

生产环境不要直接使用 `python run.py` 或 Flask 自带开发服务器。添加 Gunicorn：

`nano requirements.txt`

在最后加：

`gunicorn==23.0.0`

保存退出。

### 3.创建 Dockerfile

在项目根目录创建 Dockerfile：

`nano Dockerfile`

写入：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "120", "run:app"]
```

说明：

- `run:app` 表示导入 `run.py` 里的 `app = create_app()`
- `if __name__ == "__main__"` 里的 `app.run(debug=True, port=5001)` 只在本地直接运行 `python run.py` 时执行
- Docker 生产环境实际由 Gunicorn 启动，监听容器内 `5000`

### 4.构建 Flask 镜像

`docker build -t flask-project .`

第一次构建会比较慢，因为要下载 Python 镜像并安装 Python 依赖。

### 5.启动 Flask 容器测试公网访问

先直接把宿主机 80 端口映射到容器 5000 端口：

```bash
docker run -d \
  -p 80:5000 \
  --name flask-web \
  flask-project
```

查看容器状态：

`docker ps`

查看日志：

`docker logs flask-web`

浏览器打开：

`http://161.XX.XX.XX`

如果可以看到项目页面，说明 Flask + Docker + OCI 公网访问成功。

### 6.初始化数据库

如果注册、登录、浏览页面报错，日志里出现：

`sqlite3.OperationalError: no such table: user`

或者：

`sqlite3.OperationalError: no such table: itinerary`

说明 SQLite 数据库表还没创建。进入容器执行数据库迁移：

`docker exec -it flask-web sh`

在容器里执行：

`python -m flask --app run db upgrade`

退出容器：

`exit`

重启容器：

`docker restart flask-web`

再次测试注册功能。

### 7.持久化 SQLite 数据库

默认情况下 SQLite 数据库在容器内部。如果删除容器，数据库可能丢失。本项目数据库文件位置为：

`/app/app/app.db`

先把容器里的数据库复制到宿主机：

```bash
cd ~/cits3403-project
mkdir -p persistent-db
docker cp flask-web:/app/app/app.db ./persistent-db/app.db
```

确认复制成功：

`ls -lh persistent-db`

重新创建容器，并把宿主机数据库挂载到容器内：

```bash
docker stop flask-web
docker rm flask-web

docker run -d \
  -p 80:5000 \
  --name flask-web \
  -v ~/cits3403-project/persistent-db/app.db:/app/app/app.db \
  flask-project
```

之后每次重建容器都要保留这一段挂载：

`-v ~/cits3403-project/persistent-db/app.db:/app/app/app.db`

---

## Cloudflare 设置子域名

### 1.添加 DNS 记录

进入 Cloudflare：

`cy-server.com → DNS → Records → Add record`

添加：

```text
Type: A
Name: travelblog
IPv4 address: 161.XX.XX.XX
Proxy status: DNS only（先用灰色云）
TTL: Auto
```

保存后等待 DNS 生效。

最终子域名为：

`travelblog.cy-server.com`

### 2.测试子域名 HTTP 访问

浏览器访问：

`http://travelblog.cy-server.com`

如果可以打开项目页面，说明 DNS 指向成功。

如果打不开，检查：

- Cloudflare A 记录是否指向 OCI 公网 IP
- OCI Security List 是否开放 80
- Ubuntu iptables 是否开放 80
- Docker 容器是否在运行
- Flask 容器是否映射了 `-p 80:5000`

---

## 在 OCI 上部署 Nginx Proxy Manager

### 1.为什么要装 NPM

Nginx Proxy Manager 用来：

- 管理反向代理
- 把域名转发到 Flask 容器
- 自动申请 Let's Encrypt HTTPS 证书
- 管理 SSL 续期

最终结构：

```text
Cloudflare DNS
  ↓
OCI Public IP
  ↓
Nginx Proxy Manager
  ↓
Flask + Gunicorn container
  ↓
SQLite persistent DB
```

### 2.停止当前直接占用 80 端口的 Flask 容器

因为 NPM 需要占用宿主机 80 和 443，所以先停掉当前 Flask 容器：

```bash
docker stop flask-web
docker rm flask-web
```

### 3.创建 Docker Compose 项目

创建部署目录：

```bash
mkdir -p ~/web-stack
cd ~/web-stack
nano docker-compose.yml
```

写入：

```yaml
services:
  npm:
    image: jc21/nginx-proxy-manager:latest
    container_name: npm
    restart: unless-stopped
    ports:
      - "80:80"
      - "81:81"
      - "443:443"
    volumes:
      - ./npm-data:/data
      - ./letsencrypt:/etc/letsencrypt

  flask:
    image: flask-project
    container_name: flask-web
    restart: unless-stopped
    env_file:
      - /home/ubuntu/cits3403-project/.env
    expose:
      - "5000"
    volumes:
      - ~/cits3403-project/persistent-db/app.db:/app/app/app.db
      - /home/ubuntu/cits3403-project/persistent-db:/app/persistent-db
      - /home/ubuntu/cits3403-project/app/static/uploads:/app/app/static/uploads
```

注意：

- NPM 对外开放 80、443、81
- Flask 不再直接暴露公网端口，只在 Docker 内部网络暴露 5000
- NPM 可以通过 Docker Compose 内部 DNS 访问 `flask:5000`

### 4.启动 NPM 和 Flask

```bash
cd ~/web-stack
docker compose up -d
```

查看容器：

`docker ps`

应该能看到：

- `npm`
- `flask-web`

### 5.打开 NPM 管理后台

浏览器打开：

`http://161.XX.XX.XX:81`

首次登录 NPM 后，按页面提示修改默认账号密码。

如果打不开，检查：

- OCI Security List 是否开放 TCP 81
- Ubuntu iptables 是否开放 TCP 81
- NPM 容器是否正常运行

Ubuntu iptables 可临时开放 81：

`sudo iptables -I INPUT 7 -p tcp --dport 81 -j ACCEPT`

---

## 在 NPM 中绑定域名和申请 HTTPS

### 1.添加 Proxy Host

进入 NPM 后：

`Hosts → Proxy Hosts → Add Proxy Host`

Details 页面填写：

```text
Domain Names:
travelblog.cy-server.com

Scheme:
http

Forward Hostname / IP:
flask

Forward Port:
5000

Access List:
Public
```

建议勾选：

```text
Block Common Exploits
Websockets Support
```

保存后先访问：

`http://travelblog.cy-server.com`

如果 HTTP 能打开，说明 NPM 反向代理成功。

### 2.申请 Let's Encrypt SSL 证书

编辑刚刚创建的 Proxy Host：

`Proxy Hosts → travelblog.cy-server.com → Edit → SSL`

选择：

```text
SSL Certificate:
Request a new Certificate
```

勾选：

```text
Force SSL
HTTP/2 Support（如果可选）
I Agree to Let's Encrypt Terms of Service
```

不要勾选：

```text
Use DNS Challenge
```

因为本案例中公网 HTTP 已经可达，HTTP challenge 足够使用。

点击 Save。

成功后访问：

`https://travelblog.cy-server.com`

如果 Chrome 显示 Not Secure，可以先换无痕模式或换设备测试。有时是浏览器缓存问题。

### 3.Cloudflare SSL 设置

确认 HTTPS 正常后，进入 Cloudflare：

`SSL/TLS → Overview`

设置为：

`Full (strict)`

然后可以把 DNS 记录从灰色云改为橙色云：

`DNS → travelblog → Proxied`

如果改橙色云后异常，先改回 DNS only 排查。

---

## 常用维护命令

### 查看容器状态

`docker ps`

### 查看 Flask 日志

`docker logs --tail=100 flask-web`

实时查看：

`docker logs -f flask-web`

### 查看 NPM 日志

`docker logs --tail=100 npm`

### 重启所有服务

```bash
cd ~/web-stack
docker compose restart
```

### 用docker compose 运维
修改容器配置文件
```bash
nano ~/web-stack/docker-compose.yml
```
重启所有服务
```bash
docker compose -f ~/web-stack/docker-compose.yml up -d --force-recreate flask
```

### 更新项目代码并重新部署

```bash
cd ~/cits3403-project
git pull

docker build -t flask-project .

cd ~/web-stack
docker compose down
docker compose up -d
```

如果数据库迁移有变化，执行：

```bash
docker exec -it flask-web sh
python -m flask --app run db upgrade
exit
```

### 备份 SQLite 数据库

```bash
cd ~/cits3403-project
cp persistent-db/app.db persistent-db/app.db.backup.$(date +%Y%m%d-%H%M%S)
```

### 恢复 SQLite 数据库

先停服务：

```bash
cd ~/web-stack
docker compose down
```

复制备份覆盖当前数据库：

```bash
cp ~/cits3403-project/persistent-db/app.db.backup.YYYYMMDD-HHMMSS ~/cits3403-project/persistent-db/app.db
```

重新启动：

```bash
cd ~/web-stack
docker compose up -d
```

---

## 最终架构

```text
User Browser
  ↓
https://travelblog.cy-server.com
  ↓
Cloudflare DNS
  ↓
OCI Public IPv4
  ↓
Nginx Proxy Manager container
  ↓
Flask container + Gunicorn
  ↓
SQLite database mounted from host
```

---
      