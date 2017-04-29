Must run command in current path like this:
python bin/alert_manager.py
python -m alert.test_comm.test_log 


[Install]
1. clone source code
echo "172.30.10.87    git.dy" >> /etc/hosts
git clone git@git.dy:paas/alert-center.git

2. environment setup
# apt-get install python-pip
# pip install eventlet
# pip install sqlalchemy

3. db prepare
mysql -u ac -p alert_center < alert_center.sql
mysql -u ac -p cmdb_alert < cmdb_alert.sql
# or you can create table by alert.model.tables.py

4. config
change configuration in alert-center/conf/alert.conf

5. run
cd /dianyi/app/alert_center/alert-center/bin
./alert_manager.py