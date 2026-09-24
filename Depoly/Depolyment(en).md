# How to Create a Cloud Server Instance and Deploy a Website

---

Architecture:
Internet → Public IP → OCI VCN → Public Subnet → Ubuntu Instance → Docker → Flask + Nginx + SQLite

---

# Create the Server Build Instance on OCI

## 1. Basic Information

* **Name:** Fill in the server name yourself (Example: `cy-server-Ora(x86)`)

* **Create in compartment:** Default root account

* **Placement / Availability domain:** Depends on the region selected when creating the OCI account. After selecting the region, choose the availability domain.

* **Placement / Advanced options:** Select the host deployment scheme for the server.

  * Example: Default `On-demand capacity` (shared host machine)

* **Image:** Choose the operating system as needed.

  * Example: `Canonical Ubuntu 24.04 Minimal`

* **Shape:** Select hardware specifications according to budget.

  * Example: `VM.Standard.E2.1.Micro (Always Free-eligible)`

### Image and Shape → Advanced Options

* **Instance metadata service:** OCI’s internal metadata interface for the instance.
* **Require an authorization header:** Require IMDSv2 authentication headers when accessing metadata. Enabling it improves security; disabling improves compatibility.

  * Example: Enabled
* **Initialization script:** Startup initialization script, e.g., automatically running `apt update`.

  * Example: Skipped

---

## 2. Security

* **Shielded instance:** Enables enhanced boot security using Secure Boot, Measured Boot, and TPM. Disabling improves compatibility.

  * Example: Disabled

* **Advanced options / Security attributes:** Apply security tags to resources and control resource communication using ZPR policies.

  * Example: Not configured

---

## 3. Networking

* **Primary VNIC / VNIC name:** Name for the virtual network card.

  * Example: `VNIC-Flask`

* **Primary network:** Reuse an existing VCN or create a new one.

  * Example: Reuse `vcn-2026XXXX-XXXX`

* **Subnet:** Reuse an existing LAN or create a new one.

  * Note: Inbound/outbound rules affect all instances inside the subnet.
  * Example: `Create new public subnet`

### New Subnet

* **New subnet name:**

  * Example: `subnet-Flask`

* **Create in compartment:** Default root account

* **CIDR block:** Virtual LAN address range. Must not overlap with other subnets in the same VCN.

  * Example: `10.0.1.0/24`

* **IPv4 address assignment:** Skip for now. Configure after the subnet is created.

* **Add SSH keys:** Choose an SSH key option.

  * Example: `Generate a key pair for me`, then download the private key (optional: public key)

---

## 4. Boot Volume

* **Boot volume:** System disk size and throughput.

  * Example: Default `46.6GB`

* **Use in-transit encryption:** Encrypt traffic between the instance and storage.

  * Example: Disabled

* **Encrypt this volume with a key that you manage:** Self-managed disk encryption keys.

  * Example: Disabled

* **Block volumes:** Additional mounted disks.

  * Example: None

---

## 5. Review

Review the configuration and create the server instance.

---

# Configure Networking and SSH

## 1. Check Public IPv4 Address

Open the `cy-server-Ora(x86)` instance and go to **Networking** to verify that a Public IPv4 Address exists.

## 2. Configure Public IPv4

Open the VNIC → **IP administration**.

* If there is no IPv4 address, add one.
* If there is one, check whether it is `Reserved` or `Ephemeral` and note the address.

  * Example: `161.XX.XX.XX`

## 3. Move SSH Key

Place the downloaded SSH private key into:

```bash
~/.ssh
```

## 4. (Optional) Configure SSH Shortcut

```text
Host server-agile
  HostName 161.XX.XX.XX
  User ubuntu
  IdentityFile ~/.ssh/ssh-key-2026-05-16.key
```

## 5. Set SSH Key Permissions

```bash
chmod 600 ~/.ssh/ssh-key-2026-05-16.key
```

## 6. Connect via SSH

```bash
ssh server-agile
```

---

# Test the Console Connection

## 1. Set Password After SSH Login

```bash
sudo passwd ubuntu
```

## 2. Open OS Management → Console Connection

* Username: `ubuntu`
* Password: the password you just configured

---

# Open Required Ports

## 1. Configure Inbound Rules for subnet-Flask

### Open Port 80

* Source CIDR: `0.0.0.0/0`
* IP Protocol: `TCP`
* Source Port Range: Leave blank
* Destination Port Range: `80`
* Description: `HTTP connect`

### Open Port 81

* Source CIDR: `0.0.0.0/0`
* IP Protocol: `TCP`
* Source Port Range: Leave blank
* Destination Port Range: `81`
* Description: `npm`

### Open Port 443

* Source CIDR: `0.0.0.0/0`
* IP Protocol: `TCP`
* Source Port Range: Leave blank
* Destination Port Range: `443`
* Description: `HTTPS connect`

### Open Ping

* Source CIDR: `0.0.0.0/0`
* IP Protocol: `ICMP`
* Source Port Range: Leave blank
* Destination Port Range: Leave blank
* Description: `Ping`

---

## 2. Check Oracle Ubuntu Firewall Rules

View iptables:

```bash
sudo iptables-save
```

Default rules usually include:

1. established
2. icmp
3. lo
4. ssh
5. reject

(Optional) View nftables:

```bash
sudo nft list ruleset
```

---

## 3. Open Ubuntu iptables Ports

Allow port 80 with priority 5:

```bash
sudo iptables -I INPUT 5 -p tcp --dport 80 -j ACCEPT
```

Allow port 443 with priority 6:

```bash
sudo iptables -I INPUT 6 -p tcp --dport 443 -j ACCEPT
```

Check iptables rules:

```bash
sudo iptables -L -n --line-numbers
```

---

# Install Docker

Official Docker guide:

[https://docs.docker.com/engine/install/ubuntu/#installation-methods](https://docs.docker.com/engine/install/ubuntu/#installation-methods)

## 1. Install Basic Packages

```bash
sudo apt update
sudo apt install -y ca-certificates curl
```

## 2. Create keyrings Directory

```bash
sudo install -m 0755 -d /etc/apt/keyrings
```

## 3. Download Docker GPG Key

```bash
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
```

## 4. Set Permissions

```bash
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

## 5. Add Docker Repository

See Docker official documentation.

## 6. Update apt

```bash
sudo apt update
```

## 7. Install Docker

```bash
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 8. Test Docker

```bash
sudo docker run hello-world
```

## 9. Allow Normal User to Run Docker (Optional but Recommended)

Add the current ubuntu user to the docker group:

```bash
sudo usermod -aG docker $USER
```

Exit SSH:

```bash
exit
```

Reconnect and test:

```bash
docker ps
```

If there is no `permission denied`, the configuration is successful.

---

## 10. Test an Nginx Container

Run the official Nginx image:

```bash
docker run -d -p 80:80 --name nginx-test nginx
```

Open in browser:

```text
http://161.XX.XX.XX
```

If you see `Welcome to nginx`, then Docker, OCI Security Lists, Ubuntu iptables, and public access are all functioning correctly.

Remove the test container afterward:

```bash
docker stop nginx-test
docker rm nginx-test
```

---

# Clone the Project Repository and Dockerize the Flask Project

## 1. Clone the Repository

```bash
cd ~
git clone https://github.com/vyshm24/cits3403-project.git
cd cits3403-project
```

Check the project structure:

```bash
ls
```

You should see:

```text
app
run.py
requirements.txt
package.json
```

---

## 2. Add Gunicorn to requirements.txt

Do not use Flask’s built-in development server in production.

Edit:

```bash
nano requirements.txt
```

Add:

```text
gunicorn==23.0.0
```

---

## 3. Create Dockerfile

Create a Dockerfile in the project root:

```bash
nano Dockerfile
```

Add:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "120", "run:app"]
```

Explanation:

* `run:app` imports the `app` object from `run.py`
* `app.run(debug=True, port=5001)` only executes when running `python run.py` locally
* In production Docker deployment, Gunicorn listens on port `5000`

---

## 4. Build Flask Image

```bash
docker build -t flask-project .
```

The first build may take some time.

---

## 5. Start Flask Container and Test Public Access

```bash
docker run -d \
  -p 80:5000 \
  --name flask-web \
  flask-project
```

Check container status:

```bash
docker ps
```

View logs:

```bash
docker logs flask-web
```

Open:

```text
http://161.XX.XX.XX
```

If the website loads, Flask + Docker + OCI public access is working.

---

## 6. Initialize Database

If you see errors like:

```text
sqlite3.OperationalError: no such table: user
```

or:

```text
sqlite3.OperationalError: no such table: itinerary
```

enter the container:

```bash
docker exec -it flask-web sh
```

Run database migration:

```bash
python -m flask --app run db upgrade
```

Exit:

```bash
exit
```

Restart container:

```bash
docker restart flask-web
```

---

## 7. Persist SQLite Database

The SQLite database is stored inside the container by default. If the container is deleted, the database may be lost.

Database location:

```text
/app/app/app.db
```

Copy database to host machine:

```bash
cd ~/cits3403-project
mkdir -p persistent-db
docker cp flask-web:/app/app/app.db ./persistent-db/app.db
```

Verify:

```bash
ls -lh persistent-db
```

Recreate container with mounted database:

```bash
docker stop flask-web
docker rm flask-web

docker run -d \
  -p 80:5000 \
  --name flask-web \
  -v ~/cits3403-project/persistent-db/app.db:/app/app/app.db \
  flask-project
```

Always keep this mount:

```text
-v ~/cits3403-project/persistent-db/app.db:/app/app/app.db
```

---

# Configure Cloudflare Subdomain

## 1. Add DNS Record

In Cloudflare:

```text
cy-server.com → DNS → Records → Add record
```

Add:

```text
Type: A
Name: travelblog
IPv4 address: 161.XX.XX.XX
Proxy status: DNS only
TTL: Auto
```

Final subdomain:

```text
travelblog.cy-server.com
```

---

## 2. Test HTTP Access

Open:

```text
http://travelblog.cy-server.com
```

If it fails, check:

* Cloudflare A record
* OCI Security List port 80
* Ubuntu iptables port 80
* Docker container status
* Flask port mapping

---

# Deploy Nginx Proxy Manager on OCI

## 1. Why Install NPM

Nginx Proxy Manager is used to:

* Manage reverse proxies
* Forward domains to Flask containers
* Automatically request Let’s Encrypt HTTPS certificates
* Manage SSL renewal

Final architecture:

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

---

## 2. Stop Current Flask Container

```bash
docker stop flask-web
docker rm flask-web
```

---

## 3. Create Docker Compose Project

```bash
mkdir -p ~/web-stack
cd ~/web-stack
nano docker-compose.yml
```

Add:

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

Notes:

* NPM exposes ports 80, 443, and 81 publicly
* Flask no longer exposes public ports directly
* NPM accesses `flask:5000` through Docker Compose networking

---

## 4. Start NPM and Flask

```bash
cd ~/web-stack
docker compose up -d
```

Check containers:

```bash
docker ps
```

Expected:

* `npm`
* `flask-web`

---

## 5. Open NPM Admin Panel

Open:

```text
http://161.XX.XX.XX:81
```

If inaccessible, check:

* OCI Security List port 81
* Ubuntu iptables port 81
* NPM container status

Temporary iptables rule:

```bash
sudo iptables -I INPUT 7 -p tcp --dport 81 -j ACCEPT
```

---

# Configure Domain and HTTPS in NPM

## 1. Add Proxy Host

In NPM:

```text
Hosts → Proxy Hosts → Add Proxy Host
```

Fill:

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

Recommended:

```text
Block Common Exploits
Websockets Support
```

Test:

```text
http://travelblog.cy-server.com
```

---

## 2. Request Let’s Encrypt SSL Certificate

Edit Proxy Host:

```text
Proxy Hosts → travelblog.cy-server.com → Edit → SSL
```

Choose:

```text
SSL Certificate:
Request a new Certificate
```

Enable:

```text
Force SSL
HTTP/2 Support
I Agree to Let's Encrypt Terms of Service
```

Do NOT enable:

```text
Use DNS Challenge
```

Save.

Test:

```text
https://travelblog.cy-server.com
```

If Chrome shows `Not Secure`, test in incognito mode.

---

## 3. Cloudflare SSL Settings

In Cloudflare:

```text
SSL/TLS → Overview
```

Set:

```text
Full (strict)
```

Then optionally switch DNS from gray cloud to orange cloud:

```text
DNS → travelblog → Proxied
```

---

# Common Maintenance Commands

## Check Containers

```bash
docker ps
```

## View Flask Logs

```bash
docker logs --tail=100 flask-web
```

Realtime:

```bash
docker logs -f flask-web
```

## View NPM Logs

```bash
docker logs --tail=100 npm
```

## Restart Services

```bash
cd ~/web-stack
docker compose restart
```

## Manage with Docker Compose

Edit compose file:

```bash
nano ~/web-stack/docker-compose.yml
```

Recreate Flask service:

```bash
docker compose -f ~/web-stack/docker-compose.yml up -d --force-recreate flask
```

---

## Update Project and Redeploy

```bash
cd ~/cits3403-project
git pull

docker build -t flask-project .

cd ~/web-stack
docker compose down
docker compose up -d
```

If database migrations changed:

```bash
docker exec -it flask-web sh
python -m flask --app run db upgrade
exit
```

---

## Backup SQLite Database

```bash
cd ~/cits3403-project
cp persistent-db/app.db persistent-db/app.db.backup.$(date +%Y%m%d-%H%M%S)
```

---

## Restore SQLite Database

Stop services:

```bash
cd ~/web-stack
docker compose down
```

Restore backup:

```bash
cp ~/cits3403-project/persistent-db/app.db.backup.YYYYMMDD-HHMMSS ~/cits3403-project/persistent-db/app.db
```

Restart:

```bash
cd ~/web-stack
docker compose up -d
```

---

# Final Architecture

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
