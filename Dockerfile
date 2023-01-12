FROM python:slim
LABEL Sai Karthik <kskarthik@disroot.org>
# install the required dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y build-essential libpq-dev
# copy the contents of the repo to the image
COPY . /gkcore/
#switch to workdir gkcore
WORKDIR /gkcore
# install gkcore dependencies & run setup
RUN pip install -r requirements.txt && python3 setup.py develop
# clean the build environment
RUN apt purge build-essential wget -y &&\
	apt-get autoremove -y &&\
	apt-get clean &&\
	rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
# create a non-root user to run gkcore
RUN adduser --no-create-home --disabled-password gk
# switch to non-root user named gk, which we created above
USER gk
# initialize db & start gkcore
CMD python3 /gkcore/initdb.py && pserve /gkcore/production.ini
# expose the gkcore port
EXPOSE 6543
