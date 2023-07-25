FROM python:slim

LABEL Sai Karthik <kskarthik@disroot.org>

ARG VERSION="dev"
ENV GKCORE_VERSION=${VERSION}
# install the required dependencies
RUN apt-get update && apt-get upgrade -y \
		&& apt-get install -y \
		build-essential libpq-dev curl
# copy the contents of the repo to the image
COPY . /gkcore/
#switch to workdir gkcore
WORKDIR /gkcore
# create a non-root user to run gkcore
RUN adduser --no-create-home --disabled-password gk && \
		# install gkcore dependencies & run setup
		pip install -r requirements.txt && python3 setup.py develop &&\
		# clean the build environment
		apt purge build-essential libpq-dev wget -y &&\
		apt-get autoremove -y &&\
		apt-get clean && \
		rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
# switch to non-root user named gk, which we created above
USER gk
# initialize db & start gkcore
ENTRYPOINT python3 initdb.py && python3 db_migrate.py && pserve production.ini
# expose the gkcore port
EXPOSE 6543
# check the health of the container at regular intervals
HEALTHCHECK --start-period=60s \
  CMD curl -f http://localhost:6543 || exit 1
