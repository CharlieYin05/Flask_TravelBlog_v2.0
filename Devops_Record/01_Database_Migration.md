# 数据库迁移

**日期**
2026-07-15

---

## 目标：
  - 用MySQL代替SQLite
  - 尽量保留原有的用户数据

---

## 过程

### 1. 本地准备

#### 1.1 requirements.txt里添加PyMySQL

#### 1.2 改Flask配置文件
进入 app/config.py，把写死的连接SQLite:
```
SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'app.db'}"
```
改成本地开发环境没有`DATABASE_URL` → 自动用 SQLite，服务器在`.env`设置了`DATABASEL_URL` → 自动用MySQL：
```
  SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'app.db'}"
  )
```
#### 1.3 检查models.py是否兼容MySQL(有没有SQLite特有的写法)

### 2. 部署MySQL

#### 2.1 在`docker-compose.yml`得Service里一个MySQL服务
```
  mysql:
    image: mysql:9.7
    container_name: mysql-db
    restart: unless-stopped

    environment:
    MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    MYSQL_DATABASE: travelblog
    MYSQL_USER: travelblog
    MYSQL_PASSWORD: ${MYSQL_PASSWORD}

    volumes:
      - mysql-data:/var/lib/mysql
    
  volumes:
    mysql-data:
```

#### 2.2 在webstack的'.env'添加密码和管理员密码并启动MySQL（注意不是cit3404-project里的.env，那是Flask的环境）
```
MYSQL_ROOT_PASSWORD=XXXXX
MYSQL_PASSWORD=XXXXX
```

#### 2.3 启动MySQL并首次运行确认初始化
MySQl,启动！
```
cd ~/web-stack
docker compose up -d mysql
```
确认容器运行：
```
docker ps
```
看日志：
```
docker logs mysql-db
```
理论上第一次启动看到Initializing database，最后出现ready for connections
  
#### 问题1 首次初始化MySQL时把我的VPS小水管1G内存给榨干了，反复触发OOM Killer，整台机器卡到连Console都没法连接
拯救服务器：
  1. Reboot重启主机
  2. 开机后立刻输入 `sudo systemctl stop docker` 来终止Docker运行
  3. 之后输入 `sudo systemctl disable docker` 来禁止开机Docker自启动
  4. 创建2GB的Swap内存，并开机自启动Swap内存
     ```
     sudo fallocate -l 2G /swapfile
            
     sudo chmod 600 /swapfile

     sudo mkswap /swapfile

     sudo swapon /swapfile

     free -h

     echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
     ```
  5. 限制MySQL内存占用
     先写一个只读文件挂在到MySQL容器:
     ```
     cd ~/web-stack
     mkdir -p mysql
     nano mysql/my.cnf

     [mysqld]
     innodb_buffer_pool_size=128M
     innodb_log_buffer_size=16M
     innodb_redo_log_capacity=64M
     max_connections=20
     table_open_cache=128
     performance_schema=OFF
     skip_name_resolve=ON
     ```
     然后修改Docker配配置限制内存大小：
     ```
     mysql:
       image: mysql:9.7
       container_name: mysql-db
       restart: unless-stopped

       environment:
       MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
       MYSQL_DATABASE: travelblog
       MYSQL_USER: travelblog
       MYSQL_PASSWORD: ${MYSQL_PASSWORD}

     volumes:
       - mysql-data:/var/lib/mysql
       - ./mysql/my.cnf:/etc/mysql/conf.d/low-memory.cnf:ro

       mem_limit: 512m
       mem_reservation: 256m
     ```
  6. 下次开连服务器开多几个Terminal监控硬件与Docker状态


#### 问题2 启动无法登进我的MySQL服务器
问题：输入 `docker exec -it mysql-db mysql -u travelblog -p` 和 `docker exec -it mysql-db mysql -u root -p`都无法登录，显示：  
```
ERROR 1045 (28000): Access denied for user 'root'@'localhost' (using password: YES)
```
    
怀疑：初次启动的时候还没有完成就被linux OOM Killer把进程杀了
解决：准备妥当后重新启动MySQL，初始化时关闭Flask和NPM省内存和CPU占用。初始化后加载.env的文件（MySQL密码）。最后启动NPM和Flask
```
docker compose up -d mysql

source ~/web-stack/.env
```

#### 问题3 开启NPM时失败，显示端口80被占用Docker无法开启NPM
排查：哪个狗进程占我80端口：
```
sudo ss -tlnp | grep :80
LISTEN 0      511          0.0.0.0:80        0.0.0.0:*    users:(("nginx",pid=748,fd=5),("nginx",pid=746,fd=5),("nginx",pid=745,fd=5))
LISTEN 0      511             [::]:80           [::]:*    users:(("nginx",pid=748,fd=6),("nginx",pid=746,fd=6),("nginx",pid=745,fd=6))
```
    
解决：关闭系统自带的Nginx进程，重新启动NPM
```
sudo systemctl stop nginx

sudo systemctl disable nginx   # 防止下次开机自动启动

docker rm npm

docker compose up -d npm
```

### 3. 数据库迁移

#### 3.1 导出SQLite数据库为SQL文件并备份
先安装SQLite3:
```
sudo apt install sqlite3
```
导出导出 SQLite 数据库为 SQL 文件：
```
sqlite3 ~/cits3403-project/persistent-db/app.db .dump > /tmp/app.sql
```
备份原始文件:
```
cp /tmp/app.sql /tmp/app.sql.orig
```

#### 3.2 把原来的数据库导入到MySQL
先检查语法是否兼容：
```
sed -i 's/AUTOINCREMENT/AUTO_INCREMENT/g' /tmp/app.sql

sed -i 's/"\([^"]*\)"/`\1`/g' /tmp/app.sql

sed -i '/PRAGMA/d' /tmp/app.sql
```
    
再拷贝到MySQL容器：
```
 docker cp /tmp/app.sql mysql-db:/app.sql
```
    
导入到MySQL数据库:
```
source ~/web-stack/.env

docker exec -i mysql-db mysql -uroot -p${MYSQL_ROOT_PASSWORD} travelblog < /tmp/app.sql
```

### 啊啊啊啊！好多兼容性问题，未来直接重构原生MySQL数据库吧。。。今天数据库迁移计划算是失败了。暂时用SQLite顶着。主要是迁移的过程全靠AI来修复兼容性问题我都不知道数据库结构有没有被破坏，里面的数据还在不在。




    



