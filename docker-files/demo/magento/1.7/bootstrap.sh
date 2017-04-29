#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin
export WORKDIR=$( cd ` dirname $0 ` && pwd )
cd "$WORKDIR" || exit 1

MYSQL_PORT=${MYSQL_PORT:-3306}

MYSQL_USER=magento
MYSQL_PASSWORD=magento
MYSQL_DATABASE=magento

MAGENTO_LOCALE=en_GB
MAGENTO_DEFAULT_CURRENCY=NZD
MAGENTO_URL=$SERVICE_ADDR
MAGENTO_ADMIN_FIRSTNAME=Admin
MAGENTO_ADMIN_LASTNAME=MyStore
MAGENTO_ADMIN_EMAIL=admin@example.com
MAGENTO_ADMIN_USERNAME=admin
MAGENTO_ADMIN_PASSWORD=Letmein123


env_chk()
{
	if [[ "$MYSQL_HOST"x == "x" || "$MYSQL_ROOT_PWD"x == "x" || "$SERVICE_ADDR"x == "x" ]]; then
		echo "env is lack, exit error."
		exit 1
	fi
	cd /var/www && rm -r html && ln -s /var/www/htdocs html
}

mysql_prepare()
{
	mysql -h$MYSQL_HOST -P$MYSQL_PORT -uroot -p$MYSQL_ROOT_PWD -e "create database if not exists magento;"
	mysql -h$MYSQL_HOST -P$MYSQL_PORT -uroot -p$MYSQL_ROOT_PWD -e "grant all privileges on magento.* to magento@'%' identified by 'magento';"
	sleep 3
}


install-magento()
{
	php -f /var/www/htdocs/install.php -- \
		--license_agreement_accepted "yes" \
		--locale $MAGENTO_LOCALE \
		--timezone $MAGENTO_TIMEZONE \
		--default_currency $MAGENTO_DEFAULT_CURRENCY \
		--db_host $MYSQL_HOST:$MYSQL_PORT  \
		--db_name $MYSQL_DATABASE \
		--db_user $MYSQL_USER \
		--db_pass $MYSQL_PASSWORD \
		--url $MAGENTO_URL \
		--skip_url_validation "yes" \
		--use_rewrites "no" \
		--use_secure "no" \
		--secure_base_url "" \
		--use_secure_admin "no" \
		--admin_firstname $MAGENTO_ADMIN_FIRSTNAME \
		--admin_lastname $MAGENTO_ADMIN_LASTNAME \
		--admin_email $MAGENTO_ADMIN_EMAIL \
		--admin_username $MAGENTO_ADMIN_USERNAME \
		--admin_password $MAGENTO_ADMIN_PASSWORD
}

env_chk
mysql_prepare
install-magento
apache2-foreground
