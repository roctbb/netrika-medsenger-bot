sudo pip3 install -r requirements.txt
sudo cp agents_netrika.conf /etc/supervisor/conf.d/
sudo cp agents_netrika_nginx.conf /etc/nginx/sites-enabled/
sudo supervisorctl update
sudo systemctl restart nginx
sudo certbot --nginx -d netrika.medsenger.ru
touch config.py