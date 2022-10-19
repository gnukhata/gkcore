FROM python:slim

LABEL Sai Karthik <kskarthik@disroot.org>

# GNUKhata Branch
# ARG branch=devel

# Postgres instance url for gkcore
#ENV GKCORE_DB_URL=postgres://gkadmin:gkadmin@db:5432/gkdata

# installing required dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y build-essential libpq-dev

#first copy important scripts into /gkcore
#then give read and execute permisions

# RUN mkdir /gkcore

# copy the contents of the repo to the image
COPY . /gkcore/

WORKDIR /gkcore
# install gkcore dependencies & run setup
RUN pip install -r requirements.txt && python3 setup.py develop

# clean build environment
RUN apt purge build-essential wget -y &&\
	apt-get autoremove -y &&\
	apt-get clean &&\
	rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* 

# expose gkcore port
EXPOSE 6543

ENTRYPOINT python3 /gkcore/initdb.py && pserve /gkcore/production.ini && tail -f /dev/null
