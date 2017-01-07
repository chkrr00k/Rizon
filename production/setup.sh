#!/bin/bash

if [[ $(id -u) -ne 0]]; then
	echo "Please insert SUDO password when needed."
	echo "Installing python libs"
	sudo apt-get install python-mysqldb
	sudo apt-get install python-dev
	sudo apt-get install libmysqlclient-dev
	echo "Installing MySQL"
	sudo apt-get install mysql-server mysql-client
	
else
	echo "Installing python libs"
	apt-get install python-mysqldb
	apt-get install python-dev
	apt-get install libmysqlclient-dev
	echo "Installing MySQL"
	apt-get install mysql-server mysql-client
fi



