# copytrading-back
celery -A copyTradingApi beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
celery -A copyTradingApi worker -l INFO
location /media/ {
        alias /www/source/copytrading-back/media/$1;
}