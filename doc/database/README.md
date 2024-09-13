# 数据库

## 安装

参考[官网说明](https://www.postgresql.org/download/linux/ubuntu/)，执行下面的命令就可以完成安装：

```bash
sudo apt-get update
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh

sudo apt update
sudo apt install postgresql-16
```

## 查看版本

```bash
psql --version
```

## 服务情况

安装 PostgreSQL 后，需要知道以下 3 个命令：

- `sudo service postgresql status`: 用于检查数据库的状态。
- `sudo service postgresql start`: 用于开始运行数据库。
- `sudo service postgresql stop`: 用于停止运行数据库。

## 初始化密码

默认管理员用户 postgres 需要分配的密码才能连接到数据库。要设置密码，请执行以下操作：

1. 启动 postgres 服务：`sudo service postgresql start`
2. 输入命令：`sudo passwd postgres`
3. 系统将提示你输入新密码。
4. 关闭并重新打开终端。
5. 连接到 postgres 服务，并打开 psql shell：`sudo -u postgres psql`，或者临时切换用户的方法进入： `su - postgres && psql`
6. 成功输入 psql shell 后，将显示更改为如下所示的命令行：`postgres=#`

## 设置数据库用户名密码

上一步设置的是命令行登录的密码，下面修改使用网络连接用的用户名和密码：

```bash
sudo -u postgres psql
# 会出现 postgres=# 然后输入，xxx 就是密码，后续连接用这个密码，最后的 ; 不要漏了！
alter role postgres with password 'xxx';
```

## 访问

- 修改数据库访问权限配置文件 : `sudo vim /etc/postgresql/16/main/pg_hba.conf`

```diff
-local   all             postgres                                peer
+local   all             postgres                                trust
```

在 IPv4 下面加入

```bash
host    all             all             0.0.0.0/0               scram-sha-256
```

- 修改 数据库服务器参数配置 `sudo vim /etc/postgresql/16/main/postgresql.conf`

在 `# - Connection Settings -` 的 `#listen_addresses = 'localhost'` 前加入：

```bash
listen_addresses = '*'
```

重启服务

```bash
sudo service postgresql restart
```

## 新建数据库

需要先建立一个数据库，

1. 登录数据库：

```bash
sudo -u postgres psql
```

2. 创建数据库

```bash
CREATE DATABASE streamer_sales_db;
```

3. 查看目前所有的数据库

```bash
\l
```

后续数据表会在代码里面自行创建

## 数据库可视化

[pgadmin](https://www.pgadmin.org/)
