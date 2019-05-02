curl -O https://repo.anaconda.com/archive/Anaconda3-2019.03-Linux-x86_64.sh
sha256sum Anaconda3-2019.03-Linux-x86_64.sh
bash Anaconda3-2019.03-Linux-x86_64.sh
apt-get update
apt-get install libmysqlclient-dev
apt-get install python3.7-dev
apt-get install gcc
apt-get install awscli
apt-get install supervisor
pip install mysqlclient
pip install spacy-nightly
pip install django_mysql
pip install spacy-nightly
pip install Django==2.2b1
pip install celery
pip install django_mysql
pip install git+https://github.com/mihaivinaga/geograpy.git
pip install scrapy
pip install scrapy_djangoitem
pip install phonenumbers
pip install probablepeople
pip install html2text
pip install email_split
pip install iso3166
pip install validate_email
pip install django-bitfield
pip install dicttoxml
python -m spacy download en_core_web_lg
pip install scrapy-splash
pip install boto3
pip install cookiecutter
pip install isoweek

mkdir /var/www/soleadify_ml_v2/soleadify_ml/logs
aws configure