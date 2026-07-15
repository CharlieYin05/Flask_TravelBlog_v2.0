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
### 1.3 检查models.py是否兼容MySQL(有没有SQLite特有的写法)

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
    ---
    确认容器运行
    ```
    docker ps
    ```
    ---
    看日志
    ```
    docker logs mysql-db
    ```
    理论上第一次启动看到Initializing database，最后出现ready for connections
    ---
    我cao了呀，怎么和服务器断开SSH了，难道启动MySQL把硬件吃满了？

    



