## DEV SETUP 

postgresql -> `docker-compose pull`

redis -> `docker-compose pull`

netbox -> ```sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential libxml2-dev libxslt1-dev libffi-dev libpq-dev libssl-dev zlib1g-dev
python3 manage.py migrate
python3 manage.py createsuperuser```
